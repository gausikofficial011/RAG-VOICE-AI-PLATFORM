export type Role =
  | 'SUPER_ADMIN'
  | 'SYSTEM_ADMIN'
  | 'ORGANIZATION_OWNER'
  | 'ORGANIZATION_ADMIN'
  | 'AI_ADMIN'
  | 'AUDITOR'
  | 'MANAGER'
  | 'USER'
  | 'VIEWER';

export type PortalType = 'user' | 'org_admin' | 'ai_admin' | 'system_admin' | 'auditor';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  tenant_id: string;
  is_active: boolean;
  mfa_enabled: boolean;
  preferences: {
    theme: string;
    language: string;
    voice: string;
    voice_speed: number;
    auto_play_audio: boolean;
  };
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  role: Role;
  permissions: string[];
  mfa_required?: boolean;
}

export interface KnowledgeBase {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  embedding_model: string;
  retrieval_strategy: string;
  chunk_size: number;
  chunk_overlap: number;
  similarity_threshold: number;
  top_k: number;
  rerank_k: number;
  document_count: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentItem {
  id: string;
  tenant_id: string;
  kb_id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  classification: string;
  status: string;
  error_message?: string;
  token_count: number;
  chunk_count: number;
  doc_metadata: Record<string, any>;
  uploaded_by?: string;
  created_at: string;
  updated_at: string;
}

export interface CitationItem {
  chunk_id: string;
  document_id: string;
  filename: string;
  page: number;
  section: string;
  snippet: string;
  score: number;
}

export interface LatencyMetrics {
  vad_ms?: number;
  stt_ms?: number;
  intent_ms?: number;
  retrieval_ms?: number;
  rerank_ms?: number;
  llm_ms?: number;
  grounding_ms?: number;
  tts_ms?: number;
  total_ms: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  intent?: string;
  grounding_score?: number;
  grounding_status?: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'UNSUPPORTED';
  citations?: CitationItem[];
  latency?: LatencyMetrics;
  audio_base64?: string;
  created_at: string;
}

export interface MLModelVersion {
  version: string;
  dataset_version: string;
  status: string;
  artifact_path?: string;
  metrics?: Record<string, any>;
  created_at: string;
}

export interface MLModel {
  name: string;
  type: string;
  description: string;
  active_version: string;
  versions: Record<string, MLModelVersion>;
}

export interface AuditLogItem {
  id: string;
  event_type: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  user_id?: string;
  ip_address?: string;
  status: string;
  details: Record<string, any>;
  timestamp: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'down';
  services: {
    api: string;
    database: string;
    vector_store: string;
    object_storage: string;
    ml_models: string;
  };
  environment: string;
}
