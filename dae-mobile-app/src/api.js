// Default value is empty, forcing user to input via IpConfigScreen
export let API_BASE_URL = '';
// export const API_BASE_URL = 'http://172.18.129.27:8000'; // Legacy default

export const setBaseUrl = (url) => {
    API_BASE_URL = url;
};

export const getBaseUrl = () => API_BASE_URL;

export const fetchMetrics = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/metrics`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching metrics:", error);
        return null;
    }
};

export const fetchEvents = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/events`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching events:", error);
        return [];
    }
};

export const fetchSnapshots = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/snapshots`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching snapshots:", error);
        return [];
    }
};

export const triggerRecognition = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/recognition`);
        return await response.json();
    } catch (error) {
        console.error("Error triggering recognition:", error);
        return null;
    }
};

export const checkInstallVerification = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/install_verify`);
        return await response.json();
    } catch (error) {
        console.error("Error checking install verification:", error);
        return null;
    }
};

export const fetchStatus = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching status:", error);
        return null;
    }
};

export const fetchFleet = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/fleet`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching fleet:", error);
        return [];
    }
};

export const fetchDeviceDetail = async (deviceId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/device/${deviceId}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching device detail for ${deviceId}:`, error);
        return null;
    }
};

export const fetchProofData = async (deviceId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/device/${deviceId}/proof`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching proof for ${deviceId}:`, error);
        return null;
    }
};

export const fetchManifest = async (deviceId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/device/${deviceId}/manifest`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching manifest for ${deviceId}:`, error);
        return null;
    }
};

export const simulateIncident = async (type, duration) => {
    try {
        const response = await fetch(`${API_BASE_URL}/simulate/incident?type=${type}&duration=${duration}`, {
            method: 'POST'
        });
        return await response.json();
    } catch (error) {
        console.error("Error simulating incident:", error);
        return null;
    }
};

export const triggerOBH = async (context = null) => {
    try {
        let url = `${API_BASE_URL}/obh/trigger`;
        if (context) {
            url += `?context=${encodeURIComponent(context)}`;
        }
        const response = await fetch(url, {
            method: 'POST'
        });
        return await response.json();
    } catch (error) {
        console.error("Error triggering OBH:", error);
        return null;
    }
};

export const fetchOBHBundle = async (episodeId, context = null) => {
    try {
        let url = `${API_BASE_URL}/obh/proofcard/${encodeURIComponent(episodeId)}`;
        if (context) {
            url += `?context=${encodeURIComponent(context)}`;
        }
        const response = await fetch(url);
        return await response.json();
    } catch (error) {
        console.error("Error fetching OBH bundle:", error);
        return null;
    }
};

export const signManifest = async (episodeId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/obh/manifest/sign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ episode_id: episodeId })
        });
        return await response.json();
    } catch (error) {
        console.error("Error signing manifest:", error);
        return null;
    }
};

export const requestConsent = async (episodeId, csrId = "8871") => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/obh/consent/request`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ episode_id: episodeId, csr_id: csrId })
        });
        return await response.json();
    } catch (error) {
        console.error("Error requesting consent:", error);
        return null;
    }
};

export const fetchPendingConsents = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/obh/consent/pending`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching pending consents:", error);
        return { pending_requests: [] };
    }
};
