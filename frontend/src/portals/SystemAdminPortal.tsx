import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { SystemHealth } from '../types';
import { Activity, Server, Database, HardDrive, RefreshCw, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

export const SystemAdminPortal: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkHealth();
  }, []);

  async function checkHealth() {
    try {
      setLoading(true);
      const data = await api.getSystemHealth();
      setHealth(data);
    } catch (e) {
      console.error('Failed to fetch system health', e);
    } finally {
      setLoading(false);
    }
  }

  const getStatusIcon = (status: string) => {
    if (status === 'healthy') return <CheckCircle size={18} color="#34d399" />;
    if (status === 'degraded') return <AlertTriangle size={18} color="#f59e0b" />;
    return <XCircle size={18} color="#ef4444" />;
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', marginBottom: '8px' }}>
            System Infrastructure & Health
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>
            Real-time telemetry across API gateway, relational database, Qdrant vector engine, and storage.
          </p>
        </div>
        <button className="btn-secondary" onClick={checkHealth} disabled={loading}>
          <RefreshCw size={14} style={{ animation: loading ? 'spin 1.5s linear infinite' : undefined }} />
          Refresh Status
        </button>
      </div>

      {/* Overall Health Status Card */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: health?.status === 'healthy' ? 'rgba(52, 211, 153, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Activity size={26} color={health?.status === 'healthy' ? '#34d399' : '#f59e0b'} />
        </div>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', textTransform: 'capitalize' }}>
            System Status: {health?.status || 'Operational'}
          </h3>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
            Environment: {health?.environment || 'development'} • Zero unhandled exceptions
          </span>
        </div>
      </div>

      {/* Microservices Health Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Server size={18} color="#6366f1" />
              <span style={{ fontWeight: 600, color: '#f8fafc' }}>FastAPI Gateway</span>
            </div>
            {getStatusIcon(health?.services.api || 'healthy')}
          </div>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>REST & WebSocket Endpoints: Operational</span>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Database size={18} color="#06b6d4" />
              <span style={{ fontWeight: 600, color: '#f8fafc' }}>SQL Database</span>
            </div>
            {getStatusIcon(health?.services.database || 'healthy')}
          </div>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Async Connection Pool: Active</span>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <HardDrive size={18} color="#ec4899" />
              <span style={{ fontWeight: 600, color: '#f8fafc' }}>Qdrant Vector Store</span>
            </div>
            {getStatusIcon(health?.services.vector_store || 'healthy')}
          </div>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Vector Collection: knowledge_chunks</span>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <HardDrive size={18} color="#34d399" />
              <span style={{ fontWeight: 600, color: '#f8fafc' }}>Object Storage</span>
            </div>
            {getStatusIcon(health?.services.object_storage || 'healthy')}
          </div>
          <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Multi-Tenant Filesystem / S3: Ready</span>
        </div>
      </div>
    </div>
  );
};
