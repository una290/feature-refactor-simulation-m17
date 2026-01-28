import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, StyleSheet, TouchableOpacity, Image } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function IpConfigScreen({ onConnect }) {
    const [ip, setIp] = useState('');

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

        // Auto-fix common input errors
        let cleanIp = ip.trim();
        if (!cleanIp.startsWith('http://') && !cleanIp.startsWith('https://')) {
            cleanIp = 'http://' + cleanIp;
        }

        try {
            await AsyncStorage.setItem('api_ip', cleanIp);
            onConnect(cleanIp);
        } catch (e) {
            console.error('Failed to save IP', e);
        }
    };

    return (
        <View style={styles.container}>
            <Text style={styles.title}>DAE P1 Config</Text>
            <Text style={styles.label}>Enter Backend IP Address:</Text>

            <TextInput
                style={styles.input}
                value={ip}
                onChangeText={setIp}
                placeholder="e.g. 192.168.1.100:8000"
                autoCapitalize="none"
                autoCorrect={false}
            />

            <TouchableOpacity style={styles.button} onPress={handleConnect}>
                <Text style={styles.buttonText}>Connect</Text>
            </TouchableOpacity>

            <Text style={styles.hint}>
                Ensure your phone is on the same Wi-Fi network as the backend server.
            </Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
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
        marginBottom: 24,
        backgroundColor: '#f9f9f9',
    },
    button: {
        backgroundColor: '#007AFF',
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
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
