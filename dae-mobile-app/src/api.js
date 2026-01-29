// api.js - Dynamic IP Support
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL_KEY = 'dae_api_base_url';

// Mutable state for the API Base URL
let apiBaseUrl = null;

/**
 * Set the API Base URL dynamically.
 * @param {string} ip - The IP address (and optional port) to connect to.
 */
export const setApiBaseUrl = (inputUrl) => {
    // Basic cleanup: remove trailing slash, add http if missing
    let url = inputUrl.trim();
    if (!url.startsWith('http')) {
        url = `http://${url}`;
    }
    // If user forgot port, maybe assume 8000? Or just let them fail. 
    // For now, let's assume the user types "192.168.1.10:8000" or just "192.168.1.10"
    // If just IP, append default port 8000 for convenience
    if (!url.split(':')[2]) {
        url = `${url}:8000`;
    }

    apiBaseUrl = url;
    console.log("API Base URL set to:", apiBaseUrl);
};

export const saveApiBaseUrl = async (url) => {
    try {
        await AsyncStorage.setItem(API_URL_KEY, url);
    } catch (e) {
        console.error("Failed to save API URL", e);
    }
};

export const loadApiBaseUrl = async () => {
    try {
        const value = await AsyncStorage.getItem(API_URL_KEY);
        if (value !== null) {
            setApiBaseUrl(value);
            return value;
        }
    } catch (e) {
        console.error("Failed to load API URL", e);
    }
    return null;
};

export const getApiBaseUrl = () => apiBaseUrl;

// Helper to check if API is configured
const isConfigured = () => {
    return apiBaseUrl !== null;
};

// Helper: Fetch with Timeout
const fetchWithTimeout = async (url, options = {}, timeout = 3000) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(id);
        return response;
    } catch (error) {
        clearTimeout(id);
        throw error;
    }
};

/**
 * Test connection explicitly and return detailed info or throw error.
 * Used by HomeDashboard for debugging.
 */
export const testConnection = async () => {
    if (!isConfigured()) throw new Error("API URL not configured");
    const url = `${apiBaseUrl}/status`;

    console.log(`[API] Testing connection to ${url}`);

    try {
        const response = await fetchWithTimeout(url, {}, 3000); // 3s timeout
        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status} ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error(`Timeout: Connection to ${url} timed out after 3000ms`);
        }
        throw new Error(`Network Error: ${error.message} (Target: ${url})`);
    }
};

export const fetchMetrics = async () => {
    if (!isConfigured()) return null;
    try {
        const response = await fetch(`${apiBaseUrl}/metrics`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching metrics:", error);
        return null;
    }
};

export const fetchEvents = async () => {
    if (!isConfigured()) return [];
    try {
        const response = await fetch(`${apiBaseUrl}/events`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching events:", error);
        return [];
    }
};

export const fetchSnapshots = async () => {
    if (!isConfigured()) return [];
    try {
        const response = await fetch(`${apiBaseUrl}/snapshots`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching snapshots:", error);
        return [];
    }
};

export const checkInstallVerification = async () => {
    if (!isConfigured()) return null;
    try {
        const response = await fetch(`${apiBaseUrl}/install_verify`);
        return await response.json();
    } catch (error) {
        console.error("Error checking install verification:", error);
        return null; // Ensure this returns null on error so UI can handle it
    }
};

export const triggerRecognition = async () => {
    if (!isConfigured()) return null;
    try {
        const response = await fetch(`${apiBaseUrl}/recognition`);
        return await response.json();
    } catch (error) {
        console.error("Error triggering recognition:", error);
        return null;
    }
};

export const fetchStatus = async () => {
    if (!isConfigured()) return null;
    try {
        const response = await fetch(`${apiBaseUrl}/status`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching status:", error);
        return null;
    }
};

export const fetchFleet = async () => {
    if (!isConfigured()) return [];
    try {
        const response = await fetch(`${apiBaseUrl}/fleet`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching fleet:", error);
        return [];
    }
};

export const fetchDeviceDetail = async (deviceId) => {
    if (!isConfigured()) return null;
    try {
        const response = await fetch(`${apiBaseUrl}/device/${deviceId}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching device detail for ${deviceId}:`, error);
        return null;
    }
};

export const fetchProofData = async (deviceId) => {
    if (!isConfigured()) return null;
    try {
        const response = await fetch(`${apiBaseUrl}/device/${deviceId}/proof`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching proof for ${deviceId}:`, error);
        return null;
    }
};

export const simulateIncident = async (type, duration) => {
    if (!isConfigured()) return null;
    try {
        const response = await fetch(`${apiBaseUrl}/simulate/incident?type=${type}&duration=${duration}`, {
            method: 'POST'
        });
        return await response.json();
    } catch (error) {
        console.error("Error simulating incident:", error);
        return null;
    }
};

export const triggerOBH = async () => {
    if (!isConfigured()) return null;
    try {
        const response = await fetch(`${apiBaseUrl}/obh/trigger`, {
            method: 'POST'
        });
        return await response.json();
    } catch (error) {
        console.error("Error triggering OBH:", error);
        return null;
    }
};
