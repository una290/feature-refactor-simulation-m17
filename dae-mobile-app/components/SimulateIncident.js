import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert, FlatList } from 'react-native';
import { simulateIncident } from '../src/api';

export default function SimulateIncident({ onBack }) {
    const [selectedType, setSelectedType] = useState('latency');
    const [duration, setDuration] = useState(30);
    const [activeIncidents, setActiveIncidents] = useState([]);

    // Ref to track intervals and clean them up
    const intervalRef = useRef(null);

    const incidentTypes = [
        {
            id: 'latency',
            label: 'Latency Spike',
            desc: 'Variable Jitter (80-140ms)',
            keys: [
                { name: 'latency_ms', desc: 'Round-Trip Time', range: '80-140ms' },
                { name: 'jitter', desc: 'Delay Variance', range: '10-30ms' }
            ]
        },
        {
            id: 'retry',
            label: 'High Packet Loss',
            desc: 'Heavy Loss (15-30%)',
            keys: [
                { name: 'packet_loss_percent', desc: 'Loss Ratio', range: '15-30%' },
                { name: 'retransmissions', desc: 'Retry Count', range: 'High' }
            ]
        },
        {
            id: 'airtime',
            label: 'Airtime Congestion',
            desc: 'Severe Congestion (70-95%)',
            keys: [
                { name: 'channel_utilization', desc: 'Airtime Usage', range: '70-95%' },
                { name: 'queue_depth', desc: 'Tx Queue', range: '> 50 pkts' }
            ]
        },
        {
            id: 'complex',
            label: 'Complex Incident',
            desc: 'Multi-factor Chaos',
            keys: [
                { name: 'latency', desc: 'RTT', range: 'Variable' },
                { name: 'loss', desc: 'Packet Drop', range: '5-15%' },
                { name: 'throughput', desc: 'Bandwidth', range: 'Degrading' }
            ]
        },
        {
            id: 'oscillating',
            label: 'Oscillating',
            desc: 'Square wave + Bursts',
            keys: [
                { name: 'signal_strength', desc: 'RSSI', range: '-60 to -85dBm' },
                { name: 'noise_floor', desc: 'Interference', range: '-90dBm' }
            ]
        },
        {
            id: 'degrading',
            label: 'Degrading',
            desc: 'Slow drift into failure',
            keys: [
                { name: 'error_rate', desc: 'PER increase', range: '0% -> 10%' },
                { name: 'snr', desc: 'Signal/Noise', range: 'Dropping' }
            ]
        },
    ];

    useEffect(() => {
        intervalRef.current = setInterval(() => {
            setActiveIncidents(currentIncidents => {
                if (currentIncidents.length === 0) return currentIncidents;

                return currentIncidents.map(incident => {
                    const timeLeft = incident.timeLeft - 1;

                    // Add a mock log every 5 seconds
                    let newLogs = incident.logs;
                    if (timeLeft % 5 === 0 && timeLeft > 0) {
                        const timestamp = new Date().toLocaleTimeString();
                        const val = Math.floor(Math.random() * 100);
                        newLogs = [...newLogs, { time: timestamp, msg: `Sent batch: ${val} units` }];
                        if (newLogs.length > 5) newLogs.shift(); // Keep last 5 logs
                    }

                    return { ...incident, timeLeft, logs: newLogs };
                }).filter(incident => incident.timeLeft > 0); // Auto-remove finished
            });
        }, 1000);

        return () => clearInterval(intervalRef.current);
    }, []);

    const handleStartSimulation = async () => {
        const typeInfo = incidentTypes.find(t => t.id === selectedType);

        // 1. Add to active list immediately
        const newIncident = {
            id: Date.now().toString(), // Simple unique ID
            typeId: selectedType,
            label: typeInfo.label,
            duration: duration,
            timeLeft: duration,
            startTime: new Date().toLocaleTimeString(),
            logs: [{ time: new Date().toLocaleTimeString(), msg: 'Simulation Started' }]
        };

        setActiveIncidents(prev => [newIncident, ...prev]);

        // 2. Fire API
        // In a real app, we might wait for success, but for UI responsiveness we start immediately
        // and handle error if it fails (not implemented here for simplicity as per plan "Success Record" is visual)
        simulateIncident(selectedType, duration).catch(err => {
            console.error("Simulation API failed", err);
            // Optionally remove from list or show error state
        });
    };

    const handleDelete = (id) => {
        setActiveIncidents(prev => prev.filter(i => i.id !== id));
    };

    const handleClearAll = () => {
        setActiveIncidents([]);
    };

    const getPreviewData = () => {
        const type = incidentTypes.find(t => t.id === selectedType);
        return {
            description: `System will generate ${type.label} anomalies for ${duration} seconds.`,
            keys: type.keys, // now an array of objects
            target: 'All Modules (Default)' // Static for now as per plan
        };
    };

    const preview = getPreviewData();

    const formatTime = (seconds) => {
        const m = Math.floor(seconds / 60);
        const s = seconds % 60;
        return `${m < 10 ? '0' : ''}${m}:${s < 10 ? '0' : ''}${s}`;
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.title}>Simulate Incident</Text>
            </View>

            <ScrollView contentContainerStyle={styles.content}>

                {/* --- Step 1: Configuration --- */}
                <Text style={styles.sectionHeader}>1. Configure Incident</Text>

                <View style={styles.typeContainer}>
                    {/* LAN Section */}
                    <Text style={styles.categoryHeader}>LAN Incidents</Text>
                    <View style={styles.categoryRow}>
                        {incidentTypes.filter(t => ['latency', 'retry', 'airtime', 'complex'].includes(t.id)).map((type) => (
                            <TouchableOpacity
                                key={type.id}
                                style={[
                                    styles.typeButton,
                                    selectedType === type.id && styles.typeButtonSelected
                                ]}
                                onPress={() => setSelectedType(type.id)}
                            >
                                <Text style={[
                                    styles.typeLabel,
                                    selectedType === type.id && styles.typeLabelSelected
                                ]}>{type.label}</Text>
                            </TouchableOpacity>
                        ))}
                    </View>

                    {/* WAN Section */}
                    <Text style={[styles.categoryHeader, { marginTop: 15 }]}>WAN Incidents</Text>
                    <View style={styles.categoryRow}>
                        {incidentTypes.filter(t => ['oscillating', 'degrading'].includes(t.id)).map((type) => (
                            <TouchableOpacity
                                key={type.id}
                                style={[
                                    styles.typeButton,
                                    selectedType === type.id && styles.typeButtonSelected
                                ]}
                                onPress={() => setSelectedType(type.id)}
                            >
                                <Text style={[
                                    styles.typeLabel,
                                    selectedType === type.id && styles.typeLabelSelected
                                ]}>{type.label}</Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>

                <View style={styles.durationRow}>
                    <Text style={styles.label}>Duration:</Text>
                    {[10, 30, 60, 300].map(d => (
                        <TouchableOpacity
                            key={d}
                            onPress={() => setDuration(d)}
                            style={[styles.durBtn, duration === d && styles.durBtnActive]}
                        >
                            <Text style={duration === d ? styles.durTxtActive : styles.durTxt}>{d}s</Text>
                        </TouchableOpacity>
                    ))}
                </View>

                {/* --- Step 2: Preview --- */}
                <View style={styles.previewBox}>
                    <Text style={styles.previewTitle}>Preview</Text>
                    <Text style={styles.previewText}>• <Text style={styles.bold}>Action:</Text> {preview.description}</Text>
                    <Text style={styles.previewText}>• <Text style={styles.bold}>Target:</Text> {preview.target}</Text>

                    <Text style={[styles.previewText, { marginTop: 8 }]}><Text style={styles.bold}>Data Payload Preview:</Text></Text>
                    <View style={styles.keysTable}>
                        {preview.keys.map((k, idx) => (
                            <View key={idx} style={styles.keyRow}>
                                <Text style={styles.keyName}>{k.name}</Text>
                                <Text style={styles.keyDesc}>{k.desc}</Text>
                                <Text style={styles.keyRange}>({k.range})</Text>
                            </View>
                        ))}
                    </View>
                </View>

                <TouchableOpacity
                    style={styles.startButton}
                    onPress={handleStartSimulation}
                >
                    <Text style={styles.startButtonText}>START SIMULATION</Text>
                </TouchableOpacity>


                {/* --- Step 3: Live Tracking --- */}
                <View style={styles.trackingHeader}>
                    <Text style={styles.sectionHeader}>Active Incidents ({activeIncidents.length})</Text>
                    {activeIncidents.length > 0 && (
                        <TouchableOpacity onPress={handleClearAll}>
                            <Text style={styles.clearText}>Clear All</Text>
                        </TouchableOpacity>
                    )}
                </View>

                {activeIncidents.map(incident => (
                    <View key={incident.id} style={styles.incidentCard}>
                        <View style={styles.cardHeader}>
                            <View>
                                <Text style={styles.cardTitle}>{incident.label}</Text>
                                <Text style={styles.cardSub}>Started: {incident.startTime}</Text>
                            </View>
                            <View style={styles.timerContainer}>
                                <Text style={styles.timerText}>{formatTime(incident.timeLeft)}</Text>
                            </View>
                            <TouchableOpacity onPress={() => handleDelete(incident.id)} style={styles.delBtn}>
                                <Text style={styles.delBtnText}>X</Text>
                            </TouchableOpacity>
                        </View>

                        <View style={styles.logContainer}>
                            {incident.logs.map((log, idx) => (
                                <Text key={idx} style={styles.logText}>
                                    <Text style={styles.logTime}>[{log.time}]</Text> {log.msg}
                                </Text>
                            ))}
                        </View>
                    </View>
                ))}

                {activeIncidents.length === 0 && (
                    <Text style={styles.emptyState}>No active simulations.</Text>
                )}

            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f8f9fa',
    },
    header: {
        padding: 16,
        paddingTop: 50, // iOS status bar space roughly
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
        flexDirection: 'row',
        alignItems: 'center',
    },
    backButton: { marginRight: 15 },
    backText: { fontSize: 16, color: '#007AFF' },
    title: { fontSize: 20, fontWeight: '700' },
    content: { padding: 16, paddingBottom: 40 },

    sectionHeader: { fontSize: 18, fontWeight: '700', marginBottom: 15, color: '#222' },

    typeContainer: { marginBottom: 10 },
    categoryHeader: { fontSize: 14, fontWeight: 'bold', color: '#666', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
    categoryRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 5 },

    typeButton: {
        paddingHorizontal: 14,
        paddingVertical: 10,
        backgroundColor: '#fff',
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#ddd',
        marginRight: 8,
        marginBottom: 8,
        minWidth: '45%', // Ensure roughly 2 per row
        alignItems: 'center'
    },
    typeButtonSelected: {
        backgroundColor: '#007AFF',
        borderColor: '#007AFF',
    },
    typeLabel: { color: '#444', fontWeight: '500', fontSize: 14 },
    typeLabelSelected: { color: '#fff' },

    durationRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
    label: { fontSize: 16, marginRight: 10, color: '#555' },
    durBtn: {
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 8,
        marginRight: 8,
        backgroundColor: '#fff'
    },
    durBtnActive: { backgroundColor: '#007AFF', borderColor: '#007AFF' },
    durTxt: { color: '#333' },
    durTxtActive: { color: '#fff', fontWeight: '600' },

    previewBox: {
        backgroundColor: '#e3f2fd',
        padding: 15,
        borderRadius: 8,
        marginBottom: 20,
        borderLeftWidth: 4,
        borderLeftColor: '#2196f3'
    },
    previewTitle: { fontWeight: 'bold', marginBottom: 5, color: '#1565c0' },
    previewText: { fontSize: 14, color: '#0d47a1', marginBottom: 2 },
    bold: { fontWeight: '600' },

    keysTable: {
        backgroundColor: '#fff',
        borderRadius: 4,
        padding: 8,
        marginTop: 5,
        borderWidth: 1,
        borderColor: '#bbdefb'
    },
    keyRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingVertical: 4,
        borderBottomWidth: 1,
        borderBottomColor: '#f0f0f0'
    },
    keyName: { fontSize: 13, fontFamily: 'monospace', fontWeight: 'bold', color: '#333', flex: 1 },
    keyDesc: { fontSize: 13, color: '#555', flex: 1.5, paddingHorizontal: 5 },
    keyRange: { fontSize: 12, color: '#888', fontStyle: 'italic', flex: 1, textAlign: 'right' },

    startButton: {
        backgroundColor: '#2e7d32',
        paddingVertical: 15,
        borderRadius: 8,
        alignItems: 'center',
        marginBottom: 30,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 3,
        elevation: 2,
    },
    startButtonText: { color: '#fff', fontSize: 16, fontWeight: 'bold', letterSpacing: 1 },

    trackingHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
    clearText: { color: 'red', fontWeight: '600' },

    incidentCard: {
        backgroundColor: '#fff',
        borderRadius: 8,
        padding: 12,
        marginBottom: 10,
        borderWidth: 1,
        borderColor: '#eee',
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
        elevation: 1,
    },
    cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 },
    cardTitle: { fontSize: 16, fontWeight: 'bold', color: '#333' },
    cardSub: { fontSize: 12, color: '#888', marginTop: 2 },

    timerContainer: { backgroundColor: '#f0f0f0', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 },
    timerText: { fontFamily: 'monospace', fontWeight: 'bold', color: '#d32f2f' },

    delBtn: { padding: 5 },
    delBtnText: { color: '#999', fontSize: 18, fontWeight: 'bold' },

    logContainer: {
        backgroundColor: '#222',
        padding: 8,
        borderRadius: 4,
        maxHeight: 100
    },
    logText: { color: '#0f0', fontFamily: 'monospace', fontSize: 10, marginBottom: 2 },
    logTime: { color: '#888' },

    emptyState: { textAlign: 'center', color: '#999', marginTop: 20, fontStyle: 'italic' }
});
