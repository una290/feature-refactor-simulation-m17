import React, { useState, useMemo, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView, TextInput } from 'react-native';

// Standalone API Client for CSR Dashboard
const csrFetchOBHBundle = async (ip, episodeId, context = null) => {
    let url = `${ip}/obh/proofcard/${encodeURIComponent(episodeId)}`;
    if (context) url += `?context=${encodeURIComponent(context)}`;
    const response = await fetch(url);
    return await response.json();
};

const csrRequestConsent = async (ip, episodeId, csrId = "8871") => {
    const response = await fetch(`${ip}/api/obh/consent/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ episode_id: episodeId, csr_id: csrId })
    });
    return await response.json();
};

export default function CsrDashboard({ onBack }) {
    const [ipAddress, setIpAddress] = useState('');
    const [connectedIp, setConnectedIp] = useState(null);
    const [isConnecting, setIsConnecting] = useState(false);
    const [ipError, setIpError] = useState(null);

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [activeTab, setActiveTab] = useState('pc-min'); // 'pc-min', 'pc-priv', 'raw'
    const [reportContext, setReportContext] = useState('default'); // 'default', 'dispute'
    const [searchQuery, setSearchQuery] = useState('');
    const [fontScale, setFontScale] = useState(1.0);
    const [pendingAuth, setPendingAuth] = useState(false);

    const styles = useMemo(() => getStyles(fontScale), [fontScale]);

    const handleConnect = async () => {
        if (!ipAddress) return;
        setIsConnecting(true);
        setIpError(null);

        let cleanIp = ipAddress.trim();
        if (!cleanIp.startsWith('http://') && !cleanIp.startsWith('https://')) {
            cleanIp = 'http://' + cleanIp;
        }
        if (cleanIp.endsWith('/')) {
            cleanIp = cleanIp.slice(0, -1);
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            const response = await fetch(`${cleanIp}/`, { method: 'GET', signal: controller.signal });
            clearTimeout(timeoutId);
            // Even a 404 means the server is reachable and responding
            if (response.ok || response.status === 404) {
                setConnectedIp(cleanIp);
            } else {
                throw new Error(`Server block (${response.status})`);
            }
        } catch (e) {
            let msg = e.message || 'Timeout or Network Error';
            if (e.name === 'AbortError') msg = 'Connection Timed Out';
            setIpError(`Failed: ${msg}`);
            setConnectedIp(null);
        } finally {
            setIsConnecting(false);
        }
    };

    const handleSearch = async (context = reportContext, isPolling = false) => {
        if (!searchQuery || !connectedIp) return;
        if (!isPolling) {
            setLoading(true);
            setActiveTab('pc-min');
        }

        try {
            const apiContext = context === 'default' ? null : context;
            const data = await csrFetchOBHBundle(connectedIp, searchQuery.trim(), apiContext);
            if (!data || data.error) throw new Error(data?.error || "Failed to contact server.");
            setResult(data);

            // If we were polling and the grade is now DELIVERY_GRADE, stop polling
            if (isPolling && data.bundle?.pc_min?.evidence_grade !== 'NOT_CLOSURE_GRADE') {
                setPendingAuth(false);
                setActiveTab('pc-priv'); // Auto-switch to priv tab when unlocked
            }
        } catch (err) {
            console.error(err);
            if (!isPolling) setResult({ error: err.message || "Retrieval Failed." });
        } finally {
            if (!isPolling) setLoading(false);
        }
    };

    const handleAuthRequest = async () => {
        if (!result?.bundle?.pc_min?.episode_id || !connectedIp) return;
        setPendingAuth(true);
        await csrRequestConsent(connectedIp, result.bundle.pc_min.episode_id);
    };

    // Polling hook
    useEffect(() => {
        let interval;
        if (pendingAuth) {
            interval = setInterval(() => {
                handleSearch(reportContext, true);
            }, 1000); // 縮短為每 1 秒輪詢一次
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [pendingAuth, reportContext, searchQuery, connectedIp]);

    const handleContextChange = (newContext) => {
        setReportContext(newContext);
        if (result && !result.error) {
            // reset auth state on context change
            setPendingAuth(false);
            handleSearch(newContext);
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

    const renderTabContent = (bundle) => {
        if (!bundle) return null;

        const pcMin = bundle.pc_min;
        const pcPriv = bundle.pc_priv;

        if (!pcMin) return <Text style={{ padding: 20 }}>No ProofCard Data Found</Text>;

        const isReady = pcMin.status === 'READY' || pcMin.verdict === 'READY';
        const finalStatus = pcMin.status || pcMin.verdict || 'UNKNOWN';
        const diagnosisCode = pcMin.diagnosis_code || 'UNKNOWN';
        const grade = pcMin.evidence_grade || 'UNKNOWN';

        const hasPrivacyMissing = pcMin.missing_evidence_class && pcMin.missing_evidence_class.length > 0;
        const privacyVerdict = hasPrivacyMissing ? 'FAIL' : 'PASS';
        const privacySubtext = hasPrivacyMissing ? pcMin.missing_evidence_class.join(", ") : "All Privacy Requirements Met";

        if (activeTab === 'pc-min') {
            return (
                <View style={styles.tabContent}>
                    {/* [NEW] COMPLIANCE WIZARD BLOCKER CARD */}
                    {grade === 'NOT_CLOSURE_GRADE' && (
                        <View style={styles.blockerCard}>
                            <Text style={styles.blockerTitle}>🛑 Cannot Close Ticket (NOT_CLOSURE_GRADE)</Text>
                            <Text style={styles.blockerText}>This diagnostic data is being used for "{reportContext}".</Text>
                            <Text style={styles.blockerText}>The current evidence lacks required permissions for this use case.</Text>
                            <View style={styles.blockerActionBox}>
                                <Text style={styles.blockerActionLabel}>Required to Proceed:</Text>
                                <Text style={styles.blockerActionReq}>📝 {pcMin.upgrade_requirements_ref}</Text>
                                <TouchableOpacity
                                    style={[styles.blockerBtn, pendingAuth && { backgroundColor: '#ffb300', borderColor: '#ff6f00', borderWidth: 1 }]}
                                    onPress={handleAuthRequest}
                                    disabled={pendingAuth}
                                >
                                    <Text style={[styles.blockerBtnText, pendingAuth && { color: '#3e2723' }]}>
                                        {pendingAuth ? "⏳ Waiting for customer approval to unlock payload..." : "👉 Send Authorization Request to User"}
                                    </Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    )}

                    <View style={{ marginTop: 5 }}>
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
                            subtext={`For Context: ${reportContext}`}
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
                    </View>

                    <Text style={[styles.sectionHeader, { marginTop: 20 }]}>TECHNICAL METADATA (Public)</Text>
                    <View style={styles.metadataCard}>
                        <View style={styles.fieldRow}><Text style={styles.fieldLab}>Episode ID</Text><Text style={styles.fieldVal}>{pcMin.episode_id}</Text></View>
                        <View style={styles.fieldRow}><Text style={styles.fieldLab}>Window Ref</Text><Text style={styles.fieldVal}>{pcMin.window_ref}</Text></View>
                        <View style={styles.fieldRow}><Text style={styles.fieldLab}>Receipt Ref</Text><Text style={styles.fieldVal}>{pcMin.egress_receipt_ref || 'None'}</Text></View>
                    </View>
                </View>
            );
        }

        if (activeTab === 'pc-priv' || activeTab === 'raw') {
            if (!pcPriv) {
                return (
                    <View style={styles.tabContent}>
                        <View style={styles.unauthCard}>
                            <Text style={styles.unauthTitle}>⛔ Privacy Redaction Enabled</Text>
                            <Text style={styles.unauthText}>You do not have the required authority scope to view the sensitive payload data for this ProofCard.</Text>
                            <Text style={styles.unauthText}>Only PC-Min metadata is available.</Text>
                        </View>
                    </View>
                );
            }

            if (activeTab === 'pc-priv') {
                const obs = bundle.pc_priv.observability || {};
                const obsStatus = obs.observability_status || obs.status || 'UNKNOWN';
                const isDegraded = obs.opaque_risk || obs.is_degraded || false;
                const missingRefs = obs.missing_refs || [];
                const originHint = obs.origin_hint || 'unknown';

                const isSufficient = obsStatus === 'SUFFICIENT';
                const actionColor = isSufficient ? '#e8f5e9' : '#fff3e0';
                const actionBorder = isSufficient ? '#c8e6c9' : '#ffe0b2';
                const actionTextColor = isSufficient ? '#2e7d32' : '#e65100';
                const actionTitle = isSufficient ? '💡 Analysis Confidence: HIGH' : '⚠️ Analysis Confidence: DEGRADED';
                const actionDesc = isSufficient
                    ? 'Diagnosis context is fully mapped and reliable. No opaque risks detected. Proceed with the standard automated resolution steps.'
                    : 'Diagnosis has opaque risks due to missing context. DO NOT blindly apply automated steps. Please ask customer to restart the router to gather a fresh diagnosis trace.';

                return (
                    <View style={styles.tabContent}>
                        <Text style={styles.sectionHeader}>PRIVACY REFERENCES (Internal Refs)</Text>
                        <View style={styles.metadataCard}>
                            {bundle.pc_priv.evidence_refs && bundle.pc_priv.evidence_refs.map((ref, idx) => (
                                <Text key={idx} style={styles.monoText}>• {ref}</Text>
                            ))}
                            {(!bundle.pc_priv.evidence_refs || bundle.pc_priv.evidence_refs.length === 0) && (
                                <Text style={styles.monoText}>No internal refs found.</Text>
                            )}
                        </View>

                        <Text style={styles.sectionHeader}>CONTEXT AUDIT (OBSERVABILITY)</Text>

                        {/* Agent Action Guide (Proposal 3) */}
                        <View style={{ backgroundColor: actionColor, padding: 15, borderRadius: 8, marginBottom: 15, borderWidth: 1, borderColor: actionBorder }}>
                            <Text style={{ fontWeight: 'bold', fontSize: 16 * fontScale, color: actionTextColor, marginBottom: 8 }}>
                                {actionTitle}
                            </Text>
                            <Text style={{ fontSize: 14 * fontScale, color: actionTextColor, lineHeight: 20 }}>
                                {actionDesc}
                            </Text>
                        </View>

                        {/* Checklist & Radar (Proposal 2) */}
                        <View style={styles.metadataCard}>
                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10, borderBottomWidth: 1, borderBottomColor: '#eee', paddingBottom: 10 }}>
                                <Text style={{ fontWeight: 'bold', color: '#555', fontSize: 14 * fontScale }}>System Audit Status</Text>
                                <Text style={{ fontWeight: 'bold', color: actionTextColor, fontSize: 14 * fontScale }}>
                                    {isSufficient ? '🟢 SUFFICIENT' : '🟠 INSUFFICIENT'}
                                </Text>
                            </View>

                            <View style={{ marginBottom: 5 }}>
                                <Text style={{ fontSize: 13 * fontScale, color: '#333', marginBottom: 6 }}>
                                    {(!isSufficient && missingRefs.includes('origin_hint')) ? '❌ Event Origin (Trace missing)' : '✅ Event Origin (Trace captured)'}
                                </Text>
                                <Text style={{ fontSize: 13 * fontScale, color: '#333', marginBottom: 6 }}>
                                    {(!isSufficient && missingRefs.includes('change_ref')) ? '❌ Change Refs (System logs missing)' : '✅ Change Refs (System logs audited)'}
                                </Text>
                                <Text style={{ fontSize: 13 * fontScale, color: '#333', marginBottom: 6 }}>
                                    {(!isSufficient && missingRefs.includes('version_refs')) ? '❌ Version Info (Firmware mismatch risk)' : '✅ Version Info (Firmware verified)'}
                                </Text>
                            </View>

                            {isDegraded && (
                                <Text style={{ fontSize: 12 * fontScale, color: '#e65100', marginTop: 10, fontStyle: 'italic' }}>
                                    ↳ Warning: Opaque risk detected. Missing context mapped to: {missingRefs.join(', ') || 'Unknown'}
                                </Text>
                            )}
                        </View>
                    </View>
                );
            }

            if (activeTab === 'raw') {
                const fullJsonStr = JSON.stringify(pcPriv, null, 2);
                const isMassive = fullJsonStr.length > 3000;

                return (
                    <View style={styles.tabContent}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                            <Text style={[styles.sectionHeader, { marginBottom: 0, marginTop: 0 }]}>FROZEN PAYLOAD</Text>
                            {pcMin.egress_receipt_ref && (
                                <View style={styles.receiptBadge}><Text style={styles.receiptText}>👁️ Receipt: {pcMin.egress_receipt_ref.split('-')[2]}</Text></View>
                            )}
                        </View>
                        <Text style={{ fontSize: 12 * fontScale, color: '#ff9800', marginBottom: 5 }}>
                            ⚠️ Raw payload includes heavy timeline data.
                        </Text>
                        <View style={styles.jsonContainer}>
                            <ScrollView nestedScrollEnabled={true}>
                                <Text style={styles.jsonText}>
                                    {isMassive && !result.showFullJson
                                        ? fullJsonStr.substring(0, 3000) + '\n\n... [TRUNCATED FOR UI PERFORMANCE] ...\n'
                                        : fullJsonStr}
                                </Text>
                                {isMassive && !result.showFullJson && (
                                    <TouchableOpacity
                                        style={{ padding: 10, backgroundColor: 'rgba(255,255,255,0.1)', marginTop: 10, borderRadius: 5, alignItems: 'center' }}
                                        onPress={() => setResult({ ...result, showFullJson: true })}
                                    >
                                        <Text style={{ color: '#81c784', fontWeight: 'bold' }}>Load Full JSON (May lag for a few seconds)</Text>
                                    </TouchableOpacity>
                                )}
                            </ScrollView>
                        </View>
                    </View>
                );
            }
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <TouchableOpacity onPress={onBack} style={styles.backButton}>
                        <Text style={styles.backText}>← Back</Text>
                    </TouchableOpacity>
                    <View>
                        <Text style={styles.title}>CSR App Console</Text>
                        <Text style={styles.subtitle}>Telco Agent Access View</Text>
                    </View>
                </View>
                <View style={{ flexDirection: 'row', backgroundColor: '#333', borderRadius: 8, padding: 2 }}>
                    <TouchableOpacity onPress={() => handleFontChange(-0.1)} style={{ paddingHorizontal: 10, paddingVertical: 4 }}>
                        <Text style={{ fontSize: 14, fontWeight: 'bold', color: '#fff' }}>A-</Text>
                    </TouchableOpacity>
                    <View style={{ width: 1, backgroundColor: '#555', marginVertical: 4 }} />
                    <TouchableOpacity onPress={() => handleFontChange(0.1)} style={{ paddingHorizontal: 10, paddingVertical: 4 }}>
                        <Text style={{ fontSize: 18, fontWeight: 'bold', color: '#fff' }}>A+</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {result && !result.error ? (
                <View style={{ flex: 1, backgroundColor: '#f4f6f8' }}>

                    {/* Context Selector Workflow */}
                    <View style={styles.contextBar}>
                        <Text style={styles.contextLabel}>Report Context (BYUSE):</Text>
                        <View style={styles.contextBtns}>
                            <TouchableOpacity
                                style={[styles.ctxBtn, reportContext === 'default' && styles.ctxBtnActive]}
                                onPress={() => handleContextChange('default')}
                                disabled={loading}
                            >
                                <Text style={[styles.ctxBtnTxt, reportContext === 'default' && styles.ctxBtnTxtActive]}>Routine Check</Text>
                            </TouchableOpacity>
                            <TouchableOpacity
                                style={[styles.ctxBtn, reportContext === 'dispute' && styles.ctxBtnActive, { borderLeftWidth: 1, borderColor: '#ccc' }]}
                                onPress={() => handleContextChange('dispute')}
                                disabled={loading}
                            >
                                <Text style={[styles.ctxBtnTxt, reportContext === 'dispute' && styles.ctxBtnTxtActive]}>Dispute/Closure</Text>
                            </TouchableOpacity>
                        </View>
                    </View>

                    <View style={styles.tabBar}>
                        {['PC-Min (Overview)', 'PC-Priv (Details)', 'Raw Data']
                            .filter(tab => reportContext === 'default' ? tab.startsWith('PC-Min') : true)
                            .map((tab) => {
                                const key = tab.toLowerCase().split(' ')[0]; // pc-min, pc-priv, raw
                                const isActive = activeTab === key;
                                return (
                                    <TouchableOpacity key={key} style={[styles.tabItem, isActive && styles.tabItemActive]} onPress={() => setActiveTab(key)}>
                                        <Text style={[styles.tabText, isActive && styles.tabTextActive]}>{tab.split(' ')[0]}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                    </View>

                    {loading ? (
                        <ActivityIndicator size="large" color="#2196F3" style={{ marginTop: 50 }} />
                    ) : (
                        <ScrollView style={{ flex: 1 }}>
                            {renderTabContent(result.bundle)}
                        </ScrollView>
                    )}
                </View>
            ) : (
                <View style={[styles.content, { justifyContent: 'flex-start', paddingTop: 60 }]}>
                    <Text style={styles.guide}>
                        Assume the identity of a Customer Support Representative resolving an issue with a customer's device.
                    </Text>

                    {/* Step 1: Connect to Device IP */}
                    <View style={styles.searchContainer}>
                        <Text style={styles.searchLabel}>Step 1: Connect to Device IP</Text>
                        <TextInput
                            style={[styles.searchInput, { marginBottom: 10 }]}
                            placeholder="e.g. 192.168.1.100:8000"
                            value={ipAddress}
                            onChangeText={(text) => { setIpAddress(text); setConnectedIp(null); setIpError(null); }}
                            autoCorrect={false}
                            autoCapitalize="none"
                        />
                        <TouchableOpacity
                            style={[styles.idleContextBtn, { padding: 12, marginBottom: 10 }, isConnecting && { opacity: 0.7 }]}
                            onPress={handleConnect}
                            disabled={isConnecting}
                        >
                            {isConnecting ? (
                                <ActivityIndicator color="#1565c0" />
                            ) : (
                                <Text style={[styles.idleContextBtnTitle, { fontSize: 16, marginBottom: 0 }]}>{connectedIp ? '✓ Connected' : 'Connect'}</Text>
                            )}
                        </TouchableOpacity>
                        {ipError && <Text style={{ color: 'red', textAlign: 'center', marginBottom: 10 }}>{ipError}</Text>}
                        {connectedIp && <Text style={{ color: '#2e7d32', textAlign: 'center', fontWeight: 'bold', marginBottom: 10 }}>Connected to {connectedIp}</Text>}
                    </View>

                    {/* Step 2: Retrieve Diagnostic Session */}
                    <View style={[styles.searchContainer, !connectedIp && { opacity: 0.3 }]} pointerEvents={connectedIp ? 'auto' : 'none'}>
                        <Text style={styles.searchLabel}>Step 2: Retrieve Diagnostic Session</Text>
                        <TextInput
                            style={styles.searchInput}
                            placeholder="Enter Episode ID (e.g. 550e8400...)"
                            value={searchQuery}
                            onChangeText={setSearchQuery}
                            autoCorrect={false}
                            autoCapitalize="none"
                        />
                        <View style={styles.idleContextContainer}>
                            <TouchableOpacity
                                style={[styles.idleContextBtn, !searchQuery && { opacity: 0.5 }]}
                                onPress={() => { setReportContext('default'); handleSearch('default'); }}
                                disabled={loading || !searchQuery}
                            >
                                <Text style={styles.idleContextBtnTitle}>Perform Routine Check</Text>
                                <Text style={styles.idleContextBtnDesc}>Standard diagnostics with default privacy</Text>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={[styles.idleContextBtn, { marginTop: 15 }, !searchQuery && { opacity: 0.5 }]}
                                onPress={() => { setReportContext('dispute'); handleSearch('dispute'); }}
                                disabled={loading || !searchQuery}
                            >
                                <Text style={styles.idleContextBtnTitle}>Escalate to Dispute/Closure</Text>
                                <Text style={styles.idleContextBtnDesc}>Strict mode requiring signed manifest for legal cases</Text>
                            </TouchableOpacity>
                        </View>
                    </View>

                    {loading && <ActivityIndicator size="large" color="#1565c0" style={{ marginTop: 30 }} />}
                    {result && result.error && <Text style={styles.errorText}>Error: {result.error}</Text>}
                </View>
            )}
        </View>
    );
}

const getStyles = (s) => StyleSheet.create({
    container: { flex: 1, backgroundColor: '#1e1e1e' },
    header: { padding: 20, borderBottomWidth: 1, borderBottomColor: '#333', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#1e1e1e' },
    backButton: { marginRight: 15 },
    backText: { fontSize: 16 * s, color: '#4fc3f7' },
    title: { fontSize: 20 * s, fontWeight: 'bold', color: '#fff' },
    subtitle: { fontSize: 12 * s, color: '#aaa', marginTop: 2 },
    content: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 30, backgroundColor: '#f4f6f8' },
    guide: { fontSize: 16 * s, textAlign: 'center', color: '#555', marginBottom: 40, lineHeight: 28 },

    idleContextContainer: { width: '100%', paddingHorizontal: 10, maxWidth: 400, alignSelf: 'center' },
    idleContextBtn: { backgroundColor: '#e3f2fd', padding: 20, borderRadius: 12, borderWidth: 2, borderColor: '#1565c0', alignItems: 'center', shadowColor: "#000", shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.1, shadowRadius: 6, elevation: 4 },
    idleContextBtnTitle: { color: '#1565c0', fontSize: 18 * s, fontWeight: 'bold', marginBottom: 5 },
    idleContextBtnDesc: { color: '#546e7a', fontSize: 12 * s, textAlign: 'center' },

    searchContainer: { width: '100%', maxWidth: 400, alignSelf: 'center', marginBottom: 20 },
    searchLabel: { fontSize: 14 * s, fontWeight: 'bold', color: '#37474f', marginBottom: 8, textTransform: 'uppercase' },
    searchInput: { backgroundColor: '#fff', borderWidth: 2, borderColor: '#eceff1', borderRadius: 8, padding: 15, fontSize: 16 * s, color: '#000', marginBottom: 20, fontFamily: 'monospace' },

    errorText: { color: 'red', textAlign: 'center', fontSize: 14 * s, marginTop: 20 },

    contextBar: { flexDirection: 'row', padding: 12, backgroundColor: '#e3f2fd', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: '#bbdefb' },
    contextLabel: { fontSize: 13 * s, fontWeight: 'bold', color: '#1565c0' },
    contextBtns: { flexDirection: 'row', backgroundColor: '#fff', borderRadius: 6, borderWidth: 1, borderColor: '#ccc', overflow: 'hidden' },
    ctxBtn: { paddingVertical: 6, paddingHorizontal: 12 },
    ctxBtnActive: { backgroundColor: '#1565c0' },
    ctxBtnTxt: { fontSize: 12 * s, color: '#555', fontWeight: 'bold' },
    ctxBtnTxtActive: { color: '#fff' },

    tabBar: { flexDirection: 'row', backgroundColor: '#fff', elevation: 2 },
    tabItem: { flex: 1, paddingVertical: 14, alignItems: 'center', borderBottomWidth: 3, borderBottomColor: 'transparent' },
    tabItemActive: { borderBottomColor: '#2196F3' },
    tabText: { fontSize: 14 * s, fontWeight: '600', color: '#757575' },
    tabTextActive: { color: '#2196F3' },

    tabContent: { padding: 15 },
    sectionHeader: { fontSize: 14 * s, fontWeight: 'bold', color: '#37474f', marginBottom: 12, marginTop: 15 },

    metadataCard: { backgroundColor: '#fff', borderRadius: 8, padding: 12, borderWidth: 1, borderColor: '#eceff1' },
    fieldRow: { flexDirection: 'row', justifyContent: 'space-between', marginVertical: 4 },
    fieldLab: { fontSize: 13 * s, color: '#546e7a', fontWeight: '500' },
    fieldVal: { fontSize: 13 * s, color: '#263238', fontFamily: 'monospace', fontWeight: 'bold' },

    unifiedCard: { backgroundColor: '#fff', borderRadius: 6, marginBottom: 8, padding: 12, borderLeftWidth: 5, elevation: 1, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 2, shadowOffset: { width: 0, height: 1 }, borderWidth: 1, borderColor: '#eceff1' },
    checkName: { fontSize: 14 * s, fontWeight: 'bold', color: '#37474f' },
    reasonText: { fontSize: 11 * s, color: '#c62828', marginTop: 4, fontStyle: 'italic' },

    blockerCard: { backgroundColor: '#fff5f5', borderRadius: 8, padding: 16, marginBottom: 15, borderWidth: 2, borderColor: '#f44336' },
    blockerTitle: { fontSize: 16 * s, fontWeight: 'bold', color: '#c62828', marginBottom: 8 },
    blockerText: { fontSize: 14 * s, color: '#b71c1c', marginBottom: 4 },
    blockerActionBox: { marginTop: 12, backgroundColor: '#fff', padding: 12, borderRadius: 6, borderWidth: 1, borderColor: '#ffcdd2' },
    blockerActionLabel: { fontSize: 12 * s, color: '#d32f2f', fontWeight: 'bold', marginBottom: 4 },
    blockerActionReq: { fontSize: 14 * s, color: '#000', fontFamily: 'monospace', fontWeight: 'bold', marginBottom: 12 },
    blockerBtn: { backgroundColor: '#f44336', padding: 10, borderRadius: 6, alignItems: 'center' },
    blockerBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 14 * s },

    unauthCard: { backgroundColor: '#fafafa', borderRadius: 8, padding: 20, alignItems: 'center', borderColor: '#eee', borderWidth: 1, marginTop: 20 },
    unauthTitle: { fontSize: 16 * s, fontWeight: 'bold', color: '#757575', marginBottom: 10 },
    unauthText: { fontSize: 14 * s, color: '#9e9e9e', textAlign: 'center', marginBottom: 5 },

    jsonContainer: { backgroundColor: '#263238', borderRadius: 8, padding: 10, height: 400 },
    jsonText: { color: '#c3e88d', fontFamily: 'monospace', fontSize: 11 * s },
    monoText: { fontFamily: 'monospace', fontSize: 12 * s, color: '#546e7a', marginVertical: 2 },

    receiptBadge: { backgroundColor: '#e8f5e9', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4, borderWidth: 1, borderColor: '#c8e6c9' },
    receiptText: { color: '#2e7d32', fontWeight: 'bold', fontSize: 11 * s }
});
