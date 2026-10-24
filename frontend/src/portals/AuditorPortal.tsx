import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { AuditLogItem } from '../types';
import { Filter } from 'lucide-react';

export const AuditorPortal: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterType, setFilterType] = useState<string>('');

  useEffect(() => {
    loadAuditLogs();
  }, [filterType]);

  async function loadAuditLogs() {
    try {
      setLoading(true);
      const data = await api.getAuditLogs(filterType || undefined);
      setLogs(data);
    } catch (e) {
      console.error('Failed to load audit logs', e);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', marginBottom: '8px' }}>
            Compliance & Security Audit Trail
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>
            Immutable, tamper-resistant record of authentication, access control, and document operations.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Filter size={16} color="#94a3b8" />
          <select
            className="glass-input"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            style={{ fontSize: '0.85rem' }}
          >
            <option value="">All Security Events</option>
            <option value="LOGIN">LOGIN</option>
            <option value="LOGOUT">LOGOUT</option>
            <option value="REGISTER">REGISTER</option>
            <option value="MFA_ENABLED">MFA_ENABLED</option>
            <option value="DOC_UPLOAD">DOC_UPLOAD</option>
            <option value="DOC_DELETE">DOC_DELETE</option>
            <option value="KB_CREATE">KB_CREATE</option>
            <option value="KB_DELETE">KB_DELETE</option>
          </select>
        </div>
      </div>

      {/* Audit Log Records Table */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: '#94a3b8' }}>
                <th style={{ padding: '12px 14px' }}>TIMESTAMP</th>
                <th style={{ padding: '12px 14px' }}>EVENT TYPE</th>
                <th style={{ padding: '12px 14px' }}>ACTION</th>
                <th style={{ padding: '12px 14px' }}>IP ADDRESS</th>
                <th style={{ padding: '12px 14px' }}>STATUS</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ padding: '32px', textAlign: 'center', color: '#64748b' }}>
                    {loading ? 'Fetching compliance records...' : 'No audit records found.'}
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '12px 14px', color: '#94a3b8', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: log.event_type.includes('DELETE') ? 'rgba(239,68,68,0.15)' : 'rgba(99,102,241,0.15)',
                          color: log.event_type.includes('DELETE') ? '#f87171' : '#818cf8',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                        }}
                      >
                        {log.event_type}
                      </span>
                    </td>
                    <td style={{ padding: '12px 14px', color: '#f8fafc', fontWeight: 500 }}>
                      {log.action}
                    </td>
                    <td style={{ padding: '12px 14px', color: '#94a3b8', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {log.ip_address || '127.0.0.1'}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span
                        style={{
                          color: log.status === 'SUCCESS' ? '#34d399' : '#f87171',
                          fontWeight: 600,
                          fontSize: '0.8rem',
                        }}
                      >
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
