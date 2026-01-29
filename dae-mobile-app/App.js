import React, { useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { setBaseUrl } from './src/api';
import { StyleSheet, SafeAreaView, Platform, StatusBar } from 'react-native';
import HomeDashboard from './components/HomeDashboard';
import InstallationVerifier from './components/InstallationVerifier';
import SimulateIncident from './components/SimulateIncident';
import SettingsMenu from './components/SettingsMenu';
import OneButtonHelper from './components/OneButtonHelper';
import FleetView from './components/FleetView';
import DeviceDrilldown from './components/DeviceDrilldown';
import ProofCard from './components/ProofCard';
import MetricsView from './components/MetricsView';
import ModuleInspector from './components/ModuleInspector';
import IpConfigScreen from './components/IpConfigScreen';


export default function App() {

  // Changed default to IP_CONFIG to force user input
  const [currentScreen, setCurrentScreen] = useState('IP_CONFIG');
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);

  // We no longer automatically set IP on load, we just wait for user in IpConfigScreen

  const handleNavigate = (screenId) => {
    if (screenId === 'PROOF') {
      setSelectedDeviceId('local');
    }
    setCurrentScreen(screenId);
  };

  const navigateToDrilldown = (deviceId) => {
    setSelectedDeviceId(deviceId);
    setCurrentScreen('DRILLDOWN');
  };

  const navigateToProof = (deviceId) => {
    setCurrentScreen('PROOF');
  };

  const navigateToMetrics = () => {
    setCurrentScreen('METRICS');
  };

  const navigateToModules = () => {
    setCurrentScreen('MODULES');
  };

  const navigateBack = () => {
    if (currentScreen === 'PROOF') {
      setCurrentScreen('DRILLDOWN');
    } else if (currentScreen === 'DRILLDOWN') {
      setCurrentScreen('FLEET');
      setSelectedDeviceId(null);
    } else if (['METRICS', 'MODULES'].includes(currentScreen)) {
      // Return to wherever we came from, but for now FLEET is the main legacy parent
      setCurrentScreen('FLEET');
    } else if (currentScreen === 'SETTINGS') {
      setCurrentScreen('HOME');

    } else if (currentScreen === 'SIMULATE') {
      setCurrentScreen('SETTINGS');
    } else {
      // Default back to Home
      setCurrentScreen('HOME');
    }
  };

  const handleConnect = (ip) => {
    setBaseUrl(ip);
    setCurrentScreen('HOME');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />

      {currentScreen === 'IP_CONFIG' && (
        <IpConfigScreen onConnect={handleConnect} />
      )}

      {currentScreen === 'HOME' && (
        <HomeDashboard onNavigate={handleNavigate} />
      )}

      {currentScreen === 'SETTINGS' && (
        <SettingsMenu
          onNavigate={handleNavigate}
          onBack={() => setCurrentScreen('HOME')}
        />
      )}

      {currentScreen === 'INSTALL' && (
        <InstallationVerifier onBack={() => setCurrentScreen('HOME')} />
      )}

      {currentScreen === 'SIMULATE' && (
        <SimulateIncident onBack={navigateBack} />
      )}

      {currentScreen === 'OBH' && (
        <OneButtonHelper onBack={() => setCurrentScreen('HOME')} />
      )}

      {currentScreen === 'FLEET' && (
        <FleetView
          onNavigate={navigateToDrilldown}
          onNavigateMetrics={navigateToMetrics}
          onNavigateModules={navigateToModules}
          onBack={() => setCurrentScreen('HOME')} // Pass back prop if FleetView supports it, or add button
        />
      )}

      {currentScreen === 'DRILLDOWN' && selectedDeviceId && (
        <DeviceDrilldown
          deviceId={selectedDeviceId}
          onNavigateProof={navigateToProof}
          onBack={navigateBack}
        />
      )}
      {currentScreen === 'PROOF' && selectedDeviceId && (
        <ProofCard
          deviceId={selectedDeviceId}
          onBack={navigateBack}
        />
      )}
      {currentScreen === 'METRICS' && (
        <MetricsView onBack={navigateBack} />
      )}
      {currentScreen === 'MODULES' && (
        <ModuleInspector onBack={navigateBack} />
      )}


    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#fff', // Changed to match HomeDashboard
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  }
});
