import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { X, FileText, ChevronLeft, ChevronRight, Hash, Bookmark } from 'lucide-react';

interface DocumentViewerModalProps {
  docId: string;
  filename: string;
  highlightSnippet?: string;
  targetPage?: number;
  onClose: () => void;
}

export const DocumentViewerModal: React.FC<DocumentViewerModalProps> = ({
  docId,
  filename,
  highlightSnippet,
  targetPage = 1,
  onClose,
}) => {
  const [chunks, setChunks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(targetPage);

  useEffect(() => {
    async function loadChunks() {
      try {
        setLoading(true);
        const data = await api.getDocumentChunks(docId);
        setChunks(data);
      } catch (e) {
        console.error('Failed to load document chunks', e);
      } finally {
        setLoading(false);
      }
    }
    loadChunks();
  }, [docId]);

  const maxPage = chunks.length > 0 ? Math.max(...chunks.map((c) => c.page_number || 1)) : 1;
  const pageChunks = chunks.filter((c) => c.page_number === currentPage);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
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
          maxWidth: '850px',
          maxHeight: '85vh',
          display: 'flex',
          flexDirection: 'column',
          background: '#0d1322',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 24px',
            borderBottom: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileText size={20} color="#6366f1" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#f8fafc' }}>{filename}</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
          {loading ? (
            <p style={{ color: '#94a3b8', textAlign: 'center', padding: '40px' }}>Loading document chunks...</p>
          ) : pageChunks.length === 0 ? (
            <p style={{ color: '#94a3b8', textAlign: 'center', padding: '40px' }}>No text extracted for page {currentPage}.</p>
          ) : (
            pageChunks.map((chunk, idx) => {
              const isTarget = highlightSnippet && chunk.content.includes(highlightSnippet.slice(0, 30));
              return (
                <div
                  key={chunk.id || idx}
                  style={{
                    background: isTarget ? 'rgba(99, 102, 241, 0.15)' : 'rgba(15, 23, 42, 0.5)',
                    border: isTarget ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.05)',
                    padding: '16px',
                    borderRadius: '10px',
                    marginBottom: '16px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontSize: '0.75rem', color: '#818cf8' }}>
                    <Bookmark size={14} />
                    <span>Section: {chunk.section || 'General'}</span>
                    <span>•</span>
                    <Hash size={14} />
                    <span>Chunk #{chunk.chunk_index} ({chunk.token_count} tokens)</span>
                  </div>
                  <p style={{ color: '#e2e8f0', fontSize: '0.92rem', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                    {chunk.content}
                  </p>
                </div>
              );
            })
          )}
        </div>

        {/* Footer / Pagination */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 24px',
            borderTop: '1px solid var(--border-subtle)',
            background: 'rgba(15, 23, 42, 0.4)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              className="btn-secondary"
              disabled={currentPage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            >
              <ChevronLeft size={16} /> Previous
            </button>
            <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
              Page {currentPage} of {Math.max(1, maxPage)}
            </span>
            <button
              className="btn-secondary"
              disabled={currentPage >= maxPage}
              onClick={() => setCurrentPage((p) => Math.min(maxPage, p + 1))}
              style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            >
              Next <ChevronRight size={16} />
            </button>
          </div>
          <button className="btn-secondary" onClick={onClose} style={{ padding: '6px 16px', fontSize: '0.85rem' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
