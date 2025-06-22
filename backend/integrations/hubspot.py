# hubspot.py
import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64
import requests
from datetime import datetime
from integrations.integration_item import IntegrationItem

from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

CLIENT_ID = 'your_client_id_here'
CLIENT_SECRET = 'your_client_secret_here' 
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
authorization_url = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=crm.objects.contacts.read%20oauth'

async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')
    
    auth_url = f'{authorization_url}&state={encoded_state}'
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)

    return auth_url

async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error_description'))
    
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode('utf-8'))

    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')

    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    async with httpx.AsyncClient() as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'code': code,
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )

    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)
    
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)

async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')

    return credentials

def create_integration_item_metadata_object(response_json, item_type, parent_id=None, parent_name=None) -> IntegrationItem:
    def parse_time(ts):
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(int(ts) / 1000)
        except Exception:
            return None

    integration_item_metadata = IntegrationItem(
        id=response_json.get('id', None),
        name=response_json.get('properties', {}).get('firstname', '') + ' ' + response_json.get('properties', {}).get('lastname', ''),
        type=item_type,
        parent_id=parent_id,
        parent_path_or_name=parent_name,
        creation_time=parse_time(response_json.get('createdAt')),
        last_modified_time=parse_time(response_json.get('updatedAt')),
        url=f"https://app.hubspot.com/contacts/{response_json.get('id')}" if response_json.get('id') else None,
    )

    return integration_item_metadata

async def get_items_hubspot(credentials) -> list[IntegrationItem]:
    """Fetches HubSpot contacts and returns them as IntegrationItem objects"""
    credentials = json.loads(credentials)
    access_token = credentials.get('access_token')
    
    if not access_token:
        raise HTTPException(status_code=400, detail='No access token found in credentials.')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    list_of_integration_item_metadata = []
    
    # Fetch contacts from HubSpot
    url = 'https://api.hubapi.com/crm/v3/objects/contacts'
    params = {'limit': 100}  # HubSpot default limit
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            for contact in results:
                list_of_integration_item_metadata.append(
                    create_integration_item_metadata_object(contact, 'Contact')
                )
            
            # Handle pagination if there are more results
            while data.get('paging', {}).get('next', {}).get('after'):
                params['after'] = data['paging']['next']['after']
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    for contact in results:
                        list_of_integration_item_metadata.append(
                            create_integration_item_metadata_object(contact, 'Contact')
                        )
                else:
                    break
        else:
            print(f"Error fetching HubSpot contacts: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception while fetching HubSpot contacts: {str(e)}")
    
    print(json.dumps([item.__dict__ for item in list_of_integration_item_metadata], indent=2, default=str))
    return list_of_integration_item_metadata