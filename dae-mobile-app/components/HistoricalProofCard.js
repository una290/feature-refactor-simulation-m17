import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
import { fetchOBHBundle } from '../src/api';

const UnifiedHealthCard = ({ title, status, details, subtext, fontScale = 1.0, themeColor }) => {
    const s = String(status).toUpperCase();
    let color = '#757575', icon = '?';

    if (['FAIL', 'NOT_READY', 'DENY', 'STOP', 'PUBLIC', 'NOT_CLOSURE_GRADE', 'INSUFFICIENT_EVIDENCE'].includes(s)) {
        color = '#c62828'; icon = '✗';
    } else if (themeColor) {
        color = themeColor;
        icon = title === 'Data Range' ? '📅' : '✓';
    } else if (['PASS', 'ALL SYSTEMS GO', 'ADMIT', 'READY', 'PRIVATE', 'DELIVERY_GRADE', 'VALID', 'OK'].includes(s)) {
        color = '#2e7d32'; icon = '✓';
    } else {
        color = '#0288d1'; icon = 'ℹ';
    }

    return (
        <View style={[styles.unifiedCard, { borderLeftColor: color }]}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <View style={{ flex: 1 }}>
                    <Text style={[styles.checkName, { fontSize: 14 * fontScale }]}>{title}</Text>
                    {subtext ? <Text style={{ color: color, fontSize: 12 * fontScale, marginTop: 4 }}>{subtext}</Text> : null}
                </View>
                <Text style={{ color: color, fontWeight: 'bold', fontSize: 14 * fontScale }}>{icon} {status}</Text>
            </View>
            {details && details.reason_code && (
                <Text style={styles.reasonText}>Code: {details.reason_code}</Text>
            )}
        </View>
    );
};

