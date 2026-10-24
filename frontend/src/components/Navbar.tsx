import React from 'react';
import type { User, PortalType, KnowledgeBase } from '../types';
import {
  Sparkles,
  Command,
  LogOut,
  Shield,
  Brain,
  Users,
  MessageSquare,
  Activity,
} from 'lucide-react';

interface NavbarProps {
  user: User | null;
  currentPortal: PortalType;
  onSelectPortal: (portal: PortalType) => void;
  knowledgeBases: KnowledgeBase[];
  selectedKBId: string | null;
  onSelectKB: (kbId: string) => void;
  onOpenCommandPalette: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  user,
  currentPortal,
  onSelectPortal,
  knowledgeBases,
  selectedKBId,
  onSelectKB,
  onOpenCommandPalette,
  onLogout,
}) => {
  const portals: { id: PortalType; label: string; icon: any; requiredRole?: string[] }[] = [
    { id: 'user', label: 'Voice Assistant', icon: <MessageSquare size={16} /> },
    { id: 'org_admin', label: 'Org Admin', icon: <Users size={16} />, requiredRole: ['ORGANIZATION_ADMIN', 'SUPER_ADMIN', 'ORGANIZATION_OWNER'] },
    { id: 'ai_admin', label: 'AI / MLOps', icon: <Brain size={16} />, requiredRole: ['AI_ADMIN', 'SUPER_ADMIN', 'ORGANIZATION_ADMIN'] },
    { id: 'system_admin', label: 'System Health', icon: <Activity size={16} />, requiredRole: ['SYSTEM_ADMIN', 'SUPER_ADMIN'] },
    { id: 'auditor', label: 'Auditor Trail', icon: <Shield size={16} />, requiredRole: ['AUDITOR', 'SUPER_ADMIN', 'ORGANIZATION_ADMIN'] },
  ];

  return (
    <header
      style={{
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(9, 13, 22, 0.85)',
        backdropFilter: 'blur(16px)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        padding: '0 24px',
        height: '68px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }} onClick={() => onSelectPortal('user')}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)',
            }}
          >
            <Sparkles size={20} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em', margin: 0 }}>
              RAG VOICE INTELLIGENCE
            </h1>
            <span style={{ fontSize: '0.68rem', color: '#818cf8', fontWeight: 600, letterSpacing: '0.04em' }}>
              EVIDENCE-GROUNDED PRIVATE AI
            </span>
          </div>
        </div>

        {/* Knowledge Base Selector */}
        {knowledgeBases.length > 0 && (
          <select
            className="glass-input"
            value={selectedKBId || ''}
            onChange={(e) => onSelectKB(e.target.value)}
            style={{ fontSize: '0.85rem', padding: '6px 12px', height: '36px' }}
          >
            <option value="" disabled>Select Knowledge Base...</option>
            {knowledgeBases.map((kb) => (
              <option key={kb.id} value={kb.id} style={{ background: '#0f172a', color: 'white' }}>
                {kb.name} ({kb.document_count || 0} docs)
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Navigation Portals */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        {portals.map((p) => {
          const isActive = currentPortal === p.id;
          return (
            <button
              key={p.id}
              onClick={() => onSelectPortal(p.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 14px',
                borderRadius: '8px',
                border: 'none',
                background: isActive ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                color: isActive ? '#a5b4fc' : '#94a3b8',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {p.icon}
              {p.label}
            </button>
          );
        })}
      </nav>

      {/* Utilities & User Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <button
          className="btn-secondary"
          onClick={onOpenCommandPalette}
          title="Open Command Palette (Ctrl+K)"
          style={{ padding: '6px 12px', fontSize: '0.8rem' }}
        >
          <Command size={14} />
          <span>Cmd+K</span>
        </button>

        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f8fafc', display: 'block' }}>
                {user.full_name}
              </span>
              <span style={{ fontSize: '0.72rem', color: '#6366f1', textTransform: 'uppercase', fontWeight: 700 }}>
                {user.role}
              </span>
            </div>
            <button
              onClick={onLogout}
              className="btn-secondary"
              title="Logout session"
              style={{ padding: '8px', color: '#ef4444' }}
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
