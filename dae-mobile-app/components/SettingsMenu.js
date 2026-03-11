import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getBaseUrl, setBaseUrl } from '../src/api';

export default function SettingsMenu({ onNavigate, onBack }) {
    const [ip, setIp] = useState(getBaseUrl());
    const [isLoading, setIsLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState(null);
    const [successMsg, setSuccessMsg] = useState(null);

    const handleSave = async () => {
        setIsLoading(true);
        setErrorMsg(null);
        setSuccessMsg(null);

        let cleanIp = ip.trim();
        if (cleanIp && !cleanIp.startsWith('http://') && !cleanIp.startsWith('https://')) {
            cleanIp = 'http://' + cleanIp;
        }
        if (cleanIp.endsWith('/')) {
            cleanIp = cleanIp.slice(0, -1);
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            console.log(`Pinging ${cleanIp}...`);
            const response = await fetch(`${cleanIp}/`, {
                method: 'GET',
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (response.ok) {
                setBaseUrl(cleanIp);
                await AsyncStorage.setItem('api_ip', cleanIp);
                setSuccessMsg(`✓ Connected to ${cleanIp}`);
            } else {
                throw new Error(`Server returned status ${response.status}`);
            }
        } catch (e) {
            console.error(e);
            let msg = e.message;
            if (e.name === 'AbortError' || msg.includes('aborted')) {
                msg = 'Connection Timed Out. (Check Firewall?)';
            } else if (msg.includes('Network request failed')) {
                msg = 'Network Error. (Check IP/Wi-Fi)';
            }
            setErrorMsg(`Failed: ${msg}`);
        } finally {
            setIsLoading(false);
        }
    };

    const settingsItems = [
        {
            id: 'SIMULATE',
            title: 'Simulate Incident (M17)',
            desc: 'Inject faults to test detection logic',
            icon: '⚠'
        },
        {
            id: 'CSR_DASHBOARD',
            title: 'CSR Support Console',
            desc: 'Simulate agent fetching BYUSE diagnostic data',
            icon: '🎧'
        },
        {
            id: 'DOMAIN_OVERRIDE',
            title: 'Target Demo Domain',
            desc: 'Force app environment (Wi-Fi / Cable)',
            icon: '🔌'
        }
    ];

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Settings</Text>
                <View style={{ width: 60 }} />
            </View>

            <ScrollView contentContainerStyle={styles.menuContainer}>
                <Text style={styles.sectionHeader}>Connection Settings</Text>
                <View style={styles.inputContainer}>
                    <Text style={styles.inputLabel}>Backend URL</Text>
                    <TextInput
                        style={styles.input}
                        value={ip}
                        onChangeText={setIp}
                        autoCapitalize="none"
                        autoCorrect={false}
                        placeholder="http://192.168.x.x:8000"
                        editable={!isLoading}
                    />

                    {errorMsg && <Text style={styles.errorText}>{errorMsg}</Text>}
                    {successMsg && <Text style={styles.successText}>{successMsg}</Text>}

                    <TouchableOpacity
                        style={[styles.saveButton, isLoading && styles.saveButtonDisabled]}
                        onPress={handleSave}
                        disabled={isLoading}
                    >
                        {isLoading ? (
                            <ActivityIndicator color="#FFF" />
                        ) : (
                            <Text style={styles.saveButtonText}>Save & Connect</Text>
                        )}
                    </TouchableOpacity>
                </View>

                <Text style={styles.sectionHeader}>Developer Options</Text>

                {settingsItems.map((item) => (
                    <TouchableOpacity
                        key={item.id}
                        style={styles.itemRow}
                        onPress={() => onNavigate(item.id)}
                    >
                        <View style={styles.iconContainer}>
                            <Text style={styles.iconText}>{item.icon}</Text>
                        </View>
                        <View style={styles.textContainer}>
                            <Text style={styles.itemTitle}>{item.title}</Text>
                            <Text style={styles.itemDesc}>{item.desc}</Text>
                        </View>
                        <Text style={styles.arrow}>›</Text>
                    </TouchableOpacity>
                ))}

                <View style={styles.versionContainer}>
                    <Text style={styles.versionText}>DAE P1 Mobile App v1.0</Text>
                </View>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F2F2F7',
    },
    header: {
        paddingTop: 60,
        paddingBottom: 16,
        paddingHorizontal: 16,
        backgroundColor: '#FFF',
        borderBottomWidth: 1,
        borderBottomColor: '#C6C6C8',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    backButton: {
        padding: 8,
        minWidth: 60,
    },
    backButtonText: {
        fontSize: 17,
        color: '#007AFF',
    },
    headerTitle: {
        fontSize: 17,
        fontWeight: '600',
        color: '#000',
    },
    menuContainer: {
        paddingVertical: 20,
    },
    sectionHeader: {
        fontSize: 13,
        color: '#6D6D72',
        marginBottom: 8,
        paddingHorizontal: 16,
        textTransform: 'uppercase',
    },
    itemRow: {
        backgroundColor: '#FFF',
        paddingVertical: 12,
        paddingHorizontal: 16,
        flexDirection: 'row',
        alignItems: 'center',
        borderTopWidth: StyleSheet.hairlineWidth,
        borderBottomWidth: StyleSheet.hairlineWidth,
        borderColor: '#C6C6C8',
        marginBottom: 20,
    },
    iconContainer: {
        width: 30,
        alignItems: 'center',
        marginRight: 12,
    },
    iconText: {
        fontSize: 22,
    },
    textContainer: {
        flex: 1,
    },
    itemTitle: {
        fontSize: 17,
        color: '#000',
        marginBottom: 2,
    },
    itemDesc: {
        fontSize: 13,
        color: '#8E8E93',
    },
    arrow: {
        fontSize: 20,
        color: '#C7C7CC',
        marginLeft: 8,
    },
    versionContainer: {
        padding: 20,
        alignItems: 'center',
    },
    versionText: {
        fontSize: 13,
        color: '#8E8E93',
    },
    inputContainer: {
        backgroundColor: '#FFF',
        padding: 16,
        marginBottom: 20,
        borderTopWidth: StyleSheet.hairlineWidth,
        borderBottomWidth: StyleSheet.hairlineWidth,
        borderColor: '#C6C6C8',
    },
    inputLabel: {
        fontSize: 13,
        color: '#6D6D72',
        marginBottom: 8,
        textTransform: 'uppercase',
    },
    input: {
        height: 44,
        borderWidth: 1,
        borderColor: '#C6C6C8',
        borderRadius: 8,
        paddingHorizontal: 12,
        fontSize: 17,
        marginBottom: 12,
        backgroundColor: '#F9F9F9',
    },
    saveButtonText: {
        color: '#FFF',
        fontSize: 17,
        fontWeight: '600',
    },
    saveButtonDisabled: {
        backgroundColor: '#99c9ff',
    },
    errorText: {
        color: '#ff4444',
        fontSize: 13,
        marginBottom: 12,
        paddingHorizontal: 4,
    },
    successText: {
        color: '#00C851',
        fontSize: 13,
        marginBottom: 12,
        paddingHorizontal: 4,
        fontWeight: 'bold',
    },
    saveButton: {
        backgroundColor: '#007AFF',
        borderRadius: 8,
        paddingVertical: 12,
        alignItems: 'center',
    }
});
