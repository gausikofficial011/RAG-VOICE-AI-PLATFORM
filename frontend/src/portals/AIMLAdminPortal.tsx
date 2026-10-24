import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import type { MLModel } from '../types';
import { Brain, Cpu, Play, RefreshCw } from 'lucide-react';

export const AIMLAdminPortal: React.FC = () => {
  const [models, setModels] = useState<MLModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [trainingModelName, setTrainingModelName] = useState<string | null>(null);
  const [trainingLogs, setTrainingLogs] = useState<string | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  async function loadModels() {
    try {
      setLoading(true);
      const data = await api.getModels();
      setModels(data);
    } catch (e) {
      console.error('Failed to load ML models', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleTrain(modelName: string) {
    try {
      setTrainingModelName(modelName);
      setTrainingLogs(`Initiating controlled training pipeline for ${modelName}...`);
      const res = await api.trainModel(modelName);
      setTrainingLogs(
        `✓ Training Complete!\n` +
        `Accuracy: ${(res.metrics.accuracy * 100).toFixed(1)}%\n` +
        `Weighted F1: ${(res.metrics.f1 * 100).toFixed(1)}%\n` +
        `Artifact saved: ml/artifacts/${modelName}.joblib`
      );
      await loadModels();
    } catch (err: any) {
      setTrainingLogs(`❌ Training failed: ${err.message}`);
    } finally {
      setTrainingModelName(null);
    }
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 24px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', marginBottom: '8px' }}>
          AI & MLOps Model Registry
        </h2>
        <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>
          Two-layer AI architecture: Foundation LLM/Speech models + Project-specific trained NLP and grounding classifiers.
        </p>
      </div>

      {/* Model Cards Grid */}
      {loading && <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Loading models from registry...</p>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px' }}>
        {models.map((model) => {
          const activeVer = model.versions?.[model.active_version] || {};
          const isTraining = trainingModelName === model.name;

          return (
            <div key={model.name} className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>
                    <Brain size={20} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>{model.name}</h3>
                    <span style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>
                      Type: {model.type}
                    </span>
                  </div>
                </div>
                <span
                  style={{
                    padding: '3px 10px',
                    borderRadius: '20px',
                    background: 'rgba(52, 211, 153, 0.15)',
                    border: '1px solid rgba(52, 211, 153, 0.3)',
                    color: '#34d399',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                  }}
                >
                  DEPLOYED
                </span>
              </div>

              <p style={{ fontSize: '0.88rem', color: '#cbd5e1', lineHeight: '1.5' }}>
                {model.description}
              </p>

              {/* Version & Metrics Box */}
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.8rem' }}>
                  <span style={{ color: '#94a3b8' }}>Active Version:</span>
                  <span style={{ color: '#818cf8', fontWeight: 700 }}>{model.active_version}</span>
                </div>
                {activeVer.metrics && (
                  <div style={{ display: 'flex', gap: '14px', fontSize: '0.8rem' }}>
                    {activeVer.metrics.accuracy !== undefined && (
                      <span style={{ color: '#34d399' }}>Accuracy: {(activeVer.metrics.accuracy * 100).toFixed(0)}%</span>
                    )}
                    {activeVer.metrics.f1 !== undefined && (
                      <span style={{ color: '#38bdf8' }}>F1: {(activeVer.metrics.f1 * 100).toFixed(0)}%</span>
                    )}
                    {activeVer.metrics.mrr !== undefined && (
                      <span style={{ color: '#c084fc' }}>MRR: {activeVer.metrics.mrr}</span>
                    )}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: '10px', marginTop: 'auto' }}>
                <button
                  className="btn-primary"
                  onClick={() => handleTrain(model.name)}
                  disabled={isTraining}
                  style={{ flex: 1, justifyContent: 'center' }}
                >
                  {isTraining ? <RefreshCw size={14} style={{ animation: 'spin 1.5s linear infinite' }} /> : <Play size={14} />}
                  {isTraining ? 'Training Run...' : 'Train Model'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Training Run Output Terminal */}
      {trainingLogs && (
        <div className="glass-panel" style={{ padding: '20px', background: '#020617', border: '1px solid #1e293b' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <Cpu size={16} color="#818cf8" />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8' }}>TRAINING WORKER LOGS</span>
          </div>
          <pre style={{ color: '#38bdf8', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
            {trainingLogs}
          </pre>
        </div>
      )}
    </div>
  );
};
