import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, FlatList, TouchableOpacity, ActivityIndicator } from 'react-native';
import { fetchHistorySummary } from '../src/api';

const ProofCardList = ({ onNavigateToMin, onBack }) => {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadData = async () => {
        setLoading(true);
        const res = await fetchHistorySummary();
        if (res && res.status === "Success") {
            setHistory(res.history || []);
        }
        setLoading(false);
    };

    useEffect(() => {
        loadData();
    }, []);

    const renderItem = ({ item }) => {
        return (
            <TouchableOpacity style={styles.card} onPress={() => onNavigateToMin(item.episode_id)}>
                <View style={styles.row}>
                    <Text style={styles.idText}>{item.episode_id}</Text>
                    <Text style={[styles.verdictText, { color: item.verdict === 'PASS' ? '#2e7d32' : (item.verdict === 'FAIL' ? '#c62828' : '#e65100') }]}>
                        {item.verdict || 'UNKNOWN'}
                    </Text>
                </View>
                <View style={[styles.row, { marginTop: 8 }]}>
                    <Text style={styles.timeText}>{item.time || "Unknown Time"}</Text>
                    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                        <Text style={[styles.refText, { backgroundColor: item.is_dispute ? '#ffebee' : '#e3f2fd', color: item.is_dispute ? '#c62828' : '#1565c0', marginRight: 4 }]}>
                            {item.is_dispute ? 'DISPUTE' : 'ROUTINE'}
                        </Text>
                        <Text style={[styles.refText, { backgroundColor: item.is_signed ? '#e8f5e9' : '#fff3e0', color: item.is_signed ? '#2e7d32' : '#e65100' }]}>
                            {item.is_signed ? 'SIGNED' : 'UNSIGNED'}
                        </Text>
                    </View>
                </View>
            </TouchableOpacity>
        );
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Proof Card Archive</Text>
                <View style={{ width: 50 }} />
            </View>

            {loading ? (
                <ActivityIndicator size="large" color="#9C27B0" style={{ marginTop: 50 }} />
            ) : (
                <FlatList
                    data={history}
                    keyExtractor={(item) => item.episode_id}
                    renderItem={renderItem}
                    contentContainerStyle={styles.listContainer}
                    ListEmptyComponent={<Text style={styles.emptyText}>No historical proof cards found. Generate one in OBH!</Text>}
                />
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16, paddingTop: 40, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#ddd' },
    backButton: { paddingRight: 15 },
    backText: { fontSize: 16, color: '#007AFF' },
    headerTitle: { fontSize: 18, fontWeight: 'bold', color: '#333' },
    listContainer: { padding: 16 },
    card: { backgroundColor: '#fff', padding: 16, borderRadius: 8, marginBottom: 12, elevation: 2, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4, shadowOffset: { width: 0, height: 2 } },
    row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
    idText: { fontSize: 13, fontWeight: 'bold', fontFamily: 'monospace', color: '#333', maxWidth: '70%' },
    verdictText: { fontSize: 16, fontWeight: 'bold' },
    timeText: { fontSize: 12, color: '#666' },
    refText: { fontSize: 11, color: '#555', backgroundColor: '#e0e0e0', paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
    emptyText: { textAlign: 'center', marginTop: 40, color: '#888', fontStyle: 'italic' }
});

export default ProofCardList;
