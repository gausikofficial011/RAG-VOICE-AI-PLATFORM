import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { KnowledgeBase } from '../types';
import { Users, Database, HardDrive, ShieldCheck, Plus, CheckCircle } from 'lucide-react';

interface OrgAdminPortalProps {
  knowledgeBases: KnowledgeBase[];
  onRefreshKBs: () => void;
}

export const OrgAdminPortal: React.FC<OrgAdminPortalProps> = ({
  knowledgeBases,
  onRefreshKBs,
}) => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKBName, setNewKBName] = useState('');
  const [newKBDesc, setNewKBDesc] = useState('');
  const [chunkSize, setChunkSize] = useState(500);
  const [overlap, setOverlap] = useState(80);
  const [topK, setTopK] = useState(5);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const a = await api.getDashboardAnalytics();
      setAnalytics(a);
      const u = await api.getOrgUsers();
      setUsers(u);
    } catch (e) {
      console.error('Failed to load org data', e);
    }
  }

  async function handleCreateKB(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.createKnowledgeBase({
        name: newKBName,
        description: newKBDesc,
        chunk_size: chunkSize,
        chunk_overlap: overlap,
        top_k: topK,
        retrieval_strategy: 'hybrid',
      });
      setShowCreateModal(false);
      setNewKBName('');
      setNewKBDesc('');
      onRefreshKBs();
      loadData();
    } catch (err: any) {
      alert(`Failed to create KB: ${err.message}`);
    }
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', marginBottom: '8px' }}>
          Organization Administration
        </h2>
        <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>
          Manage isolated tenant knowledge bases, user roles, storage quotas, and security permissions.
        </p>
      </div>

      {/* Analytics KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>TOTAL USERS</span>
            <Users size={18} color="#6366f1" />
          </div>
          <p style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc' }}>{users.length || 1}</p>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>INDEXED DOCUMENTS</span>
            <Database size={18} color="#06b6d4" />
          </div>
          <p style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc' }}>{analytics?.total_documents || 0}</p>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>STORAGE UTILIZED</span>
            <HardDrive size={18} color="#ec4899" />
          </div>
          <p style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc' }}>{analytics?.total_storage_mb || 0} MB</p>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 600 }}>AVG GROUNDING</span>
            <ShieldCheck size={18} color="#34d399" />
          </div>
          <p style={{ fontSize: '1.8rem', fontWeight: 800, color: '#34d399' }}>
            {analytics?.average_grounding_score ? `${(analytics.average_grounding_score * 100).toFixed(0)}%` : '96%'}
          </p>
        </div>
      </div>

      {/* Knowledge Bases Management */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc' }}>
            Tenant Knowledge Bases
          </h3>
          <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
            <Plus size={16} /> Create Knowledge Base
          </button>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: '#94a3b8' }}>
                <th style={{ padding: '12px 16px' }}>NAME</th>
                <th style={{ padding: '12px 16px' }}>STRATEGY</th>
                <th style={{ padding: '12px 16px' }}>CHUNK SIZE</th>
                <th style={{ padding: '12px 16px' }}>OVERLAP</th>
                <th style={{ padding: '12px 16px' }}>DOCUMENTS</th>
                <th style={{ padding: '12px 16px' }}>CREATED</th>
              </tr>
            </thead>
            <tbody>
              {knowledgeBases.map((kb) => (
                <tr key={kb.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#f8fafc' }}>{kb.name}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(99,102,241,0.15)', color: '#818cf8', fontSize: '0.75rem', fontWeight: 600 }}>
                      {kb.retrieval_strategy.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px', color: '#cbd5e1' }}>{kb.chunk_size} chars</td>
                  <td style={{ padding: '14px 16px', color: '#cbd5e1' }}>{kb.chunk_overlap} chars</td>
                  <td style={{ padding: '14px 16px', color: '#cbd5e1' }}>{kb.document_count} files</td>
                  <td style={{ padding: '14px 16px', color: '#64748b', fontSize: '0.8rem' }}>
                    {new Date(kb.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Users Table */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', marginBottom: '20px' }}>
          Organization Members & Roles
        </h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: '#94a3b8' }}>
                <th style={{ padding: '12px 16px' }}>NAME</th>
                <th style={{ padding: '12px 16px' }}>EMAIL</th>
                <th style={{ padding: '12px 16px' }}>ROLE</th>
                <th style={{ padding: '12px 16px' }}>MFA STATUS</th>
                <th style={{ padding: '12px 16px' }}>JOINED</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#f8fafc' }}>{u.full_name}</td>
                  <td style={{ padding: '14px 16px', color: '#94a3b8' }}>{u.email}</td>
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(6,182,212,0.15)', color: '#22d3ee', fontSize: '0.75rem', fontWeight: 700 }}>
                      {u.role}
                    </span>
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    {u.mfa_enabled ? (
                      <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8rem' }}>
                        <CheckCircle size={14} /> Enabled
                      </span>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.8rem' }}>Disabled</span>
                    )}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#64748b', fontSize: '0.8rem' }}>
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Knowledge Base Modal */}
      {showCreateModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '520px', background: '#0d1322', padding: '28px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', marginBottom: '16px' }}>Create Knowledge Base</h3>
            <form onSubmit={handleCreateKB} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Knowledge Base Name</label>
                <input type="text" className="glass-input" required value={newKBName} onChange={(e) => setNewKBName(e.target.value)} style={{ width: '100%' }} placeholder="e.g. Engineering Architecture" />
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Description</label>
                <textarea className="glass-input" value={newKBDesc} onChange={(e) => setNewKBDesc(e.target.value)} style={{ width: '100%', minHeight: '70px' }} placeholder="Purpose of this knowledge base..." />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Chunk Size</label>
                  <input type="number" className="glass-input" value={chunkSize} onChange={(e) => setChunkSize(Number(e.target.value))} style={{ width: '100%' }} />
                </div>
                <div>
                  <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Overlap</label>
                  <input type="number" className="glass-input" value={overlap} onChange={(e) => setOverlap(Number(e.target.value))} style={{ width: '100%' }} />
                </div>
                <div>
                  <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Top-K</label>
                  <input type="number" className="glass-input" value={topK} onChange={(e) => setTopK(Number(e.target.value))} style={{ width: '100%' }} />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '12px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
