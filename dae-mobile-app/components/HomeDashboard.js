import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, ActivityIndicator, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { setApiBaseUrl, testConnection, getApiBaseUrl, loadApiBaseUrl, saveApiBaseUrl } from '../src/api';

export default function HomeDashboard({ onNavigate }) {

    const [ipAddress, setIpAddress] = useState('');
    const [isConnecting, setIsConnecting] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState('IDLE'); // IDLE, CONNECTED, FAILED
    const [debugLog, setDebugLog] = useState([]);

    useEffect(() => {
        const loadIp = async () => {
            const savedIp = await loadApiBaseUrl();
            if (savedIp) {
                setIpAddress(savedIp);
                // Optional: Auto-connect or just pre-fill. 
                // Let's just pre-fill for now to avoid loops if IP is bad.
            } else {
                setIpAddress('172.20.10.13'); // Default fallback
            }
        };
        loadIp();
    }, []);

    const addLog = (msg) => {
        const time = new Date().toLocaleTimeString();
        setDebugLog(prev => [`[${time}] ${msg}`, ...prev]);
    };

    const handleConnect = async () => {
        if (!ipAddress) {
            Alert.alert("Error", "Please enter an IP address");
            return;
        }

        setIsConnecting(true);
        setConnectionStatus('CONNECTING');
        setDebugLog([]); // Clear logs on new attempt

        addLog(`Starting connection attempt...`);
        addLog(`Input IP: ${ipAddress}`);

        setApiBaseUrl(ipAddress);
        const targetUrl = getApiBaseUrl();
        addLog(`Target URL set to: ${targetUrl}`);

        try {
            addLog(`Sending request to ${targetUrl}/status...`);

            // Use specialized test func with timeout
            const result = await testConnection();

            addLog(`Response received! Status: ${result.status}`);
            setConnectionStatus('CONNECTED');
            addLog("Connection Successful.");

            // Persist the working IP
            saveApiBaseUrl(ipAddress);

        } catch (e) {
            console.log("Connect Error:", e);
            setConnectionStatus('FAILED');
            addLog(`ERROR: ${e.message}`);
            Alert.alert("Connection Failed", e.message);
        } finally {
            setIsConnecting(false);
        }
    };

    const menuItems = [
        {
            id: 'INSTALL',
            title: 'Installation Verifier',
            desc: 'Validate install quality & readiness',
            color: '#4CAF50',
            icon: '✓'
        },
        {
            id: 'SIMULATE',
            title: 'Simulate Incident',
            desc: 'Inject faults to test detection',
            color: '#FF9500',
            icon: '⚠'
        },
        {
            id: 'OBH',
            title: 'One Button Helper',
            desc: 'Instant diagnose & capture',
            color: '#FF3B30',
            icon: '⛑'
        },
        {
            id: 'FLEET',
            title: 'Fleet View',
            desc: 'Monitor all devices (Legacy)',
            color: '#007AFF',
            icon: '📱'
        },
        {
            id: 'METRICS',
            title: 'Metrics Dashboard',
            desc: 'Real-time performance stats',
            color: '#9C27B0',
            icon: '📊'
        }
    ];

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>DAE Field Tool</Text>
                <Text style={styles.headerSubtitle}>Technician Dashboard</Text>
            </View>

            <View style={styles.connectionCard}>
                <Text style={styles.sectionTitle}>Server Connection</Text>
                <View style={styles.inputRow}>
                    <TextInput
                        style={styles.input}
                        placeholder="Enter Server IP (e.g. 192.168.1.5)"
                        value={ipAddress}
                        onChangeText={setIpAddress}
                        autoCapitalize="none"
                        autoCorrect={false}
                        keyboardType="url"
                    />
                    <TouchableOpacity
                        style={[
                            styles.connectButton,
                            connectionStatus === 'CONNECTED' && styles.connectedButton,
                            connectionStatus === 'FAILED' && styles.failedButton
                        ]}
                        onPress={handleConnect}
                        disabled={isConnecting}
                    >
                        {isConnecting ? (
                            <ActivityIndicator color="#FFF" size="small" />
                        ) : (
                            <Text style={styles.connectButtonText}>
                                {connectionStatus === 'CONNECTED' ? 'LINKED' : connectionStatus === 'FAILED' ? 'RETRY' : 'CONNECT'}
                            </Text>
                        )}
                    </TouchableOpacity>
                </View>
                {connectionStatus === 'CONNECTED' && (
                    <Text style={styles.statusSuccess}>● Connected to Core Service</Text>
                )}

                {/* Debug Console */}
                <View style={styles.debugContainer}>
                    <Text style={styles.debugTitle}>Debug Log:</Text>
                    <ScrollView style={styles.debugScroll} nestedScrollEnabled={true}>
                        {debugLog.length === 0 ? (
                            <Text style={styles.debugTextPlaceholder}>Waiting for connection...</Text>
                        ) : (
                            debugLog.map((log, idx) => (
                                <Text key={idx} style={styles.debugText}>{log}</Text>
                            ))
                        )}
                    </ScrollView>
                </View>
            </View>

            <ScrollView contentContainerStyle={styles.menuContainer}>
                {menuItems.map((item) => (
                    <TouchableOpacity
                        key={item.id}
                        style={[styles.card, { borderLeftColor: item.color }]}
                        onPress={() => onNavigate(item.id)}
                        disabled={connectionStatus !== 'CONNECTED' && item.id !== 'FLEET'}
                    >
                        <View style={[styles.iconCircle, { backgroundColor: connectionStatus === 'CONNECTED' ? item.color : '#ccc' }]}>
                            <Text style={styles.iconText}>{item.icon}</Text>
                        </View>
                        <View style={styles.textContainer}>
                            <Text style={[styles.cardTitle, connectionStatus !== 'CONNECTED' && { color: '#999' }]}>{item.title}</Text>
                            <Text style={styles.cardDesc}>{item.desc}</Text>
                        </View>
                        <Text style={styles.arrow}>→</Text>
                    </TouchableOpacity>
                ))}
            </ScrollView>

            <Text style={styles.footer}>DAE P1 Modules v1.9</Text>
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
        paddingBottom: 20,
        paddingHorizontal: 20,
        backgroundColor: '#FFF',
        borderBottomWidth: 1,
        borderBottomColor: '#E5E5EA',
    },
    headerTitle: {
        fontSize: 28,
        fontWeight: '800',
        color: '#000',
    },
    headerSubtitle: {
        fontSize: 16,
        color: '#8E8E93',
        fontWeight: '500',
    },
    connectionCard: {
        margin: 20,
        marginBottom: 10,
        padding: 15,
        backgroundColor: '#FFF',
        borderRadius: 12,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
    sectionTitle: {
        fontSize: 12,
        color: '#888',
        fontWeight: '600',
        textTransform: 'uppercase',
        marginBottom: 10,
    },
    inputRow: {
        flexDirection: 'row',
        gap: 10,
        marginBottom: 15,
    },
    input: {
        flex: 1,
        backgroundColor: '#F2F2F7',
        borderRadius: 8,
        paddingHorizontal: 12,
        paddingVertical: 10,
        fontSize: 16,
        color: '#333',
    },
    connectButton: {
        backgroundColor: '#007AFF',
        borderRadius: 8,
        paddingHorizontal: 20,
        justifyContent: 'center',
        alignItems: 'center',
        minWidth: 100,
    },
    connectedButton: {
        backgroundColor: '#34C759',
    },
    failedButton: {
        backgroundColor: '#FF3B30',
    },
    connectButtonText: {
        color: '#FFF',
        fontWeight: '600',
        fontSize: 14,
    },
    statusSuccess: {
        color: '#34C759',
        fontSize: 12,
        fontWeight: '500',
        marginTop: 8,
        marginLeft: 4,
    },
    debugContainer: {
        marginTop: 10,
        backgroundColor: '#333',
        borderRadius: 8,
        padding: 10,
        height: 120,
    },
    debugTitle: {
        color: '#AAA',
        fontSize: 10,
        marginBottom: 5,
        textTransform: 'uppercase',
    },
    debugScroll: {
        flex: 1,
    },
    debugText: {
        color: '#0F0',
        fontSize: 11,
        fontFamily: 'monospace',
        marginBottom: 2,
    },
    debugTextPlaceholder: {
        color: '#666',
        fontSize: 11,
        fontStyle: 'italic',
    },
    menuContainer: {
        padding: 20,
        paddingTop: 10,
    },
    card: {
        backgroundColor: '#FFF',
        borderRadius: 16,
        padding: 20,
        marginBottom: 16,
        flexDirection: 'row',
        alignItems: 'center',
        shadowColor: "#000",
        shadowOffset: {
            width: 0,
            height: 2,
        },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
        borderLeftWidth: 6,
    },
    iconCircle: {
        width: 50,
        height: 50,
        borderRadius: 25,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: 15,
    },
    iconText: {
        fontSize: 24,
        color: '#FFF',
        fontWeight: 'bold',
    },
    textContainer: {
        flex: 1,
    },
    cardTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#000',
        marginBottom: 4,
    },
    cardDesc: {
        fontSize: 14,
        color: '#666',
    },
    arrow: {
        fontSize: 24,
        color: '#C7C7CC',
        marginLeft: 10,
    },
    footer: {
        textAlign: 'center',
        padding: 20,
        color: '#999',
        fontSize: 12
    }
});
