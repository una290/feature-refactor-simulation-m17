import React, { useState, useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Image, ScrollView, Dimensions } from 'react-native';
import { triggerOBH } from '../src/api';

export default function OneButtonHelper({ onBack }) {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [activeTab, setActiveTab] = useState('pc-min'); // 'pc-min', 'pc-priv', 'raw'

    // Font Scale State (Default 1.1 for bigger font as requested)
    const [fontScale, setFontScale] = useState(1.1);

    // Memoize styles to avoid flicker/re-calc
    const styles = useMemo(() => getStyles(fontScale), [fontScale]);

    const handlePress = async () => {
        setLoading(true);
        setResult(null);
        setActiveTab('pc-min'); // Reset to first tab on new path

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

    // --- PC-MIN ACCORDION COMPONENTS ---

    const PC_MIN_METADATA = {
        // 1. Identity
        episode_id: { label: "Episode ID", desc: "Unique diagnostic event ID", logic: "M00: Auto-generated GUID" },
        window_ref: { label: "Window Ref", desc: "Time window slice ID", logic: "M01: Time-slotting logic" },
        data_range_start: { label: "Data Start", desc: "Sampling start time", logic: "Agg: Min timestamp" },
        data_range_end: { label: "Data End", desc: "Sampling end time", logic: "Agg: Max timestamp" },

        // 2. Verdicts
        primary_verdict: { label: "Primary Verdict", desc: "Main network health conclusion", logic: "M13: Profile Thresholds (P95/P50)" },
        admission_verdict: { label: "Admission", desc: "Gate admission decision", logic: "M22: Strict Mode + Privacy Check" },
        privacy_check_verdict: { label: "Privacy Check", desc: "Sensitive data detection", logic: "M22: PII/Context Analysis" },
        evidence_grade: { label: "Evidence Grade", desc: "Data completeness level", logic: "M13: Missing metrics check" },
    };

    const StatusBadge = ({ label, status, fontScale }) => {
        let color = '#757575';
        let bg = '#eee';

        const s = String(status).toUpperCase();
        if (s === 'PASS' || s === 'PRIVATE' || s === 'READY') {
            color = '#2e7d32'; bg = '#e8f5e9';
        } else if (s === 'FAIL' || s === 'PUBLIC' || s === 'STOP') {
            color = '#c62828'; bg = '#ffebee';
        } else if (s === 'WARN' || s === 'REVIEW') {
            color = '#ef6c00'; bg = '#fff3e0';
        }

        return (
            <View style={{ backgroundColor: bg, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 }}>
                <Text style={{ color: color, fontWeight: 'bold', fontSize: 12 * fontScale }}>{status}</Text>
            </View>
        );
    };

    const FieldItem = ({ label, value, fontScale }) => (
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text style={{ fontSize: 13 * fontScale, color: '#546e7a', fontWeight: '500' }}>{label}</Text>
            <Text style={{ fontSize: 13 * fontScale, color: '#263238', fontFamily: 'monospace', maxWidth: '60%', textAlign: 'right' }} numberOfLines={2}>
                {String(value !== undefined && value !== null ? value : '-')}
            </Text>
        </View>
    );

    const FieldGroup = ({ title, fields, data, fontScale }) => {
        const meta = PC_MIN_METADATA;
        return (
            <View style={{ marginBottom: 16, backgroundColor: '#fdfdfd', padding: 12, borderRadius: 6, borderWidth: 1, borderColor: '#eceff1' }}>
                <Text style={{ fontSize: 14 * fontScale, fontWeight: 'bold', color: '#37474f', marginBottom: 10, paddingBottom: 6, borderBottomWidth: 1, borderBottomColor: '#cfd8dc' }}>
                    {title}
                </Text>
                {fields.map(key => {
                    const m = meta[key] || {};
                    return (
                        <FieldItem
                            key={key}
                            label={m.label || key}
                            value={data[key]}
                            fontScale={fontScale}
                        />
                    );
                })}
            </View>
        );
    };

    const ProofCardMinView = ({ minCard, fontScale }) => {
        if (!minCard) return null;
        return (
            <View>
                <Text style={[styles.sectionHeader, { marginLeft: 0, marginTop: 20 }]}>TECHNICAL METADATA</Text>

                <FieldGroup
                    title="Identity & Context"
                    fields={['episode_id', 'window_ref', 'data_range_start', 'data_range_end']}
                    data={minCard}
                    fontScale={fontScale}
                />

                <FieldGroup
                    title="Governance Basis"
                    fields={['gate_ref', 'policy_snapshot_ref', 'byuse_context_ref']}
                    data={minCard}
                    fontScale={fontScale}
                />
            </View>
        );
    };

    const formatTimeNoLocale = (iso) => {
        if (!iso) return '-';
        const d = new Date(iso);
        const pad = (n) => n < 10 ? '0' + n : n;
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
    };

    const renderTabContent = (bundle) => {
        if (!bundle) return null;

        // Try to get pure PC-Min first (Proposal 2), else fallback to v13 (Proposal 1 Shim)
        const pcMin = bundle.proof_card_min || bundle.proof_card_v13;
        const v13Card = bundle.proof_card_v13; // Keep for legacy UI parts

        if (!pcMin) return <Text>No ProofCard Data Found</Text>;

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
        const isReady = v13Card.verdict === 'READY' || pcMin.primary_verdict === 'READY';
        const verdictColor = isReady ? '#2e7d32' : '#c62828';
        const episodeStart = (pcMin.data_range_start || v13Card.episode_start) ? formatTimeNoLocale(pcMin.data_range_start || v13Card.episode_start) : 'N/A';
        const grade = pcMin.evidence_grade || 'UNKNOWN';
        const admission = pcMin.admission_verdict || '-';
        const finalVerdict = pcMin.primary_verdict || v13Card.verdict;

        // Count health check failures
        const failedChecks = v13Card.health_checks ? v13Card.health_checks.filter(c => c.status !== 'PASS') : [];
        const passChecks = v13Card.health_checks ? v13Card.health_checks.filter(c => c.status === 'PASS') : [];
        const privacyVerdict = pcMin.privacy_check_verdict || 'N/A';

        // --- HELPER: UNIFIED CARD COMPONENT (Updated Logic with Themes) ---
        const UnifiedHealthCard = ({ title, status, details, subtext, fontScale, themeColor }) => {
            const s = String(status).toUpperCase();

            let color = '#757575';
            let icon = '?';

            // 1. Fail / Bad State (Always Red)
            if (['FAIL', 'NOT_READY', 'DENY', 'STOP', 'PUBLIC', 'NOT_CLOSURE_GRADE', 'INSUFFICIENT_EVIDENCE'].includes(s)) {
                color = '#c62828'; // Red
                icon = '✗';
            }
            // 2. Override Theme Color (For Specific Zones)
            else if (themeColor) {
                color = themeColor;
                icon = title === 'Data Range' ? '📅' : '✓';
            }
            // 3. Default Pass / Good State (Green)
            else if (['PASS', 'ALL SYSTEMS GO', 'ADMIT', 'READY', 'PRIVATE', 'DELIVERY_GRADE', 'VALID', 'OK', '7DAYS', '7 DAYS'].includes(s)) {
                color = '#2e7d32'; // Green
                icon = '✓';
            }
            // 4. Info / Neutral State (Blue)
            else {
                color = '#0288d1'; // Blue
                icon = 'ℹ';
            }

            return (
                <View style={[styles.unifiedCard, { borderLeftColor: color }]}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <View style={{ flex: 1 }}>
                            <Text style={styles.checkName}>{title}</Text>
                            {subtext ? <Text style={{ color: color, fontSize: 12 * fontScale, marginTop: 4 }}>{subtext}</Text> : null}
                        </View>
                        <Text style={{ color: color, fontWeight: 'bold', fontSize: 14 * fontScale }}>
                            {icon} {status}
                        </Text>
                    </View>

                    {/* DETAILS SECTION */}
                    {details && (
                        <View style={styles.checkDetails}>
                            <Text style={styles.monoText}>Threshold: {details.threshold}</Text>
                            <Text style={[styles.monoText, { fontWeight: 'bold' }]}>Actual: {details.actual}</Text>
                        </View>
                    )}

                    {/* REASON CODE */}
                    {details && details.reason_code && (
                        <Text style={styles.reasonText}>Code: {details.reason_code}</Text>
                    )}
                </View>
            );
        };

        // --- TAB 1: PC-MIN ---
        if (activeTab === 'pc-min') {
            return (
                <View style={styles.tabContent}>

                    {/* Unified Status Stack (Customized) */}
                    <View style={{ marginTop: 5 }}>

                        {/* 1. Health Check (Green) */}
                        <UnifiedHealthCard
                            title="Health Check"
                            status={finalVerdict}
                            subtext={failedChecks.length > 0 ? `${failedChecks.length} Issues Detected` : "All Checks Passed"}
                            fontScale={fontScale}
                        />

                        {/* 2. Governance Zone (Blue) */}
                        <UnifiedHealthCard
                            title="Privacy Check"
                            status={privacyVerdict}
                            subtext={privacyVerdict === 'PASS' ? "No PII Detected" : "Review Required"}
                            fontScale={fontScale}
                            themeColor="#2196F3"
                        />

                        <UnifiedHealthCard
                            title="Evidence Grade"
                            status={grade}
                            subtext="Data Integrity Level"
                            fontScale={fontScale}
                            themeColor="#2196F3"
                        />

                        <UnifiedHealthCard
                            title="Network Admission"
                            status={admission}
                            subtext="Gate Control Decision"
                            fontScale={fontScale}
                            themeColor="#2196F3"
                        />

                        {/* 3. Data Range Zone (Orange) */}
                        <UnifiedHealthCard
                            title="Data Range"
                            status={v13Card.validity_horizon_ref || "7 DAYS"}
                            subtext={pcMin.data_range_start && pcMin.data_range_end ?
                                `${formatTimeNoLocale(pcMin.data_range_start)} ... ${formatTimeNoLocale(pcMin.data_range_end).split(' ')[1]}` :
                                "No Range Data"}
                            fontScale={fontScale}
                            themeColor="#ff9800"
                        />
                    </View>

                    {/* [NEW] PC-MIN ACCORDION VIEW (PROPOSAL 3) */}
                    <ProofCardMinView minCard={pcMin} fontScale={fontScale} />

                </View>
            );
        }

        // --- TAB 2: PC-PRIV ---
        if (activeTab === 'pc-priv') {
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
                    <Text style={[styles.sectionHeader, { color: '#37474f', borderBottomColor: '#cfe8fc', borderBottomWidth: 2, paddingBottom: 4 }]}>Health Check Details ({v13Card.health_checks?.length || 0})</Text>

                    {/* Failed Checks First */}
                    {failedChecks.map((check, idx) => (
                        <UnifiedHealthCard
                            key={`fail-${idx}`}
                            title={check.name}
                            status={check.status} // FAIL
                            details={check} // Pass full check object for details
                            fontScale={fontScale}
                        />
                    ))}

                    {/* API Checks */}
                    {passChecks.map((check, idx) => (
                        <UnifiedHealthCard
                            key={`pass-${idx}`}
                            title={check.name}
                            status={check.status} // PASS
                            details={check}
                            fontScale={fontScale}
                        />
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
        <View style={styles.container} >
            {/* 1. STICKY HEADER with Font Controls */}
            < View style={styles.header} >
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <TouchableOpacity onPress={onBack} style={styles.backButton}>
                        <Text style={styles.backText}>← Back</Text>
                    </TouchableOpacity>
                    <Text style={styles.title}>One Button Helper</Text>
                </View>

                {/* Font Size Controls */}
                <View style={{ flexDirection: 'row', backgroundColor: '#f0f0f0', borderRadius: 8, padding: 2 }} >
                    <TouchableOpacity onPress={() => handleFontChange(-0.1)} style={{ paddingHorizontal: 10, paddingVertical: 4 }}>
                        <Text style={{ fontSize: 14, fontWeight: 'bold' }}>A-</Text>
                    </TouchableOpacity>
                    <View style={{ width: 1, backgroundColor: '#ddd', marginVertical: 4 }} />
                    <TouchableOpacity onPress={() => handleFontChange(0.1)} style={{ paddingHorizontal: 10, paddingVertical: 4 }}>
                        <Text style={{ fontSize: 18, fontWeight: 'bold' }}>A+</Text>
                    </TouchableOpacity>
                </View >
            </View >

            {
                result && !result.error ? (
                    <View style={{ flex: 1, backgroundColor: '#f4f6f8' }} >
                        {/* Sticky Result Header */}
                        < View style={styles.resultHeader} >
                            <Text style={styles.pathText} numberOfLines={1}>{result.path}</Text>
                        </View >

                        {/* Tabs */}
                        < View style={styles.tabBar} >
                            {
                                ['PC-min', 'PC-priv', 'Raw Data'].map((tab) => {
                                    const key = tab.toLowerCase().split(' ')[0]; // pc-min, pc-priv, raw
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
                                })
                            }
                        </View >

                        {/* Content Area */}
                        < ScrollView style={{ flex: 1 }
                        }>
                            {renderTabContent(result.bundle)}
                        </ScrollView >
                    </View >
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
        </View >
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

    // Alert Box (Deprecated visually, now used for general alerts if needed)
    alertBox: { padding: 12, borderRadius: 6, marginBottom: 10 },

    // Diagnostics
    sectionHeader: { fontSize: 16 * s, fontWeight: 'bold', color: '#37474f', marginBottom: 12, marginTop: 15, letterSpacing: 0.5 },

    // Unified Card Style (Left Stripe)
    unifiedCard: {
        backgroundColor: '#fff',
        borderRadius: 6,
        marginBottom: 8,
        padding: 12,
        borderLeftWidth: 5,
        elevation: 1,
        shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 2, shadowOffset: { width: 0, height: 1 },
        borderWidth: 1, borderColor: '#eceff1', borderLeftColor: 'transparent' // will be overridden
    },
    ucPass: { borderLeftColor: '#2e7d32' },
    ucFail: { borderLeftColor: '#c62828' },

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
    sectionTitle: { fontWeight: 'bold', fontSize: 14 * s, color: '#333' },
    sectionArrow: { fontSize: 14 * s, color: '#777' },
    sectionContent: { padding: 10 },
    zoneContainer: { borderRadius: 8, borderWidth: 1, padding: 10, marginBottom: 5 }
});
