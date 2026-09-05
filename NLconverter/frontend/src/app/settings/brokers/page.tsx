'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ConnectBrokerForm } from './components/ConnectBrokerForm';
import { BrokerList } from './components/BrokerList';

export default function BrokerSettings() {
  const router = useRouter();
  const [brokers, setBrokers] = useState<any[]>([]);
  const [isConnecting, setIsConnecting] = useState(false);
  
  const [selectedBroker, setSelectedBroker] = useState('kite');
  const [credentials, setCredentials] = useState({ api_key: '', api_secret: '', client_id: '', access_token: '' });

  const fetchBrokers = async () => {
    try {
      const res = await fetch('/api/v1/brokers/');
      if (res.ok) {
        const data = await res.json();
        setBrokers(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchBrokers();
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsConnecting(true);
    
    let creds = {};
    if (selectedBroker === 'kite' || selectedBroker === 'upstox') {
      creds = { api_key: credentials.api_key, api_secret: credentials.api_secret };
    } else if (selectedBroker === 'dhan') {
      creds = { client_id: credentials.client_id, access_token: credentials.access_token };
    }

    try {
      const res = await fetch('/api/v1/brokers/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ broker_name: selectedBroker, credentials: creds })
      });
      if (res.ok) {
        setCredentials({ api_key: '', api_secret: '', client_id: '', access_token: '' });
        fetchBrokers();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to remove this broker integration?')) return;
    try {
      await fetch(`/api/v1/brokers/${id}`, { method: 'DELETE' });
      fetchBrokers();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSetActive = async (id: number) => {
    try {
      await fetch(`/api/v1/brokers/${id}/active`, { method: 'PUT' });
      fetchBrokers();
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogin = (broker: any) => {
      if (broker.broker_name === 'kite') {
          window.location.href = `/api/v1/brokers/${broker.id}/login`;
      }
  };

  const getBrokerDisplayName = (name: string) => {
    const map: Record<string, string> = { kite: 'Zerodha Kite', upstox: 'Upstox', dhan: 'Dhan' };
    return map[name] || name;
  };

  return (
    <div className="min-h-screen bg-[#050505] text-zinc-100 p-6 pt-24 md:p-12 md:pt-32 font-sans selection:bg-zinc-800">
      <div className="max-w-5xl mx-auto space-y-12">
        
        {/* Header Section */}
        <div className="space-y-4">
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight text-white">
            Broker Credentials
          </h1>
          <p className="text-zinc-400 text-base max-w-2xl">
            Securely connect your brokerage accounts to enable live algorithmic trading and real-time market data streaming.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Add New Broker Form (Left Side) */}
          <div className="lg:col-span-5">
            <ConnectBrokerForm 
              selectedBroker={selectedBroker}
              setSelectedBroker={setSelectedBroker}
              credentials={credentials}
              setCredentials={setCredentials}
              isConnecting={isConnecting}
              handleConnect={handleConnect}
            />
          </div>

          {/* Active Connections List (Right Side) */}
          <div className="lg:col-span-7">
            <BrokerList 
              brokers={brokers}
              handleLogin={handleLogin}
              handleSetActive={handleSetActive}
              handleDelete={handleDelete}
              getBrokerDisplayName={getBrokerDisplayName}
            />
          </div>
          
        </div>
      </div>
    </div>
  );
}
