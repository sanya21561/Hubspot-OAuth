import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': { endpoint: 'notion', path: 'load' },
    'Airtable': { endpoint: 'airtable', path: 'load' },
    'HubSpot': { endpoint: 'hubspot', path: 'get_hubspot_items' }, // Added endpointMapping for HubSpot
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const integrationConfig = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${integrationConfig.endpoint}/${integrationConfig.path}`, formData); // Changed to match path for all three
            const data = response.data;
            setLoadedData(data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        }
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                <TextField
                    label="Loaded Data"
                    value={loadedData ? JSON.stringify(loadedData, null, 2) : ''} // Used JSON.stringify for readable output
                    sx={{mt: 2}}
                    InputLabelProps={{ shrink: true }}
                    multiline
                    minRows={6}
                    disabled
                />
                <Button
                    onClick={handleLoad}
                    sx={{mt: 2}}
                    variant='contained'
                >
                    Load Data
                </Button>
                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{mt: 1}}
                    variant='contained'
                >
                    Clear Data
                </Button>
            </Box>
        </Box>
    );
}
