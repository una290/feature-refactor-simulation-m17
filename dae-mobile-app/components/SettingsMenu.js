import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getBaseUrl, setBaseUrl } from '../src/api';

export default function SettingsMenu({ onNavigate, onBack }) {
    const [ip, setIp] = useState(getBaseUrl());

    const handleSave = async () => {
        try {
            setBaseUrl(ip);
            await AsyncStorage.setItem('api_ip', ip);
            Alert.alert('Success', 'IP Address saved!');
        } catch (e) {
            console.error(e);
            Alert.alert('Error', 'Failed to save settings');
        }
    };

    const settingsItems = [
        {
            id: 'SIMULATE',
            title: 'Simulate Incident (M17)',
            desc: 'Inject faults to test detection logic',
            icon: '⚠'
        },
        // Future settings can go here
    ];

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Settings</Text>
                <View style={{ width: 60 }} /> {/* Spacer for centering */}
            </View>

            <ScrollView contentContainerStyle={styles.menuContainer}>
                <Text style={styles.sectionHeader}>Connection Settings</Text>
                <View style={styles.inputContainer}>
                    <Text style={styles.inputLabel}>Backend URL</Text>
                    <TextInput
                        style={styles.input}
                        value={ip}
                        onChangeText={setIp}
                        autoCapitalize="none"
                        autoCorrect={false}
                        placeholder="http://192.168.x.x:8000"
                    />
                    <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
                        <Text style={styles.saveButtonText}>Save</Text>
                    </TouchableOpacity>
                </View>

                <Text style={styles.sectionHeader}>Developer Options</Text>

                {settingsItems.map((item) => (
                    <TouchableOpacity
                        key={item.id}
                        style={styles.itemRow}
                        onPress={() => onNavigate(item.id)}
                    >
                        <View style={styles.iconContainer}>
                            <Text style={styles.iconText}>{item.icon}</Text>
                        </View>
                        <View style={styles.textContainer}>
                            <Text style={styles.itemTitle}>{item.title}</Text>
                            <Text style={styles.itemDesc}>{item.desc}</Text>
                        </View>
                        <Text style={styles.arrow}>›</Text>
                    </TouchableOpacity>
                ))}

                <View style={styles.versionContainer}>
                    <Text style={styles.versionText}>DAE P1 Mobile App v1.0</Text>
                </View>
            </ScrollView>
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
    menuContainer: {
        paddingVertical: 20,
    },
    sectionHeader: {
        fontSize: 13,
        color: '#6D6D72',
        marginBottom: 8,
        paddingHorizontal: 16,
        textTransform: 'uppercase',
    },
    itemRow: {
        backgroundColor: '#FFF',
        paddingVertical: 12,
        paddingHorizontal: 16,
        flexDirection: 'row',
        alignItems: 'center',
        borderTopWidth: StyleSheet.hairlineWidth,
        borderBottomWidth: StyleSheet.hairlineWidth,
        borderColor: '#C6C6C8',
        marginBottom: 20, // Group spacing
    },
    iconContainer: {
        width: 30,
        alignItems: 'center',
        marginRight: 12,
    },
    iconText: {
        fontSize: 22,
    },
    textContainer: {
        flex: 1,
    },
    itemTitle: {
        fontSize: 17,
        color: '#000',
        marginBottom: 2,
    },
    itemDesc: {
        fontSize: 13,
        color: '#8E8E93',
    },
    arrow: {
        fontSize: 20,
        color: '#C7C7CC',
        marginLeft: 8,
    },
    versionContainer: {
        padding: 20,
        alignItems: 'center',
    },
    versionText: {
        fontSize: 13,
        color: '#8E8E93',
    },
    inputContainer: {
        backgroundColor: '#FFF',
        padding: 16,
        marginBottom: 20,
        borderTopWidth: StyleSheet.hairlineWidth,
        borderBottomWidth: StyleSheet.hairlineWidth,
        borderColor: '#C6C6C8',
    },
    inputLabel: {
        fontSize: 13,
        color: '#6D6D72',
        marginBottom: 8,
        textTransform: 'uppercase',
    },
    input: {
        height: 44,
        borderWidth: 1,
        borderColor: '#C6C6C8',
        borderRadius: 8,
        paddingHorizontal: 12,
        fontSize: 17,
        marginBottom: 12,
        backgroundColor: '#F9F9F9',
    },
    saveButton: {
        backgroundColor: '#007AFF',
        borderRadius: 8,
        paddingVertical: 12,
        alignItems: 'center',
    },
    saveButtonText: {
        color: '#FFF',
        fontSize: 17,
        fontWeight: '600',
    }
});
