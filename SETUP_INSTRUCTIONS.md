# HubSpot Integration Setup Instructions

## Overview
This explains how to set up and test the HubSpot OAuth integration using a Hubspot test account.

## Prerequisites
- Python 3.9+ (recommended, avoid 3.12/3.13 for best compatibility)
- Node.js & npm (for frontend)
- A HubSpot developer account ([sign up here](https://developers.hubspot.com/))

## 1. HubSpot App Setup
1. Go to your [HubSpot Developer Portal](https://developers.hubspot.com/).
2. Create a new app (e.g., "IntegrationTestApp").
3. In the **Auth** tab:
   - Add the redirect URI: `http://localhost:8000/integrations/hubspot/oauth2callback`
   - Add the **oauth** scope (for developer test accounts).
   - Save your changes.
4. Copy your **Client ID** and **Client Secret**.

## 2. Use a Sandbox Account
- Create a sandbox account in the HubSpot developer portal under the "Testing" section and use that for testing the integration.

## 3. Backend Setup
1. In `backend/integrations/hubspot.py`, set your credentials:
   ```python
   CLIENT_ID = 'your_client_id_here'
   CLIENT_SECRET = 'your_client_secret_here'
   REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'
   authorization_url = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=oauth'
   ```
2. The backend code handles OAuth, stores state in Redis, and fetches contacts from the sandbox account.
3. Install backend dependencies:
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
4. Start Redis:
   ```bash
   redis-server
   ```
5. Start the backend server:
   ```bash
   python -m uvicorn main:app --reload
   ```

## 4. Frontend Setup
1. In `frontend/src/integration-form.js`, added HubSpot to the integration mapping:
   ```js
   import { HubspotIntegration } from './integrations/hubspot';
   // ...
   const integrationMapping = {
     'Notion': NotionIntegration,
     'Airtable': AirtableIntegration,
     'HubSpot': HubspotIntegration,
   };
   ```
2. In `frontend/src/data-form.js`, updated the endpoint mapping:
   ```js
   const endpointMapping = {
     'Notion': { endpoint: 'notion', path: 'load' },
     'Airtable': { endpoint: 'airtable', path: 'load' },
     'HubSpot': { endpoint: 'hubspot', path: 'get_hubspot_items' },
   };
   // ...
   <TextField
     label="Loaded Data"
     value={loadedData ? JSON.stringify(loadedData, null, 2) : ''}
     multiline
     minRows={6}
     // ...
   />
   ```
3. In `frontend/src/integrations/hubspot.js`, used the same OAuth connection pattern as Airtable/Notion.

## 5. Running the App
1. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```
2. Open [http://localhost:3000](http://localhost:3000) in your browser.
3. Select "HubSpot" and connect using your sandbox account.
4. Click "Load Data" to fetch and display contacts.

## 6. Troubleshooting
- **Scope mismatch:** Make sure the scope in your app settings and in the code match exactly (`oauth`).
- **State does not match:** Complete the OAuth flow in a single window, and don't let the popup expire.
- **Developer account restriction:** Use a sandbox account, not the developer account.
- **[object Object] in frontend:** Used `JSON.stringify` to display objects as readable JSON.


## 7. Summary of Code Changes
- **backend/integrations/hubspot.py:**
  - Added OAuth flow, credential storage, and contact fetching.
  - Fixed timestamp parsing for HubSpot API.
- **backend/main.py:**
  - Added routes for HubSpot authorize, callback, credentials, and get_hubspot_items.
- **frontend/src/integration-form.js:**
  - Added HubSpot to integration mapping.
- **frontend/src/data-form.js:**
  - Added endpoint mapping for HubSpot and improved JSON display.
- **frontend/src/integrations/hubspot.js:**
  - Implemented OAuth connect UI for HubSpot.

## API Endpoints

- `POST /integrations/hubspot/authorize` - Initiates OAuth flow
- `GET /integrations/hubspot/oauth2callback` - OAuth callback handler
- `POST /integrations/hubspot/credentials` - Retrieves stored credentials
- `POST /integrations/hubspot/get_hubspot_items` - Fetches HubSpot contacts 
