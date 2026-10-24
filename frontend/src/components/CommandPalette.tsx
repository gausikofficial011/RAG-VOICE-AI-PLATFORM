import React, { useEffect, useState } from 'react';
import { Search, Mic, FolderPlus, Upload, Shield, Database, LayoutDashboard, X } from 'lucide-react';
import type { PortalType } from '../types';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPortal: (portal: PortalType) => void;
  onOpenUpload: () => void;
  onOpenCreateKB: () => void;
  onStartVoice: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onSelectPortal,
  onOpenUpload,
  onOpenCreateKB,
  onStartVoice,
}) => {
  const [search, setSearch] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const actions = [
    { id: 'voice', label: 'Start Voice Assistant', icon: <Mic size={18} color="#ec4899" />, run: onStartVoice },
    { id: 'upload', label: 'Upload Document (PDF, DOCX, CSV)', icon: <Upload size={18} color="#06b6d4" />, run: onOpenUpload },
    { id: 'create_kb', label: 'Create New Knowledge Base', icon: <FolderPlus size={18} color="#818cf8" />, run: onOpenCreateKB },
    { id: 'portal_user', label: 'Switch to User Portal', icon: <LayoutDashboard size={18} color="#6366f1" />, run: () => onSelectPortal('user') },
    { id: 'portal_org', label: 'Switch to Org Admin Portal', icon: <Database size={18} color="#38bdf8" />, run: () => onSelectPortal('org_admin') },
    { id: 'portal_ai', label: 'Switch to AI / MLOps Admin Portal', icon: <Database size={18} color="#a855f7" />, run: () => onSelectPortal('ai_admin') },
    { id: 'portal_auditor', label: 'Switch to Security & Audit Portal', icon: <Shield size={18} color="#34d399" />, run: () => onSelectPortal('auditor') },
  ];

  const filtered = actions.filter((a) => a.label.toLowerCase().includes(search.toLowerCase()));

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.7)',
        backdropFilter: 'blur(8px)',
        zIndex: 10000,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '15vh',
      }}
      onClick={onClose}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '600px',
          background: '#0d1322',
          border: '1px solid rgba(255,255,255,0.15)',
          borderRadius: '16px',
          overflow: 'hidden',
          boxShadow: '0 25px 50px -12px rgba(0,0,0,0.8)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
          <Search size={20} color="#818cf8" style={{ marginRight: '12px' }} />
          <input
            autoFocus
            type="text"
            placeholder="Type a command or search action (Esc to close)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#f8fafc',
              fontSize: '1rem',
              width: '100%',
            }}
          />
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ maxHeight: '350px', overflowY: 'auto', padding: '8px' }}>
          {filtered.length === 0 ? (
            <p style={{ color: '#64748b', textAlign: 'center', padding: '24px', fontSize: '0.9rem' }}>No matching commands found.</p>
          ) : (
            filtered.map((item) => (
              <div
                key={item.id}
                onClick={() => {
                  item.run();
                  onClose();
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: '10px',
                  cursor: 'pointer',
                  transition: 'background 0.15s ease',
                  color: '#e2e8f0',
                  fontSize: '0.95rem',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(99, 102, 241, 0.15)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                {item.icon}
                <span>{item.label}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
