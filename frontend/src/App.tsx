import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import type { User, PortalType, KnowledgeBase } from './types';
import { Navbar } from './components/Navbar';
import { CommandPalette } from './components/CommandPalette';
import { UserPortal } from './portals/UserPortal';
import { OrgAdminPortal } from './portals/OrgAdminPortal';
import { AIMLAdminPortal } from './portals/AIMLAdminPortal';
import { SystemAdminPortal } from './portals/SystemAdminPortal';
import { AuditorPortal } from './portals/AuditorPortal';
import { SiriDesktopOverlay } from './components/SiriDesktopOverlay';
import { Sparkles, Lock, Mail, User as UserIcon, Building } from 'lucide-react';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [portal, setPortal] = useState<PortalType>('user');
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKBId, setSelectedKBId] = useState<string | null>(null);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  // Auth modal states
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authName, setAuthName] = useState('');
  const [authOrg, setAuthOrg] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [mfaRequired, setMfaRequired] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  useEffect(() => {
    checkAuthSession();
  }, []);

  async function checkAuthSession() {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const user = await api.getMe();
      setCurrentUser(user);
      await loadKnowledgeBases();
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  async function loadKnowledgeBases() {
    try {
      const kbs = await api.getKnowledgeBases();
      setKnowledgeBases(kbs);
      if (kbs.length > 0 && !selectedKBId) {
        setSelectedKBId(kbs[0].id);
      }
    } catch (e) {
      console.error('Failed to load knowledge bases', e);
    }
  }

  async function handleAuthSubmit(e: React.FormEvent) {
    e.preventDefault();
    setAuthError(null);
    setAuthLoading(true);

    try {
      if (isLoginMode) {
        const res = await api.login({
          email: authEmail.trim(),
          password: authPassword.trim(),
          mfa_code: mfaCode.trim() || undefined,
        });

        if (res.mfa_required) {
          setMfaRequired(true);
          setAuthLoading(false);
          return;
        }

        localStorage.setItem('access_token', res.access_token);
        localStorage.setItem('refresh_token', res.refresh_token);
      } else {
        const res = await api.register({
          email: authEmail,
          password: authPassword,
          full_name: authName,
          organization_name: authOrg || undefined,
        });
        localStorage.setItem('access_token', res.access_token);
        localStorage.setItem('refresh_token', res.refresh_token);
      }

      await checkAuthSession();
    } catch (err: any) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogout() {
    await api.logout();
    setCurrentUser(null);
    setKnowledgeBases([]);
    setSelectedKBId(null);
    setMfaRequired(false);
    setMfaCode('');
  }

  // If unauthenticated, show Enterprise Login/Register Screen
  if (!currentUser) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
        }}
      >
        <div
          className="glass-panel"
          style={{
            width: '100%',
            maxWidth: '460px',
            padding: '36px',
            background: 'rgba(15, 23, 42, 0.85)',
          }}
        >
          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
                margin: '0 auto 14px auto',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 20px rgba(99, 102, 241, 0.5)',
              }}
            >
              <Sparkles size={26} color="white" />
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
              RAG VOICE INTELLIGENCE
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '0.88rem', marginTop: '4px' }}>
              Voice-first, evidence-grounded AI for private knowledge.
            </p>
          </div>

          {/* Quick Demo Fill Pills */}
          {isLoginMode && (
            <div style={{ marginBottom: '20px', padding: '12px', borderRadius: '12px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255, 255, 255, 0.06)' }}>
              <span style={{ fontSize: '0.72rem', color: '#94a3b8', display: 'block', marginBottom: '8px', textAlign: 'center', fontWeight: 600, letterSpacing: '0.04em' }}>
                QUICK DEMO ACCOUNTS (CLICK TO AUTOFILL):
              </span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
                {[
                  { label: 'Admin (All)', email: 'admin@ragvoice.ai' },
                  { label: 'Org Admin', email: 'orgadmin@ragvoice.ai' },
                  { label: 'AI/ML Admin', email: 'aiadmin@ragvoice.ai' },
                  { label: 'Auditor', email: 'auditor@ragvoice.ai' },
                  { label: 'User', email: 'user@ragvoice.ai' },
                ].map((demo) => (
                  <button
                    key={demo.email}
                    type="button"
                    onClick={() => {
                      setAuthEmail(demo.email);
                      setAuthPassword('Password123!');
                      setAuthError(null);
                    }}
                    style={{
                      background: authEmail === demo.email ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255, 255, 255, 0.05)',
                      border: authEmail === demo.email ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.1)',
                      color: authEmail === demo.email ? '#818cf8' : '#cbd5e1',
                      borderRadius: '16px',
                      padding: '4px 10px',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                      fontWeight: 500,
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {demo.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleAuthSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {!isLoginMode && (
              <>
                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Full Name</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type="text"
                      className="glass-input"
                      required
                      placeholder="Jane Doe"
                      value={authName}
                      onChange={(e) => setAuthName(e.target.value)}
                      style={{ width: '100%', paddingLeft: '36px' }}
                    />
                    <UserIcon size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Organization Name</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type="text"
                      className="glass-input"
                      placeholder="Enterprise Corp"
                      value={authOrg}
                      onChange={(e) => setAuthOrg(e.target.value)}
                      style={{ width: '100%', paddingLeft: '36px' }}
                    />
                    <Building size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                  </div>
                </div>
              </>
            )}

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Email Address</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="email"
                  className="glass-input"
                  required
                  placeholder="name@company.com"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  style={{ width: '100%', paddingLeft: '36px' }}
                />
                <Mail size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Password</label>
              <div style={{ position: 'relative' }}>
                <input
                  type="password"
                  className="glass-input"
                  required
                  placeholder="••••••••••••"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  style={{ width: '100%', paddingLeft: '36px' }}
                />
                <Lock size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '12px' }} />
              </div>
            </div>

            {mfaRequired && (
              <div>
                <label style={{ fontSize: '0.8rem', color: '#38bdf8', display: 'block', marginBottom: '6px' }}>
                  Enter 6-Digit Authenticator / Recovery Code
                </label>
                <input
                  type="text"
                  className="glass-input"
                  required
                  placeholder="123456"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                  style={{ width: '100%', letterSpacing: '0.2em', textAlign: 'center', fontSize: '1.2rem' }}
                />
              </div>
            )}

            {authError && (
              <p style={{ color: '#f87171', fontSize: '0.85rem', textAlign: 'center' }}>{authError}</p>
            )}

            <button type="submit" className="btn-primary" disabled={authLoading} style={{ width: '100%', justifyContent: 'center', marginTop: '8px' }}>
              {authLoading ? 'Verifying...' : mfaRequired ? 'Verify MFA Code' : isLoginMode ? 'Sign In to Platform' : 'Create Organization Account'}
            </button>
          </form>

          {/* Switch Mode */}
          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <button
              onClick={() => {
                setIsLoginMode(!isLoginMode);
                setAuthError(null);
                setMfaRequired(false);
              }}
              style={{ background: 'transparent', border: 'none', color: '#818cf8', fontSize: '0.85rem', cursor: 'pointer' }}
            >
              {isLoginMode ? "Don't have an account? Register organization" : 'Already registered? Sign in'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        user={currentUser}
        currentPortal={portal}
        onSelectPortal={setPortal}
        knowledgeBases={knowledgeBases}
        selectedKBId={selectedKBId}
        onSelectKB={setSelectedKBId}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        onLogout={handleLogout}
      />

      <div style={{ flex: 1 }}>
        {portal === 'user' && (
          <UserPortal
            knowledgeBases={knowledgeBases}
            selectedKBId={selectedKBId}
            onRefreshKBs={loadKnowledgeBases}
          />
        )}
        {portal === 'org_admin' && (
          <OrgAdminPortal
            knowledgeBases={knowledgeBases}
            onRefreshKBs={loadKnowledgeBases}
          />
        )}
        {portal === 'ai_admin' && <AIMLAdminPortal />}
        {portal === 'system_admin' && <SystemAdminPortal />}
        {portal === 'auditor' && <AuditorPortal />}
      </div>

      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        onSelectPortal={setPortal}
        onOpenUpload={() => setPortal('user')}
        onOpenCreateKB={() => setPortal('org_admin')}
        onStartVoice={() => setPortal('user')}
      />

      {/* Floating Apple Siri Desktop Assistant for Laptop / PC */}
      <SiriDesktopOverlay
        knowledgeBases={knowledgeBases}
        selectedKBId={selectedKBId}
        onOpenPortal={setPortal}
      />
    </div>
  );
};
export default App;
