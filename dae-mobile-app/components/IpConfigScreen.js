import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, ScrollView } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function IpConfigScreen({ onConnect }) {
    const [ip, setIp] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        const loadSavedIp = async () => {
            try {
                const saved = await AsyncStorage.getItem('api_ip');
                if (saved) {
                    setIp(saved);
                }
            } catch (e) {
                console.error('Failed to load IP', e);
            }
        };
        loadSavedIp();
    }, []);

    const handleConnect = async () => {
        if (!ip) return;

        setIsLoading(true);
        setError(null);
        setSuccess(false);

        // Auto-fix common input errors
        let cleanIp = ip.trim();
        if (!cleanIp.startsWith('http://') && !cleanIp.startsWith('https://')) {
            cleanIp = 'http://' + cleanIp;
        }

        // Remove trailing slash if present for consistency
        if (cleanIp.endsWith('/')) {
            cleanIp = cleanIp.slice(0, -1);
        }

        try {
            // Health check ping
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

            const response = await fetch(`${cleanIp}/`, {
                method: 'GET',
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (response.ok) {
                setSuccess(true);
                await AsyncStorage.setItem('api_ip', cleanIp);

                // Short delay to show success message
                setTimeout(() => {
                    onConnect(cleanIp);
                }, 500);
            } else {
                throw new Error(`Server returned ${response.status}`);
            }
        } catch (e) {
            console.log('Connection failed', e);
            let msg = e.message || 'Unknown error';
            if (e.name === 'AbortError' || msg.includes('aborted')) {
                msg = 'Timed Out (Check Firewall)';
            }
            setError(`Connect Failed: ${msg}`);
            setIsLoading(false);
        }
    };

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <Text style={styles.title}>DAE P1 Config</Text>
            <Text style={styles.label}>Enter Backend IP Address:</Text>

            <TextInput
                style={[styles.input, error && styles.inputError]}
                value={ip}
                onChangeText={setIp}
                placeholder="e.g. 192.168.1.100:8000"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading && !success}
            />

            {error && (
                <Text style={styles.errorText}>{error}</Text>
            )}

            {success && (
                <Text style={styles.successText}>✓ Connected!</Text>
            )}

            <TouchableOpacity
                style={[styles.button, (isLoading || success) && styles.buttonDisabled]}
                onPress={handleConnect}
                disabled={isLoading || success}
            >
                {isLoading ? (
                    <ActivityIndicator color="#fff" />
                ) : (
                    <Text style={styles.buttonText}>{success ? 'Redirecting...' : 'Connect'}</Text>
                )}
            </TouchableOpacity>

            <Text style={styles.hint}>
                Ensure your phone is on the same Wi-Fi network as the backend server.
            </Text>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flexGrow: 1,
        padding: 24,
        justifyContent: 'center',
        backgroundColor: '#fff',
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        marginBottom: 48,
        textAlign: 'center',
        color: '#333',
    },
    label: {
        fontSize: 16,
        marginBottom: 8,
        color: '#666',
    },
    input: {
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        marginBottom: 12,
        backgroundColor: '#f9f9f9',
    },
    inputError: {
        borderColor: '#ff4444',
    },
    errorText: {
        color: '#ff4444',
        marginBottom: 12,
        fontSize: 14,
    },
    successText: {
        color: '#00C851',
        marginBottom: 12,
        fontSize: 16,
        fontWeight: 'bold',
        textAlign: 'center',
    },
    button: {
        backgroundColor: '#007AFF',
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
        height: 54, // Fixed height to prevent layout jump
        justifyContent: 'center'
    },
    buttonDisabled: {
        backgroundColor: '#99c9ff',
    },
    buttonText: {
        color: '#fff',
        fontSize: 16,
        fontWeight: '600',
    },
    hint: {
        marginTop: 24,
        textAlign: 'center',
        color: '#999',
        fontSize: 14,
    }
});