export default function HistoricalProofCard({ episodeId, onBack }) {
    const [loading, setLoading] = useState(true);
    const [bundle, setBundle] = useState(null);
    const [error, setError] = useState(null);
    const fontScale = 1.0;

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            try {
                // Fetch only PC-Min with default context
                const res = await fetchOBHBundle(episodeId, "default", "pc_min");
                if (!res || res.error) throw new Error(res?.error || "Failed to load");
                setBundle(res.bundle);
            } catch (err) {
                setError(err.message);
            }
            setLoading(false);
        };
        if (episodeId) {
            load();
        }
    }, [episodeId]);

    const formatTimeNoLocale = (iso) => {
        if (!iso) return '-';
        const d = new Date(iso);
        const pad = (n) => n < 10 ? '0' + n : n;
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    };

    if (loading) return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}><Text style={styles.backText}>← Back</Text></TouchableOpacity>
                <Text style={styles.headerTitle}>PC-Min View</Text>
                <View style={{ width: 50 }} />
            </View>
            <ActivityIndicator size="large" color="#2196F3" style={{ marginTop: 50 }} />
        </View>
    );

    if (error) return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}><Text style={styles.backText}>← Back</Text></TouchableOpacity>
                <Text style={styles.headerTitle}>PC-Min View</Text>
                <View style={{ width: 50 }} />
            </View>
            <Text style={{ marginTop: 50, textAlign: 'center', color: 'red' }}>Error: {error}</Text>
        </View>
    );

    const pcMin = bundle?.pc_min;
    if (!pcMin) return <Text style={{ padding: 20 }}>No ProofCard Data Found</Text>;

    const isReady = pcMin.status === 'READY' || pcMin.verdict === 'READY';
    const finalStatus = pcMin.status || pcMin.verdict || 'UNKNOWN';
    const diagnosisCode = pcMin.diagnosis_code || 'UNKNOWN';
    const grade = pcMin.evidence_grade || 'UNKNOWN';

    const hasPrivacyMissing = pcMin.missing_evidence_class && pcMin.missing_evidence_class.length > 0;
    const privacyVerdict = hasPrivacyMissing ? 'FAIL' : 'PASS';
    const privacySubtext = hasPrivacyMissing ? pcMin.missing_evidence_class.join(", ") : "All Privacy Requirements Met";

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}><Text style={styles.backText}>← Back</Text></TouchableOpacity>
                <Text style={styles.headerTitle}>Historical PC-Min View</Text>
                <View style={{ width: 50 }} />
            </View>

            <ScrollView style={styles.content}>
                <View style={styles.summaryBox}>
                    <Text style={styles.summaryTitle}>Fast Compliance Check</Text>
                    <Text style={styles.summaryDesc}>Viewing optimized PC-Min payload only. No payload downloaded.</Text>
                </View>

                <UnifiedHealthCard
                    title="Network Status"
                    status={finalStatus}
                    subtext={isReady ? "Connection is stable" : `Diagnosis: ${diagnosisCode}`}
                    fontScale={fontScale}
                />

                <UnifiedHealthCard
                    title="Primary Privacy Check"
                    status={privacyVerdict}
                    subtext={privacySubtext}
                    fontScale={fontScale}
                    themeColor={hasPrivacyMissing ? '#c62828' : '#2196F3'}
                />

                <UnifiedHealthCard
                    title="Evidence Grade"
                    status={grade}
                    subtext={`For Context: Default (Routine)`}
                    fontScale={fontScale}
                    themeColor="#2196F3"
                />

                <UnifiedHealthCard
                    title="Data Range"
                    status="Timeline"
                    subtext={pcMin.data_range_start && pcMin.data_range_end ?
                        `${formatTimeNoLocale(pcMin.data_range_start)} ... ${formatTimeNoLocale(pcMin.data_range_end).split(' ')[1]}` :
                        "No Range Data"}
                    fontScale={fontScale}
                    themeColor="#ff9800"
                />

                <Text style={styles.sectionHeader}>TECHNICAL METADATA (Public)</Text>
                <View style={styles.metadataCard}>
                    <View style={styles.fieldRow}><Text style={styles.fieldLab}>Episode ID</Text><Text style={styles.fieldVal}>{pcMin.episode_id}</Text></View>
                    <View style={styles.fieldRow}><Text style={styles.fieldLab}>Window Ref</Text><Text style={styles.fieldVal}>{pcMin.window_ref}</Text></View>
                    <View style={styles.fieldRow}><Text style={styles.fieldLab}>Receipt Ref</Text><Text style={styles.fieldVal}>{pcMin.egress_receipt_ref || 'None'}</Text></View>
                </View>

                <View style={{ height: 40 }} />
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f4f6f8' },
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16, paddingTop: 40, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#ddd' },
    backButton: { paddingRight: 15 },
    backText: { fontSize: 16, color: '#007AFF' },
    headerTitle: { fontSize: 18, fontWeight: 'bold', color: '#333' },
    content: { flex: 1, padding: 15 },
    summaryBox: { backgroundColor: '#e8f5e9', padding: 16, borderRadius: 8, marginBottom: 20, borderWidth: 1, borderColor: '#c8e6c9' },
    summaryTitle: { fontSize: 16, fontWeight: 'bold', color: '#2e7d32', marginBottom: 4 },
    summaryDesc: { fontSize: 13, color: '#388e3c' },
    sectionHeader: { fontSize: 14, fontWeight: 'bold', color: '#37474f', marginBottom: 12, marginTop: 15 },
    metadataCard: { backgroundColor: '#fff', borderRadius: 8, padding: 12, borderWidth: 1, borderColor: '#eceff1' },
    fieldRow: { flexDirection: 'row', justifyContent: 'space-between', marginVertical: 4 },
    fieldLab: { fontSize: 13, color: '#546e7a', fontWeight: '500' },
    fieldVal: { fontSize: 11, color: '#263238', fontFamily: 'monospace', fontWeight: 'bold', maxWidth: '75%', textAlign: 'right' },
    unifiedCard: { backgroundColor: '#fff', borderRadius: 6, marginBottom: 8, padding: 12, borderLeftWidth: 5, elevation: 1, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 2, shadowOffset: { width: 0, height: 1 }, borderWidth: 1, borderColor: '#eceff1' },
    checkName: { fontWeight: 'bold', color: '#37474f' },
    reasonText: { fontSize: 11, color: '#c62828', marginTop: 4, fontStyle: 'italic' },
});
