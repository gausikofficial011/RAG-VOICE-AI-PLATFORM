/**
 * Unified API Client for RAG Voice Intelligence Platform
 */

const API_BASE = 'http://localhost:8000/api';

class ApiClient {
  private getHeaders(isMultipart: boolean = false): HeadersInit {
    const headers: Record<string, string> = {};
    if (!isMultipart) {
      headers['Content-Type'] = 'application/json';
    }
    const token = localStorage.getItem('access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const isMultipart = options.body instanceof FormData;
    const headers = {
      ...this.getHeaders(isMultipart),
      ...(options.headers || {}),
    };

    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (res.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
      // Try refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
          if (refreshRes.ok) {
            const data = await refreshRes.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            // Retry original request
            return this.request<T>(endpoint, options);
          }
        } catch {
          // Fall through to logout
        }
      }
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }

    if (!res.ok) {
      let errorMsg = `Error ${res.status}`;
      try {
        const errorData = await res.json();
        errorMsg = errorData.detail || errorData.error?.message || errorMsg;
      } catch {
        // Ignored
      }
      throw new Error(errorMsg);
    }

    return res.json();
  }

  // Auth
  async register(data: any) {
    return this.request<any>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async login(data: any) {
    return this.request<any>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getMe() {
    return this.request<any>('/auth/me');
  }

  async logout() {
    try {
      await this.request<any>('/auth/logout', { method: 'POST' });
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  async setupMfa() {
    return this.request<any>('/auth/mfa/setup', { method: 'POST' });
  }

  async verifyMfa(code: string) {
    return this.request<any>('/auth/mfa/verify', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  }

  // Knowledge Bases
  async getKnowledgeBases() {
    return this.request<any[]>('/knowledge-bases');
  }

  async createKnowledgeBase(data: any) {
    return this.request<any>('/knowledge-bases', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async deleteKnowledgeBase(id: string) {
    return this.request<any>(`/knowledge-bases/${id}`, { method: 'DELETE' });
  }

  // Documents
  async getDocuments(kbId?: string) {
    const url = kbId ? `/documents?kb_id=${kbId}` : '/documents';
    return this.request<any[]>(url);
  }

  async uploadDocument(kbId: string, file: File) {
    const formData = new FormData();
    formData.append('kb_id', kbId);
    formData.append('file', file);
    return this.request<any>('/documents/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async getDocumentChunks(docId: string) {
    return this.request<any[]>(`/documents/${docId}/chunks`);
  }

  async deleteDocument(docId: string) {
    return this.request<any>(`/documents/${docId}`, { method: 'DELETE' });
  }

  // RAG & Chat
  async queryRAG(data: { query: string; kb_id?: string; conversation_id?: string; audio_requested?: boolean; language?: string }) {
    return this.request<any>('/rag/query', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getConversations() {
    return this.request<any[]>('/rag/conversations');
  }

  async getConversationMessages(convId: string) {
    return this.request<any[]>(`/rag/conversations/${convId}/messages`);
  }

  async submitFeedback(data: { message_id: string; rating: number; feedback_type: string; comment?: string }) {
    return this.request<any>('/rag/feedback', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async voiceQuery(audioBlob: Blob, kbId?: string, convId?: string, language?: string, transcriptText?: string) {
    const formData = new FormData();
    formData.append('file', audioBlob, 'speech.wav');
    if (kbId) formData.append('kb_id', kbId);
    if (convId) formData.append('conversation_id', convId);
    if (language) formData.append('language', language);
    if (transcriptText) formData.append('transcript_text', transcriptText);

    return this.request<any>('/voice/query', {
      method: 'POST',
      body: formData,
    });
  }

  async synthesizeSpeech(text: string, language?: string) {
    const formData = new FormData();
    formData.append('text', text);
    if (language) formData.append('language', language);
    return this.request<any>('/voice/synthesize', {
      method: 'POST',
      body: formData,
    });
  }

  // ML & Models
  async getModels() {
    return this.request<any[]>('/ml/models');
  }

  async trainModel(modelName: string) {
    return this.request<any>(`/ml/models/${modelName}/train`, {
      method: 'POST',
      body: JSON.stringify({ dataset_version: 'v1.0.0' }),
    });
  }

  async deployModel(modelName: string, version: string) {
    return this.request<any>(`/ml/models/${modelName}/deploy`, {
      method: 'POST',
      body: JSON.stringify({ version }),
    });
  }

  // Analytics & Health & Audit
  async getDashboardAnalytics() {
    return this.request<any>('/analytics/dashboard');
  }

  async getAuditLogs(eventType?: string) {
    const url = eventType ? `/audit/logs?event_type=${eventType}` : '/audit/logs';
    return this.request<any[]>(url);
  }

  async getSystemHealth() {
    return this.request<any>('/health');
  }

  async getOrgUsers() {
    return this.request<any[]>('/organizations/users');
  }

  // PC & Laptop Autonomous Agent
  async executeAgentCommand(command: string, audioRequested: boolean = true) {
    return this.request<any>('/agent/command', {
      method: 'POST',
      body: JSON.stringify({ command, audio_requested: audioRequested }),
    });
  }

  async getAgentTelemetry() {
    return this.request<any>('/agent/telemetry');
  }

  async getRunningProcesses(limit: number = 8) {
    return this.request<any>(`/agent/processes?limit=${limit}`);
  }

  async executeAgentWorkflow(workflowName: string) {
    return this.request<any>('/agent/workflow', {
      method: 'POST',
      body: JSON.stringify({ workflow_name: workflowName }),
    });
  }
}

export const api = new ApiClient();
