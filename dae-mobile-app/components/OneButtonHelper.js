import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Image, ScrollView } from 'react-native';
import { triggerOBH } from '../src/api';

export default function OneButtonHelper({ onBack }) {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handlePress = async () => {
        setLoading(true);
        setResult(null);

        try {
            const data = await triggerOBH();
            if (!data) {
                // API call failed completely (network error, etc)
                throw new Error("Failed to contact server.");
            }
            setResult(data);
        } catch (err) {
            console.error(err);
            setResult({ error: "Connection Failed. Check IP Settings." });
        } finally {
            setLoading(false);
        }
    };

    const ExpandableSection = ({ title, children, defaultExpanded = false }) => {
        const [expanded, setExpanded] = useState(defaultExpanded);
        return (
            <View style={styles.sectionContainer}>
                <TouchableOpacity style={styles.sectionHeader} onPress={() => setExpanded(!expanded)}>
                    <Text style={styles.sectionTitle}>{title}</Text>
                    <Text style={styles.sectionArrow}>{expanded ? '▼' : '▶'}</Text>
                </TouchableOpacity>
                {expanded && <View style={styles.sectionContent}>{children}</View>}
            </View>
        );
    };

    const renderEvidence = (bundle) => {
        if (!bundle) return null;

        // 1. Try to read V1.3 Proof Card (New Path: Root)
        const v13Card = bundle.proof_card_v13;
        if (v13Card) {
            const isReady = v13Card.verdict === 'READY';
            const verdictColor = isReady ? '#2e7d32' : '#c62828';
            const episodeStart = v13Card.episode_start ? new Date(v13Card.episode_start).toLocaleString() : 'N/A';
            const grade = v13Card.evidence_grade || 'UNKNOWN';

            return (
                <View>
                    {/* Header: PC-MIN (Public/Safe) - Low Saturation Green */}
                    <View style={[styles.zoneContainer, { backgroundColor: '#e8f5e9', borderColor: '#c8e6c9' }]}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                            <Text style={{ fontSize: 12, color: '#2e7d32', fontWeight: 'bold', letterSpacing: 0.5 }}>PC-MIN (PUBLIC)</Text>
                            <Text style={{ fontSize: 12, color: '#2e7d32', fontWeight: '600' }}>{episodeStart}</Text>
                        </View>
                        <Text style={{ fontWeight: '900', fontSize: 28, color: verdictColor, textAlign: 'center', marginVertical: 10, letterSpacing: 1 }}>
                            {v13Card.verdict}
                        </Text>

                        <View style={{ marginTop: 5, paddingTop: 10, borderTopWidth: 1, borderTopColor: 'rgba(0,0,0,0.05)' }}>
                            <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
                                <View style={{ alignItems: 'center' }}>
                                    <Text style={{ fontSize: 10, color: '#666', marginBottom: 2, textTransform: 'uppercase' }}>Evidence Grade</Text>
                                    <Text style={{ fontSize: 13, color: '#333', fontWeight: 'bold' }}>{grade}</Text>
                                </View>
                                <View style={{ width: 1, backgroundColor: '#ccc', height: '80%' }} />
                                <View style={{ alignItems: 'center' }}>
                                    <Text style={{ fontSize: 10, color: '#666', marginBottom: 2, textTransform: 'uppercase' }}>Admission</Text>
                                    <Text style={{ fontSize: 13, color: '#333', fontWeight: 'bold' }}>{v13Card.admission_verdict || '-'}</Text>
                                </View>
                            </View>
                        </View>
                    </View>

                    {/* Body: PC-PRIV (Sensitive/Locked) - Low Saturation Orange */}
                    <View style={[styles.zoneContainer, { backgroundColor: '#fff3e0', borderColor: '#ffe0b2', marginTop: 15 }]}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                            <Text style={{ fontSize: 12, color: '#e65100', fontWeight: 'bold', letterSpacing: 0.5 }}>PC-PRIV (RESTRICTED 🔒)</Text>
                        </View>

                        <ExpandableSection title="Reason Codes & Privacy" defaultExpanded={true}>
                            {v13Card.reason_code && v13Card.reason_code.length > 0 ? (
                                v13Card.reason_code.map((code, idx) => (
                                    <Text key={idx} style={styles.failureText}>• {code}</Text>
                                ))
                            ) : (
                                <Text style={styles.noFailuresText}>No failure codes found.</Text>
                            )}
                            <View style={{ height: 1, backgroundColor: '#ffe0b2', marginVertical: 12 }} />

                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Text style={styles.label}>Privacy Check:</Text>
                                <Text style={{ fontWeight: 'bold', color: '#e65100' }}>{v13Card.privacy_check_verdict || 'N/A'}</Text>
                            </View>
                        </ExpandableSection>

                        {/* [NEW] Detailed Health Checks */}
                        {v13Card.health_checks && v13Card.health_checks.length > 0 && (
                            <ExpandableSection title="Detailed Health Checks" defaultExpanded={true}>
                                {v13Card.health_checks.map((check, idx) => {
                                    const isPass = check.status === 'PASS';
                                    const color = isPass ? '#2e7d32' : '#c62828';
                                    const icon = isPass ? '✓' : '✗';

                                    return (
                                        <View key={idx} style={{
                                            marginBottom: 8,
                                            padding: 8,
                                            borderRadius: 6,
                                            backgroundColor: isPass ? '#f1f8e9' : '#ffebee',
                                            borderLeftWidth: 4,
                                            borderLeftColor: color
                                        }}>
                                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <Text style={{ fontWeight: 'bold', color: '#333', fontSize: 13 }}>{check.name}</Text>
                                                <Text style={{ fontWeight: '900', color: color }}>{icon} {check.status}</Text>
                                            </View>
                                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 }}>
                                                <Text style={{ fontSize: 11, color: '#666' }}>Threshold: <Text style={{ fontFamily: 'monospace' }}>{check.threshold}</Text></Text>
                                                <Text style={{ fontSize: 11, color: '#333', fontWeight: 'bold' }}>Actual: {check.actual}</Text>
                                            </View>
                                            {!isPass && check.reason_code && (
                                                <Text style={{ fontSize: 10, color: '#c62828', marginTop: 2, fontStyle: 'italic' }}>
                                                    Code: {check.reason_code}
                                                </Text>
                                            )}
                                        </View>
                                    );
                                })}
                            </ExpandableSection>
                        )}
                    </View>

                    {/* Footer: PAYLOAD (Frozen/Raw) - Low Saturation Blue/Grey */}
                    <View style={[styles.zoneContainer, { backgroundColor: '#f5f5f5', borderColor: '#e0e0e0', marginTop: 15 }]}>
                        <Text style={{ fontSize: 12, color: '#616161', fontWeight: 'bold', marginBottom: 8, letterSpacing: 0.5 }}>FROZEN EVIDENCE (PAYLOAD)</Text>

                        <ExpandableSection title="Engineering Metrics (p50)">
                            {v13Card.p50 && v13Card.p50.map((m, idx) => (
                                <View key={idx} style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6, borderBottomWidth: 1, borderBottomColor: '#e0e0e0', paddingBottom: 4 }}>
                                    <Text style={{ fontSize: 13, color: '#424242', flex: 1 }}>{m.name}</Text>
                                    <Text style={{ fontSize: 13, fontFamily: 'monospace', fontWeight: 'bold', color: '#212121' }}>{m.value}</Text>
                                </View>
                            ))}
                        </ExpandableSection>

                        <ExpandableSection title="Raw Data (JSON)">
                            <ScrollView style={{ maxHeight: 200 }} nestedScrollEnabled={true}>
                                <Text style={{ fontFamily: 'monospace', fontSize: 11, color: '#333' }}>
                                    {JSON.stringify(v13Card, null, 2)}
                                </Text>
                            </ScrollView>
                        </ExpandableSection>
                    </View>
                </View>
            );
        }

        // 2. Legacy Fallback (Old Path or just evidence_refs)
        // Check deep payload path first
        let refs = bundle.payload?.evidence_refs || bundle.evidence_refs;

        if (!refs) return <Text style={styles.noFailuresText}>No specific evidence refs found.</Text>;

        // Filter out "no_flags"
        const failures = refs.filter(ref => !ref.includes('no_flags'));

        if (failures.length === 0) {
            return <Text style={styles.noFailuresText}>No flagged evidence refs found.</Text>;
        }

        return failures.map((ref, index) => (
            <Text key={index} style={styles.failureText}>• {ref}</Text>
        ));
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.title}>One Button Helper</Text>
            </View>

            <View style={styles.content}>
                <Text style={styles.guide}>
                    Experiencing an issue? Tap the button below to capture diagnostics and generate a support bundle instantly.
                </Text>

                <TouchableOpacity
                    style={styles.bigButton}
                    onPress={handlePress}
                    disabled={loading}
                >
                    {loading ? (
                        <ActivityIndicator size="large" color="#FFF" />
                    ) : (
                        <Text style={styles.bigButtonText}>HELP</Text>
                    )}
                </TouchableOpacity>

                <Text style={styles.subtext}>
                    {loading ? "Capturing timeline & metrics..." : "Tap to capture 7-day history"}
                </Text>

                {result && (
                    <ScrollView style={styles.resultBox} contentContainerStyle={{ paddingBottom: 20 }}>
                        {result.error ? (
                            <Text style={styles.errorText}>Error: {result.error}</Text>
                        ) : (
                            <>
                                <Text style={styles.successTitle}>✓ Bundle Exported!</Text>
                                {/* <Text style={styles.label}>Episode ID:</Text>
                                <Text style={styles.value}>{result.episode_id}</Text> */}
                                <Text style={styles.label}>Location:</Text>
                                <Text style={styles.value}>{result.path}</Text>

                                <Text style={[styles.label, { marginTop: 15, marginBottom: 5 }]}>Failure Evidence:</Text>
                                <View style={styles.jsonBox}>
                                    {renderEvidence(result.bundle)}
                                </View>
                            </>
                        )}
                    </ScrollView>
                )}
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
    },
    header: {
        padding: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
        flexDirection: 'row',
        alignItems: 'center',
    },
    backButton: {
        marginRight: 15,
    },
    backText: {
        fontSize: 16,
        color: '#007AFF',
    },
    title: {
        fontSize: 20,
        fontWeight: 'bold',
    },
    content: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        padding: 30,
    },
    guide: {
        fontSize: 16,
        textAlign: 'center',
        color: '#555',
        marginBottom: 40,
        lineHeight: 24,
    },
    bigButton: {
        width: 200,
        height: 200,
        borderRadius: 100,
        backgroundColor: '#FF3B30',
        alignItems: 'center',
        justifyContent: 'center',
        shadowColor: "#FF3B30",
        shadowOffset: {
            width: 0,
            height: 10,
        },
        shadowOpacity: 0.5,
        shadowRadius: 10,
        elevation: 20,
        marginBottom: 20,
        alignSelf: 'center'
    },
    bigButtonText: {
        color: '#FFF',
        fontSize: 32,
        fontWeight: '900',
        letterSpacing: 2,
    },
    subtext: {
        color: '#999',
        fontSize: 14,
        marginBottom: 40,
        textAlign: 'center'
    },
    resultBox: {
        flex: 1,
        width: '100%',
        backgroundColor: '#F0F9F0',
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#C8E6C9',
        padding: 15,
    },
    successTitle: {
        color: '#2E7D32',
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 10,
        textAlign: 'center',
    },
    label: {
        fontSize: 12,
        color: '#666',
        marginTop: 5,
    },
    value: {
        fontSize: 14,
        color: '#333',
        fontWeight: 'bold',
    },
    errorText: {
        color: 'red',
        textAlign: 'center'
    },
    jsonBox: {
        marginTop: 5,
        backgroundColor: '#fff',
        padding: 10,
        borderRadius: 5,
        borderWidth: 1,
        borderColor: '#eee',
    },
    failureText: {
        fontSize: 12,
        fontFamily: 'monospace',
        color: '#D32F2F',
        marginBottom: 2,
        fontWeight: 'bold'
    },
    noFailuresText: {
        fontSize: 12,
        fontStyle: 'italic',
        color: '#888'
    },
    // New Styles
    sectionContainer: {
        marginBottom: 8,
        backgroundColor: '#fafafa',
        borderRadius: 6,
        borderWidth: 1,
        borderColor: '#eee',
        overflow: 'hidden'
    },
    sectionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 10,
        backgroundColor: '#f1f1f1'
    },
    sectionTitle: {
        fontWeight: 'bold',
        fontSize: 14,
        color: '#333'
    },
    sectionArrow: {
        fontSize: 14,
        color: '#777'
    },
    sectionContent: {
        padding: 10
    },
    zoneContainer: {
        borderRadius: 8,
        borderWidth: 1,
        padding: 10,
        marginBottom: 5
    }
});
