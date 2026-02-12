import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Image, ScrollView, Dimensions } from 'react-native';
import { triggerOBH } from '../src/api';

export default function OneButtonHelper({ onBack }) {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [activeTab, setActiveTab] = useState('overview'); // 'overview', 'diagnostics', 'raw'

    // Font Scale State (Default 1.1 for bigger font as requested)
    const [fontScale, setFontScale] = useState(1.1);

    // Memoize styles to avoid flicker/re-calc
    const styles = useMemo(() => getStyles(fontScale), [fontScale]);

    const handlePress = async () => {
        setLoading(true);
        setResult(null);
        setActiveTab('overview'); // Reset to first tab on new path

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

    const handleFontChange = (delta) => {
        setFontScale(prev => {
            const newScale = prev + delta;
            // Clamp between 0.8 and 1.6
            return Math.min(Math.max(newScale, 0.8), 1.6);
        });
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

    // Helper for Status Badge
    const StatusBadge = ({ label, status }) => {
        const isPass = status === 'PASS' || status === 'READY';
        const color = isPass ? '#2e7d32' : '#c62828';
        const bgColor = isPass ? '#e8f5e9' : '#ffebee';
        return (
            <View style={{ backgroundColor: bgColor, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4, alignSelf: 'flex-start', borderWidth: 1, borderColor: color }}>
                <Text style={{ color: color, fontWeight: 'bold', fontSize: 12 * fontScale }}>{label}: {status}</Text>
            </View>
        );
    };

    const renderTabContent = (bundle) => {
        if (!bundle) return null;

        const v13Card = bundle.proof_card_v13;

        // --- LEGACY FALLBACK ---
        if (!v13Card) {
            // Check deep payload path first
            let refs = bundle.payload?.evidence_refs || bundle.evidence_refs;
            if (!refs) return <Text style={styles.noFailuresText}>No specific evidence refs found.</Text>;
            const failures = refs.filter(ref => !ref.includes('no_flags'));
            if (failures.length === 0) return <Text style={styles.noFailuresText}>No flagged evidence refs found.</Text>;
            return failures.map((ref, index) => (
                <Text key={index} style={styles.failureText}>• {ref}</Text>
            ));
        }

        // --- V1.3 DATA PREP ---
        const isReady = v13Card.verdict === 'READY';
        const verdictColor = isReady ? '#2e7d32' : '#c62828';
        const episodeStart = v13Card.episode_start ? new Date(v13Card.episode_start).toLocaleString() : 'N/A';
        const grade = v13Card.evidence_grade || 'UNKNOWN';
        const admission = v13Card.admission_verdict || '-';

        // Count health check failures
        const failedChecks = v13Card.health_checks ? v13Card.health_checks.filter(c => c.status !== 'PASS') : [];
        const passChecks = v13Card.health_checks ? v13Card.health_checks.filter(c => c.status === 'PASS') : [];
        const privacyVerdict = v13Card.privacy_check_verdict || 'N/A';

        // --- TAB 1: OVERVIEW ---
        if (activeTab === 'overview') {
            return (
                <View style={styles.tabContent}>
                    {/* PC-MIN Card */}
                    <View style={[styles.card, { borderTopColor: verdictColor, borderTopWidth: 4 }]}>
                        <Text style={styles.cardTitle}>Certificate Status</Text>
                        <View style={{ alignItems: 'center', marginVertical: 15 }}>
                            <Text style={styles.verdictText}>{v13Card.verdict}</Text>
                            <Text style={{ color: '#666', marginTop: 4, fontSize: 14 * fontScale }}>Episode: {episodeStart}</Text>
                            {/* [NEW] Data Range Display */}
                            {v13Card.data_range_start && v13Card.data_range_end && (
                                <Text style={{ color: '#555', marginTop: 2, fontSize: 12 * fontScale, fontStyle: 'italic' }}>
                                    Data Range: {new Date(v13Card.data_range_start).toLocaleTimeString()} - {new Date(v13Card.data_range_end).toLocaleTimeString()}
                                </Text>
                            )}
                        </View>

                        <View style={styles.gridRow}>
                            <View style={styles.gridItem}>
                                <Text style={styles.gridLabel}>EVIDENCE GRADE</Text>
                                <Text style={styles.gridValue}>{grade}</Text>
                            </View>
                            <View style={styles.gridDivider} />
                            <View style={styles.gridItem}>
                                <Text style={styles.gridLabel}>ADMISSION</Text>
                                <Text style={styles.gridValue}>{admission}</Text>
                            </View>
                        </View>
                    </View>

                    {/* System Summary */}
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>System Summary</Text>
                        <View style={{ marginTop: 10 }}>
                            {failedChecks.length > 0 ? (
                                <View style={[styles.alertBox, { backgroundColor: '#ffebee' }]}>
                                    <Text style={{ fontWeight: 'bold', color: '#c62828', fontSize: 16 * fontScale }}>⚠ {failedChecks.length} Issues Found</Text>
                                    <Text style={{ color: '#c62828', marginTop: 4, fontSize: 14 * fontScale }}>Check "Diagnostics" tab for details.</Text>
                                </View>
                            ) : (
                                <View style={[styles.alertBox, { backgroundColor: '#e8f5e9' }]}>
                                    <Text style={{ fontWeight: 'bold', color: '#2e7d32', fontSize: 16 * fontScale }}>✓ All Systems Go</Text>
                                    <Text style={{ color: '#2e7d32', marginTop: 4, fontSize: 14 * fontScale }}>No health check failures detected.</Text>
                                </View>
                            )}

                            <View style={{ marginTop: 15, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                                <Text style={{ fontSize: 14 * fontScale }}>Privacy Check:</Text>
                                <StatusBadge label="Verdict" status={privacyVerdict} />
                            </View>
                        </View>
                    </View>
                </View>
            );
        }

        // --- TAB 2: DIAGNOSTICS ---
        if (activeTab === 'diagnostics') {
            return (
                <View style={styles.tabContent}>
                    {/* Privacy Section */}
                    <Text style={styles.sectionHeader}>PRIVACY ANALYSIS</Text>
                    <View style={[styles.card, { backgroundColor: '#fff3e0' }]}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                            <Text style={{ fontWeight: 'bold', color: '#ef6c00', fontSize: 14 * fontScale }}>PC-PRIV (Restricted)</Text>
                            <Text style={{ fontWeight: 'bold', color: '#ef6c00', fontSize: 14 * fontScale }}>{privacyVerdict}</Text>
                        </View>
                        {v13Card.reason_code && v13Card.reason_code.length > 0 ? (
                            v13Card.reason_code.map((code, idx) => (
                                <Text key={idx} style={styles.failureText}>• {code}</Text>
                            ))
                        ) : (
                            <Text style={{ fontStyle: 'italic', color: '#aaa', fontSize: 14 * fontScale }}>No privacy reason codes.</Text>
                        )}
                    </View>

                    {/* Health Checks */}
                    <Text style={styles.sectionHeader}>HEALTH CHECKS ({v13Card.health_checks?.length || 0})</Text>

                    {/* Failed Checks First */}
                    {failedChecks.map((check, idx) => (
                        <View key={`fail-${idx}`} style={[styles.checkRow, styles.checkFail]}>
                            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                                <Text style={styles.checkName}>{check.name}</Text>
                                <Text style={styles.checkStatusFail}>✗ {check.status}</Text>
                            </View>
                            <View style={styles.checkDetails}>
                                <Text style={styles.monoText}>Threshold: {check.threshold}</Text>
                                <Text style={[styles.monoText, { fontWeight: 'bold' }]}>Actual: {check.actual}</Text>
                            </View>
                            {check.reason_code && <Text style={styles.reasonText}>Code: {check.reason_code}</Text>}
                        </View>
                    ))}

                    {/* API Checks */}
                    {passChecks.map((check, idx) => (
                        <View key={`pass-${idx}`} style={[styles.checkRow, styles.checkPass]}>
                            <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                                <Text style={styles.checkName}>{check.name}</Text>
                                <Text style={styles.checkStatusPass}>✓ {check.status}</Text>
                            </View>
                            <View style={styles.checkDetails}>
                                <Text style={styles.monoText}>Threshold: {check.threshold}</Text>
                                <Text style={styles.monoText}>Actual: {check.actual}</Text>
                            </View>
                        </View>
                    ))}
                </View>
            );
        }

        // --- TAB 3: RAW DATA ---
        if (activeTab === 'raw') {
            return (
                <View style={styles.tabContent}>
                    <Text style={styles.sectionHeader}>FROZEN EVIDENCE (PAYLOAD)</Text>

                    {/* P50 Metrics */}
                    <View style={styles.card}>
                        <Text style={[styles.cardTitle, { marginBottom: 10 }]}>Engineering Metrics (p50)</Text>
                        {v13Card.p50 && v13Card.p50.map((m, idx) => (
                            <View key={idx} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' }}>
                                <Text style={{ fontSize: 13 * fontScale, color: '#333', flex: 1 }}>{m.name}</Text>
                                <Text style={{ fontSize: 13 * fontScale, fontFamily: 'monospace', fontWeight: 'bold', color: '#212121' }}>{m.value}</Text>
                            </View>
                        ))}
                    </View>

                    {/* JSON Viewer */}
                    <Text style={styles.sectionHeader}>FULL JSON DUMP</Text>
                    <View style={styles.jsonContainer}>
                        <ScrollView nestedScrollEnabled={true}>
                            <Text style={styles.jsonText}>{JSON.stringify(v13Card, null, 2)}</Text>
                        </ScrollView>
                    </View>
                </View>
            );
        }
    };

    return (
        <View style={styles.container}>
            {/* 1. STICKY HEADER with Font Controls */}
            <View style={styles.header}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <TouchableOpacity onPress={onBack} style={styles.backButton}>
                        <Text style={styles.backText}>← Back</Text>
                    </TouchableOpacity>
                    <Text style={styles.title}>One Button Helper</Text>
                </View>

                {/* Font Size Controls */}
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

            {result ? (
                <View style={{ flex: 1, backgroundColor: '#f4f6f8' }}>
                    {/* Sticky Result Header */}
                    <View style={styles.resultHeader}>
                        <Text style={styles.pathText} numberOfLines={1}>{result.path}</Text>
                    </View>

                    {/* Tabs */}
                    <View style={styles.tabBar}>
                        {['Overview', 'Diagnostics', 'Raw Data'].map((tab) => {
                            const key = tab.toLowerCase().split(' ')[0]; // overview, diagnostics, raw
                            const isActive = activeTab === key;
                            return (
                                <TouchableOpacity
                                    key={key}
                                    style={[styles.tabItem, isActive && styles.tabItemActive]}
                                    onPress={() => setActiveTab(key)}
                                >
                                    <Text style={[styles.tabText, isActive && styles.tabTextActive]}>{tab}</Text>
                                </TouchableOpacity>
                            );
                        })}
                    </View>

                    {/* Content Area */}
                    <ScrollView style={{ flex: 1 }}>
                        {renderTabContent(result.bundle)}
                    </ScrollView>
                </View>
            ) : (
                // --- IDLE STATE ---
                // Keeping original "Big Button" UI for the idle state
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

                    {/* Error display for IDLE state */}
                    {result && result.error && (
                        <Text style={styles.errorText}>Error: {result.error}</Text>
                    )}
                </View>
            )}
        </View>
    );
}

// Dynamic Style Generator
const getStyles = (s) => StyleSheet.create({
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
        justifyContent: 'space-between', // Changed to space-between for font controls
        backgroundColor: '#fff'
    },
    backButton: { marginRight: 15 },
    backText: { fontSize: 16 * s, color: '#007AFF' },
    title: { fontSize: 20 * s, fontWeight: 'bold' },

    // Idle State Styles
    content: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        padding: 30,
    },
    guide: { fontSize: 16 * s, textAlign: 'center', color: '#555', marginBottom: 40, lineHeight: 28 }, // Increased line height
    bigButton: {
        width: 200, height: 200, borderRadius: 100, backgroundColor: '#FF3B30',
        alignItems: 'center', justifyContent: 'center',
        shadowColor: "#FF3B30", shadowOffset: { width: 0, height: 10 },
        shadowOpacity: 0.5, shadowRadius: 10, elevation: 20, marginBottom: 20, alignSelf: 'center'
    },
    bigButtonText: { color: '#FFF', fontSize: 32 * s, fontWeight: '900', letterSpacing: 2 },
    subtext: { color: '#999', fontSize: 14 * s, marginBottom: 40, textAlign: 'center' },
    errorText: { color: 'red', textAlign: 'center', fontSize: 14 * s },

    // Result View Styles
    resultHeader: { padding: 10, backgroundColor: '#eceff1', borderBottomWidth: 1, borderBottomColor: '#cfd8dc' },
    pathText: { fontSize: 10 * s, color: '#546e7a', fontFamily: 'monospace', textAlign: 'center' },

    // Tabs
    tabBar: { flexDirection: 'row', backgroundColor: '#fff', elevation: 2 },
    tabItem: { flex: 1, paddingVertical: 14, alignItems: 'center', borderBottomWidth: 3, borderBottomColor: 'transparent' },
    tabItemActive: { borderBottomColor: '#2196F3' },
    tabText: { fontSize: 14 * s, fontWeight: '600', color: '#757575' },
    tabTextActive: { color: '#2196F3' },

    // Tab Content common
    tabContent: { padding: 15 },
    card: { backgroundColor: '#fff', borderRadius: 8, padding: 15, marginBottom: 15, elevation: 1, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 5, shadowOffset: { width: 0, height: 2 } },
    cardTitle: { fontSize: 16 * s, fontWeight: 'bold', color: '#37474f' },

    // Verdict Special
    verdictText: { fontSize: 32 * s, fontWeight: '900', color: '#2e7d32', letterSpacing: 1, textAlign: 'center' },

    // Grid
    gridRow: { flexDirection: 'row', marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#eee' },
    gridItem: { flex: 1, alignItems: 'center' },
    gridDivider: { width: 1, backgroundColor: '#eee', height: '100%' },
    gridLabel: { fontSize: 10 * s, color: '#78909c', marginBottom: 4, fontWeight: 'bold' },
    gridValue: { fontSize: 16 * s, fontWeight: 'bold', color: '#263238' },

    // Alert Box
    alertBox: { padding: 12, borderRadius: 6, marginBottom: 10 },

    // Diagnostics
    sectionHeader: { fontSize: 12 * s, fontWeight: 'bold', color: '#78909c', marginBottom: 8, marginTop: 10, marginLeft: 4, letterSpacing: 1 },
    checkRow: { padding: 10, borderRadius: 6, marginBottom: 8, borderWidth: 1 },
    checkFail: { backgroundColor: '#ffebee', borderColor: '#ef9a9a' },
    checkPass: { backgroundColor: '#fff', borderColor: '#e0e0e0' },
    checkName: { fontSize: 14 * s, fontWeight: 'bold', color: '#37474f' },
    checkStatusPass: { color: '#2e7d32', fontWeight: 'bold', fontSize: 14 * s },
    checkStatusFail: { color: '#c62828', fontWeight: 'bold', fontSize: 14 * s },
    checkDetails: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
    monoText: { fontFamily: 'monospace', fontSize: 11 * s, color: '#546e7a' },
    reasonText: { fontSize: 11 * s, color: '#c62828', marginTop: 4, fontStyle: 'italic' },
    failureText: { fontSize: 12 * s, fontFamily: 'monospace', color: '#d32f2f', marginVertical: 2 },

    // Raw Data
    jsonContainer: { backgroundColor: '#263238', borderRadius: 8, padding: 10, height: 300 },
    jsonText: { color: '#c3e88d', fontFamily: 'monospace', fontSize: 11 * s },

    // Helpers
    noFailuresText: { fontStyle: 'italic', color: '#888', textAlign: 'center', padding: 20, fontSize: 12 * s },

    // Legacy support
    sectionContainer: { marginBottom: 8, backgroundColor: '#fafafa', borderRadius: 6, borderWidth: 1, borderColor: '#eee', overflow: 'hidden' },
    sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 10, backgroundColor: '#f1f1f1' },
    sectionTitle: { fontWeight: 'bold', fontSize: 14 * s, color: '#333' },
    sectionArrow: { fontSize: 14 * s, color: '#777' },
    sectionContent: { padding: 10 },
    zoneContainer: { borderRadius: 8, borderWidth: 1, padding: 10, marginBottom: 5 }
});
