import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ScrollView, Button, ActivityIndicator, Dimensions } from 'react-native';
import { fetchDeviceDetail, fetchMetrics, fetchStatus, checkInstallVerification } from '../src/api';
import Svg, { Polyline } from 'react-native-svg';

const MetricCard = ({ label, value, unit, chartData, color }) => {
    const chartWidth = Dimensions.get('window').width - 64;
    const chartHeight = 60;

    const renderChart = () => {
        if (!chartData || chartData.length < 2) return null;

        const max = Math.max(...chartData);
        const min = Math.min(...chartData);
        const range = max - min || 1;

        const points = chartData.map((val, idx) => {
            const x = (idx / (chartData.length - 1)) * chartWidth;
            const y = chartHeight - ((val - min) / range) * chartHeight;
            return `${x},${y}`;
        }).join(' ');

        return (
            <Svg width={chartWidth} height={chartHeight} style={styles.chart}>
                <Polyline
                    points={points}
                    fill="none"
                    stroke={color}
                    strokeWidth="2"
                />
            </Svg>
        );
    };

    return (
        <View style={styles.metricCardBig}>
            <Text style={styles.metricLabelBig}>{label}</Text>
            <View style={styles.metricValueRowBig}>
                <Text style={[styles.metricValueBig, { color }]}>{value}</Text>
                <Text style={styles.metricUnitBig}>{unit}</Text>
            </View>
            {renderChart()}
        </View>
    );
};

const StatusIndicator = ({ status }) => {
    let statusColor = '#9e9e9e';
    switch (status?.toLowerCase()) {
        case 'ok': statusColor = '#4caf50'; break;
        case 'unstable': statusColor = '#ff9800'; break;
        case 'suspected': statusColor = '#f44336'; break;
        case 'investigating': statusColor = '#2196f3'; break;
    }

    return (
        <View style={styles.statusBanner}>
            <View style={styles.statusItem}>
                <View style={[styles.statusIndicator, { backgroundColor: statusColor }]} />
                <View>
                    <Text style={styles.statusLabel}>System Status</Text>
                    <Text style={styles.statusValue}>{status?.toUpperCase() || 'LOADING...'}</Text>
                </View>
            </View>
            <View style={styles.statusItem}>
                <Text style={styles.statusLabel}>Auto-refresh</Text>
                <Text style={styles.statusValue}>Every 2s</Text>
            </View>
        </View>
    );
};

const Section = ({ title, children }) => (
    <View style={styles.section}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {children}
    </View>
);

