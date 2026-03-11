import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { simulateIncident } from '../src/api';

export default function DomainConfig({ onBack }) {
    const [targetDomain, setTargetDomain] = useState('WIFI');

    // We repurpose the SimulateIncident api parameter to just send a dummy/null incident
    // but pass the domain override so the server flips modes continuously.
    // For a real app this would call a dedicated settings endpoint.
    const handleSetDomain = (domain) => {
        setTargetDomain(domain);

        // Use "stable" type for 5 mins just to set the domain override actively
        simulateIncident("stable", 300, domain).catch(err => {
            console.error("Failed to set domain override", err);
        });
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Demo Domain Override</Text>
                <View style={{ width: 60 }} />
            </View>

            <View style={styles.content}>
                <Text style={styles.title}>Target Demo Domain</Text>
                <Text style={styles.description}>
                    For demonstration purposes, manually force the app to simulate a different physical network interface. This will change the context of the metrics and verification rules applied.
                </Text>

                <View style={styles.domainToggleRow}>
                    <TouchableOpacity
                        style={[styles.domainToggleBtn, targetDomain === 'WIFI' && styles.domainToggleBtnActive]}
                        onPress={() => handleSetDomain('WIFI')}
                    >
                        <Text style={[styles.domainToggleText, targetDomain === 'WIFI' && styles.domainToggleTextActive]}>📶 Wi-Fi</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={[styles.domainToggleBtn, targetDomain === 'CABLE' && styles.domainToggleBtnActive]}
                        onPress={() => handleSetDomain('CABLE')}
                    >
                        <Text style={[styles.domainToggleText, targetDomain === 'CABLE' && styles.domainToggleTextActive]}>🔌 DOCSIS (Cable)</Text>
                    </TouchableOpacity>
                </View>

                <View style={{ marginTop: 30, padding: 15, backgroundColor: '#e8f5e9', borderRadius: 8 }}>
                    <Text style={{ color: '#2e7d32', fontWeight: 'bold' }}>Current Override Active: {targetDomain}</Text>
                    <Text style={{ color: '#1b5e20', fontSize: 13, marginTop: 5 }}>The "Installation Verifier" and logic engines will now evaluate against this profile context.</Text>
                </View>
            </View>
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
        paddingBottom: 16,
        paddingHorizontal: 16,
        backgroundColor: '#FFF',
        borderBottomWidth: 1,
        borderBottomColor: '#C6C6C8',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    backButton: {
        padding: 8,
        minWidth: 60,
    },
    backButtonText: {
        fontSize: 17,
        color: '#007AFF',
    },
    headerTitle: {
        fontSize: 17,
        fontWeight: '600',
        color: '#000',
    },
    content: {
        padding: 20,
    },
    title: {
        fontSize: 18,
        fontWeight: '700',
        marginBottom: 10,
        color: '#333'
    },
    description: {
        fontSize: 14,
        color: '#666',
        marginBottom: 20,
        lineHeight: 20
    },
    domainToggleRow: {
        flexDirection: 'row',
        marginTop: 5,
    },
    domainToggleBtn: {
        flex: 1,
        paddingVertical: 15,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#ccc',
        backgroundColor: '#fff',
        marginHorizontal: 4,
        borderRadius: 8
    },
    domainToggleBtnActive: {
        backgroundColor: '#FF8A65',
        borderColor: '#E64A19'
    },
    domainToggleText: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#555'
    },
    domainToggleTextActive: {
        color: '#fff'
    }
});
