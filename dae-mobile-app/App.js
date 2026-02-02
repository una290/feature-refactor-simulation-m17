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

  // Changed default to HOME as requested, connection logic moved there
  const [currentScreen, setCurrentScreen] = useState('HOME');
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);

  // We no longer automatically set IP on load, we just wait for user in HomeDashboard

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

  // Connection State (Lifted from HomeDashboard)
  const [ip, setIp] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [log, setLog] = useState([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const loadSavedIp = async () => {
      try {
        const saved = await AsyncStorage.getItem('api_ip');
        if (saved) {
          setIp(saved);
        }
      } catch (e) {
        console.error('Failed to load IP', e);
      }
    };
    loadSavedIp();
  }, []);

  const addLog = (message) => {
    setLog(prev => [`[${new Date().toLocaleTimeString()}] ${message}`, ...prev]);
  };

  const handleConnect = async (targetIp) => {
    // If called with an argument, use it (from input), otherwise use state 'ip'
    const ipToConnect = targetIp || ip;
    if (!ipToConnect) return;

    setIsLoading(true);
    setIsConnected(false);
    setLog([]); // Clear previous log
    addLog('Starting connection...');

    // Auto-fix common input errors
    let cleanIp = ipToConnect.trim();
    if (!cleanIp.startsWith('http://') && !cleanIp.startsWith('https://')) {
      cleanIp = 'http://' + cleanIp;
    }

    // Remove trailing slash if present for consistency
    if (cleanIp.endsWith('/')) {
      cleanIp = cleanIp.slice(0, -1);
    }

    // Update IP state if it changed via cleaning or argument
    setIp(cleanIp);
    addLog(`Target: ${cleanIp}`);

    try {
      // Health check ping
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

      addLog('Sending health check...');
      const response = await fetch(`${cleanIp}/`, {
        method: 'GET',
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      addLog(`Response status: ${response.status}`);

      if (response.ok) {
        setIsConnected(true);
        addLog('Connection Successful!');
        await AsyncStorage.setItem('api_ip', cleanIp);
        setBaseUrl(cleanIp);
      } else {
        throw new Error(`Server returned ${response.status}`);
      }
    } catch (e) {
      console.log('Connection failed', e);
      let msg = e.message || 'Unknown error';
      if (e.name === 'AbortError' || msg.includes('aborted')) {
        msg = 'Timed Out (Check Firewall)';
      }
      addLog(`Error: ${msg}`);
      setIsLoading(false);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />

      {currentScreen === 'IP_CONFIG' && (
        <IpConfigScreen onConnect={handleConnect} />
      )}

      {currentScreen === 'HOME' && (
        <HomeDashboard
          onNavigate={handleNavigate}

          // Pass connection props
          ip={ip}
          setIp={setIp}
          log={log}
          isConnected={isConnected}
          isLoading={isLoading}
          onConnect={() => handleConnect(ip)}
        />
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