export default function DeviceDrilldown({ deviceId, onNavigateProof, onBack }) {
    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [metrics, setMetrics] = useState(null);
    const [status, setStatus] = useState(null);
    const [verification, setVerification] = useState(null);
    const [chartData, setChartData] = useState({
        signal: [],
        tx: [],
        rx: [],
        cpu: [],
        memory: []
    });

    const MAX_POINTS = 20;

    useEffect(() => {
        const load = async () => {
            const data = await fetchDeviceDetail(deviceId);
            setDetail(data);
            setLoading(false);
        };
        load();
    }, [deviceId]);

    // Fetch metrics for local device
    useEffect(() => {
        if (deviceId !== 'local') return; // Only fetch metrics for local device

        const loadDataAndMetrics = async () => {
            try {
                const [metricsData, statusData, verificationData] = await Promise.all([
                    fetchMetrics(),
                    fetchStatus(),
                    checkInstallVerification()
                ]);

                if (metricsData) {
                    setMetrics(metricsData);
                    setChartData(prev => {
                        const newData = {
                            signal: [...prev.signal, metricsData.signal_strength_pct || 0],
                            tx: [...prev.tx, metricsData.out_rate || 0],
                            rx: [...prev.rx, metricsData.in_rate || 0],
                            cpu: [...prev.cpu, metricsData.cpu_load || 0],
                            memory: [...prev.memory, metricsData.mem_load || 0]
                        };

                        Object.keys(newData).forEach(key => {
                            if (newData[key].length > MAX_POINTS) {
                                newData[key] = newData[key].slice(-MAX_POINTS);
                            }
                        });

                        return newData;
                    });
                }
                if (statusData) setStatus(statusData.status);
                if (verificationData) setVerification(verificationData);
            } catch (err) {
                console.error("Failed to fetch live data:", err);
            }
        };

        loadDataAndMetrics();
        const interval = setInterval(loadDataAndMetrics, 2000);
        return () => clearInterval(interval);
    }, [deviceId]);

    if (loading) return <ActivityIndicator size="large" color="#2196f3" style={{ marginTop: 50 }} />;
    if (!detail) return <Text>Error loading details.</Text>;

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Button title="< Back" onPress={onBack} />
                <Text style={styles.headerTitle}>Device: {detail.id}</Text>
                <View style={{ width: 50 }} />
            </View>

            <ScrollView contentContainerStyle={styles.content}>

                {/* OBH Snapshot Timeline */}
                <Section title="OBH Snapshot Timeline">
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.timelineScroll}>
                        {detail.obh_snapshot_timeline.map((snap, idx) => (
                            <View key={idx} style={styles.timelineItem}>
                                <Text style={styles.timelineRef}>{snap.ref}</Text>
                                <Text style={styles.timelineType}>{snap.type}</Text>
                                <Text style={styles.timelineTime}>T={snap.time}</Text>
                            </View>
                        ))}
                    </ScrollView>
                </Section>

                {/* Cohort Compare */}
                <Section title="Cohort Compare">
                    <View style={[styles.card, { borderLeftColor: detail.cohort_compare.status === 'normal' ? '#4caf50' : '#ff9800', borderLeftWidth: 4 }]}>
                        <Text style={styles.cardTitle}>{detail.cohort_compare.status.toUpperCase()}</Text>
                        <Text style={styles.cardBody}>{detail.cohort_compare.message}</Text>
                    </View>
                </Section>

                {/* Feature Ledger */}
                <Section title="Feature Ledger">
                    {detail.feature_ledger.length === 0 ? <Text style={styles.emptyText}>No active feature controls.</Text> :
                        detail.feature_ledger.map((f, i) => (
                            <View key={i} style={styles.ledgerRow}>
                                <View>
                                    <Text style={styles.ledgerName}>{f.feature}</Text>
                                    <Text style={styles.ledgerReason}>{f.reason}</Text>
                                </View>
                                <View style={{ alignItems: 'flex-end' }}>
                                    <View style={[styles.badge, { backgroundColor: f.state === 'ON' ? '#4caf50' : '#f44336' }]}>
                                        <Text style={styles.badgeText}>{f.state}</Text>
                                    </View>
                                    {f.ttl && <Text style={styles.ttlText}>{f.ttl}</Text>}
                                </View>
                            </View>
                        ))
                    }
                </Section>

                {/* Compliance Verdict */}
                <Section title="Compliance Verdict">
                    <View style={styles.verdictBox}>
                        <Text style={[styles.verdictTitle, { color: detail.compliance_verdict.result === 'PASS' ? '#2e7d32' : '#c62828' }]}>
                            {detail.compliance_verdict.result}
                        </Text>
                        {detail.compliance_verdict.evidence_missing.length > 0 && (
                            <View style={{ marginTop: 8 }}>
                                <Text style={{ fontWeight: 'bold' }}>Evidence Missing:</Text>
                                {detail.compliance_verdict.evidence_missing.map((e, k) => (
                                    <Text key={k} style={styles.missingItem}>• {e}</Text>
                                ))}
                            </View>
                        )}
                    </View>
                </Section>

                {/* Real-time Metrics - Only for local device */}
                {deviceId === 'local' && metrics && (
                    <Section title="Real-time System Status & Metrics">
                        <StatusIndicator status={status} />

                        <View style={styles.metricsGridBig}>
                            <MetricCard
                                label="Signal Strength"
                                value={metrics?.signal_strength_pct ?? '--'}
                                unit="%"
                                chartData={chartData.signal}
                                color="#667eea"
                            />

                            <MetricCard
                                label="TX Rate"
                                value={metrics?.out_rate ? metrics.out_rate.toFixed(1) : '--'}
                                unit="Mbps"
                                chartData={chartData.tx}
                                color="#48bb78"
                            />

                            <MetricCard
                                label="RX Rate"
                                value={metrics?.in_rate ? metrics.in_rate.toFixed(1) : '--'}
                                unit="Mbps"
                                chartData={chartData.rx}
                                color="#4299e1"
                            />

                            <MetricCard
                                label="CPU Usage"
                                value={metrics?.cpu_load ? metrics.cpu_load.toFixed(1) : '--'}
                                unit="%"
                                chartData={chartData.cpu}
                                color="#ed8936"
                            />

                            <MetricCard
                                label="Memory Usage"
                                value={metrics?.mem_load ? metrics.mem_load.toFixed(1) : '--'}
                                unit="%"
                                chartData={chartData.memory}
                                color="#f56565"
                            />

                            <View style={styles.metricCardBig}>
                                <Text style={styles.metricLabelBig}>Timestamp</Text>
                                <Text style={[styles.metricValueBig, { fontSize: 16, color: '#667eea' }]}>
                                    {metrics?.ts ? Math.floor(metrics.ts) : '--'}
                                </Text>
                                <Text style={styles.metricUnitBig}>Unix Time</Text>
                            </View>
                        </View>

                        {verification && (
                            <View style={styles.verificationCard}>
                                <Text style={styles.verificationTitle}>Installation Verification</Text>
                                <View style={styles.verificationGrid}>
                                    <View style={styles.verificationItem}>
                                        <Text style={styles.verificationLabel}>Closure Readiness</Text>
                                        <Text style={[
                                            styles.verificationValue,
                                            { color: verification.closure_readiness === 'ready' ? '#48bb78' : '#f56565' }
                                        ]}>
                                            {verification.closure_readiness?.toUpperCase() || '--'}
                                        </Text>
                                    </View>

                                    <View style={styles.verificationItem}>
                                        <Text style={styles.verificationLabel}>Readiness Verdict</Text>
                                        <Text style={[
                                            styles.verificationValue,
                                            { color: verification.readiness_verdict === 'PASS' ? '#48bb78' : '#f56565' }
                                        ]}>
                                            {verification.readiness_verdict || '--'}
                                        </Text>
                                    </View>

                                    <View style={styles.verificationItem}>
                                        <Text style={styles.verificationLabel}>Dominant Factor</Text>
                                        <Text style={styles.verificationValue}>
                                            {verification.dominant_factor || '--'}
                                        </Text>
                                    </View>

                                    <View style={styles.verificationItem}>
                                        <Text style={styles.verificationLabel}>Confidence</Text>
                                        <Text style={styles.verificationValue}>
                                            {verification.confidence ? verification.confidence.toFixed(2) : '--'}
                                        </Text>
                                    </View>
                                </View>
                            </View>
                        )}
                    </Section>
                )}

                <View style={{ marginTop: 24, marginBottom: 40 }}>
                    <Button title="Generate Proof Card" onPress={() => onNavigateProof(deviceId)} color="#673ab7" />
                </View>

            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 12,
        backgroundColor: '#fff',
        justifyContent: 'space-between',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    headerTitle: { fontSize: 18, fontWeight: 'bold' },
    content: { padding: 16 },
    section: { marginBottom: 24 },
    sectionTitle: { fontSize: 16, fontWeight: '600', color: '#444', marginBottom: 8 },
    card: { backgroundColor: '#fff', padding: 12, borderRadius: 8 },
    cardTitle: { fontWeight: 'bold', fontSize: 14, marginBottom: 4 },
    cardBody: { fontSize: 14, color: '#555' },

    timelineScroll: { paddingVertical: 8 },
    timelineItem: {
        marginRight: 12,
        backgroundColor: '#e3f2fd',
        padding: 10,
        borderRadius: 8,
        minWidth: 100,
        alignItems: 'center'
    },
    timelineRef: { fontWeight: 'bold', fontSize: 14, color: '#1565c0' },
    timelineType: { fontSize: 12, color: '#1976d2' },
    timelineTime: { fontSize: 10, color: '#555', marginTop: 4 },

    ledgerRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        backgroundColor: '#fff',
        padding: 12,
        borderRadius: 8,
        marginBottom: 8
    },
    ledgerName: { fontSize: 15, fontWeight: 'bold', color: '#333' },
    ledgerReason: { fontSize: 12, color: '#888' },
    badge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
    badgeText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },
    ttlText: { fontSize: 10, color: '#f57c00', marginTop: 2 },

    emptyText: { fontStyle: 'italic', color: '#999' },

    verdictBox: {
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 8,
        alignItems: 'center'
    },
    verdictTitle: { fontSize: 24, fontWeight: '900' },
    missingItem: { color: '#d32f2f', fontSize: 12, marginTop: 2 },

    // Big Metrics styles from MetricsView
    statusBanner: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    statusItem: { flexDirection: 'row', alignItems: 'center', gap: 12 },
    statusIndicator: { width: 12, height: 12, borderRadius: 6 },
    statusLabel: { fontSize: 12, color: '#888' },
    statusValue: { fontSize: 14, fontWeight: '600', color: '#333' },
    metricsGridBig: { gap: 12 },
    metricCardBig: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    metricLabelBig: {
        fontSize: 12,
        color: '#888',
        textTransform: 'uppercase',
        letterSpacing: 1,
        marginBottom: 8,
        fontWeight: '500',
    },
    metricValueRowBig: {
        flexDirection: 'row',
        alignItems: 'baseline',
        marginBottom: 12,
    },
    metricValueBig: { fontSize: 32, fontWeight: '700', marginRight: 8 },
    metricUnitBig: { fontSize: 14, color: '#666' },
    chart: { marginTop: 8 },

    // Verification Card
    verificationCard: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        marginTop: 16,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    verificationTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
        marginBottom: 16,
    },
    verificationGrid: { gap: 12 },
    verificationItem: {
        backgroundColor: '#f9f9f9',
        padding: 12,
        borderRadius: 8,
    },
    verificationLabel: {
        fontSize: 11,
        color: '#888',
        textTransform: 'uppercase',
        letterSpacing: 1,
        marginBottom: 4,
    },
    verificationValue: { fontSize: 16, fontWeight: '600', color: '#333' }
});
