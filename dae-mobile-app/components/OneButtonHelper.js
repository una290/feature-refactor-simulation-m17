import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
import { triggerOBH } from '../src/api';

export default function OneButtonHelper({ onBack }) {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [fontScale, setFontScale] = useState(1.1);

    const styles = useMemo(() => getStyles(fontScale), [fontScale]);

    const handlePress = async () => {
        setLoading(true);

        try {
            // "Customers" always trigger default context implicitly
            const data = await triggerOBH(null);
            if (!data) throw new Error("Failed to contact server.");
            setResult(data);
        } catch (err) {
            console.error(err);
            setResult({ error: "Connection Failed. Check IP Settings." });
        } finally {
            setLoading(false);
        }
    };

    const handleFontChange = (delta) => {
        setFontScale(prev => Math.min(Math.max(prev + delta, 0.8), 1.6));
    };

    const formatTimeNoLocale = (iso) => {
        if (!iso) return '-';
        const d = new Date(iso);
        const pad = (n) => n < 10 ? '0' + n : n;
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    };

    const UnifiedHealthCard = ({ title, status, details, subtext, fontScale, themeColor }) => {
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
                        <Text style={styles.checkName}>{title}</Text>
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

    const renderPcMinContent = (bundle) => {
        if (!bundle || !bundle.pc_min) return <Text style={{ padding: 20 }}>No ProofCard Data Found</Text>;
        const pcMin = bundle.pc_min;

        const isReady = pcMin.verdict === 'READY';
        const finalVerdict = pcMin.verdict || 'UNKNOWN';
        const grade = pcMin.evidence_grade || 'UNKNOWN';

        const hasPrivacyMissing = pcMin.missing_evidence_class && pcMin.missing_evidence_class.length > 0;
        const privacyVerdict = hasPrivacyMissing ? 'FAIL' : 'PASS';
        const privacySubtext = hasPrivacyMissing ? pcMin.missing_evidence_class.join(", ") : "All Privacy Requirements Met";

        return (
            <ScrollView style={{ flex: 1, padding: 15 }}>
                <View style={styles.successCard}>
                    <Text style={styles.successTitle}>✅ Sent Securely</Text>
                    <Text style={styles.successDesc}>Your diagnostic data has been packaged securely and sent to the support team.</Text>
                </View>

                <Text style={[styles.sectionHeader, { marginTop: 20 }]}>DIAGNOSTIC OVERVIEW (PC-Min)</Text>

                <UnifiedHealthCard
                    title="Network Diagnosis"
                    status={finalVerdict}
                    subtext={isReady ? "Connection is stable" : "Issues detected"}
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
                    subtext="For Context: default"
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

                <Text style={[styles.sectionHeader, { marginTop: 20 }]}>TECHNICAL METADATA</Text>
                <View style={styles.metadataCard}>
                    <View style={styles.fieldRow}><Text style={styles.fieldLab}>Episode ID</Text><Text style={styles.fieldVal}>{pcMin.episode_id}</Text></View>
                    <View style={styles.fieldRow}><Text style={styles.fieldLab}>Window Ref</Text><Text style={styles.fieldVal}>{pcMin.window_ref}</Text></View>
                    <View style={styles.fieldRow}><Text style={styles.fieldLab}>Receipt Ref</Text><Text style={styles.fieldVal}>{pcMin.egress_receipt_ref || 'None'}</Text></View>
                </View>
                <View style={{ height: 40 }} />
            </ScrollView>
        );
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <TouchableOpacity onPress={onBack} style={styles.backButton}>
                        <Text style={styles.backText}>← Back</Text>
                    </TouchableOpacity>
                    <Text style={styles.title}>Diagnostics & Help</Text>
                </View>
                <View style={{ flexDirection: 'row', backgroundColor: '#f0f0f0', borderRadius: 8, padding: 2 }}>
                    <TouchableOpacity onPress={() => handleFontChange(-0.1)} style={{ paddingHorizontal: 10, paddingVertical: 4 }}>
                        <Text style={{ fontSize: 14, fontWeight: 'bold' }}>A-</Text>
                    </TouchableOpacity>
                    <View style={{ width: 1, backgroundColor: '#ddd', marginVertical: 4 }} />
                    <TouchableOpacity onPress={() => handleFontChange(0.1)} style={{ paddingHorizontal: 10, paddingVertical: 4 }}>
                        <Text style={{ fontSize: 18, fontWeight: 'bold' }}>A+</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {result && !result.error ? (
                <View style={{ flex: 1, backgroundColor: '#f4f6f8' }}>
                    {renderPcMinContent(result.bundle)}
                </View>
            ) : (
                <View style={styles.content}>
                    <Text style={styles.guide}>
                        Experiencing an issue? Tap the button below to capture diagnostics and generate a secure support bundle instantly.
                    </Text>

                    <TouchableOpacity style={styles.bigButton} onPress={handlePress} disabled={loading}>
                        {loading ? <ActivityIndicator size="large" color="#FFF" /> : <Text style={styles.bigButtonText}>HELP</Text>}
                    </TouchableOpacity>
                    <Text style={styles.subtext}>
                        {loading ? "Capturing timeline & metrics..." : "Tap to capture diagnostic history"}
                    </Text>

                    {result && result.error && <Text style={styles.errorText}>Error: {result.error}</Text>}
                </View>
            )}
        </View>
    );
}

const getStyles = (s) => StyleSheet.create({
    container: { flex: 1, backgroundColor: '#fff' },
    header: { padding: 20, borderBottomWidth: 1, borderBottomColor: '#eee', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#fff' },
    backButton: { marginRight: 15 },
    backText: { fontSize: 16 * s, color: '#007AFF' },
    title: { fontSize: 20 * s, fontWeight: 'bold' },
    content: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30 },
    guide: { fontSize: 16 * s, textAlign: 'center', color: '#555', marginBottom: 40, lineHeight: 28 },
    bigButton: { width: 200, height: 200, borderRadius: 100, backgroundColor: '#FF3B30', alignItems: 'center', justifyContent: 'center', shadowColor: "#FF3B30", shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.5, shadowRadius: 10, elevation: 20, marginBottom: 20 },
    bigButtonText: { color: '#FFF', fontSize: 32 * s, fontWeight: '900', letterSpacing: 2 },
    subtext: { color: '#999', fontSize: 14 * s, marginBottom: 40, textAlign: 'center' },
    errorText: { color: 'red', textAlign: 'center', fontSize: 14 * s },

    successCard: { backgroundColor: '#e8f5e9', padding: 20, borderRadius: 12, alignItems: 'center', borderColor: '#c8e6c9', borderWidth: 1 },
    successTitle: { fontSize: 20 * s, fontWeight: 'bold', color: '#2e7d32', marginBottom: 8 },
    successDesc: { fontSize: 13 * s, color: '#2e7d32', textAlign: 'center' },

    sectionHeader: { fontSize: 14 * s, fontWeight: 'bold', color: '#37474f', marginBottom: 12, marginTop: 15 },
    unifiedCard: { backgroundColor: '#fff', borderRadius: 6, marginBottom: 8, padding: 12, borderLeftWidth: 5, elevation: 1, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 2, shadowOffset: { width: 0, height: 1 }, borderWidth: 1, borderColor: '#eceff1' },
    checkName: { fontSize: 14 * s, fontWeight: 'bold', color: '#37474f' },
    reasonText: { fontSize: 11 * s, color: '#c62828', marginTop: 4, fontStyle: 'italic' },

    metadataCard: { backgroundColor: '#fff', borderRadius: 8, padding: 12, borderWidth: 1, borderColor: '#eceff1' },
    fieldRow: { flexDirection: 'row', justifyContent: 'space-between', marginVertical: 4 },
    fieldLab: { fontSize: 13 * s, color: '#546e7a', fontWeight: '500' },
    fieldVal: { fontSize: 13 * s, color: '#263238', fontFamily: 'monospace', fontWeight: 'bold' },
});
