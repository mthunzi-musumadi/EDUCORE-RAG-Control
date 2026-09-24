import { 
  User, 
  AuthResponse, 
  EducoreModel, 
  MessageTelemetry, 
  SystemStatus, 
  AuditEntry 
} from '../types';
import { AuthService } from './auth';

export interface StreamCallbacks {
  onChunk: (text: string) => void;
  onDone: (telemetry?: MessageTelemetry) => void;
  onError: (error: Error) => void;
}

export interface ChatOptions {
  temperature?: number;
  systemPrompt?: string;
}

function getAuthHeaders(): Record<string, string> {
  const token = AuthService.getToken();
  const user = AuthService.getUser();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (user) {
    headers['X-Educore-User-Email'] = user.email;
    headers['X-Educore-User-Role'] = user.role;
    headers['X-Educore-User-Groups'] = (user.groups || []).join(',');
  }
  return headers;
}

export const ApiService = {
  // Authentication Endpoints
  async signIn(email: string, password: string): Promise<AuthResponse> {
    const res = await fetch('/api/v1/auths/signin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Sign in failed');
    }
    return data;
  },

  async signUp(name: string, email: string, password: string, campus: string = 'all'): Promise<AuthResponse> {
    const res = await fetch('/api/v1/auths/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, campus })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Sign up failed');
    }
    return data;
  },

  async getCurrentUser(): Promise<User> {
    const res = await fetch('/api/v1/auths/user', {
      method: 'GET',
      headers: getAuthHeaders()
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Failed to fetch user session');
    }
    return data;
  },

  async updateProfile(name: string, email: string): Promise<{ success: boolean; user: User }> {
    const res = await fetch('/api/v1/auths/update/profile', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ name, email })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Failed to update profile');
    }
    return data;
  },

  async updatePassword(currentPassword: string, newPassword: string): Promise<{ success: boolean }> {
    const res = await fetch('/api/v1/auths/update/password', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Failed to update password');
    }
    return data;
  },

  // Admin User Directory
  async getUsers(): Promise<User[]> {
    const res = await fetch('/api/v1/users', {
      method: 'GET',
      headers: getAuthHeaders()
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Failed to fetch user directory');
    }
    return data.users || data;
  },

  async updateUser(userData: { id: string; role: string; clearance: string; campus: string }): Promise<{ success: boolean }> {
    const res = await fetch('/api/v1/users/user/update', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(userData)
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Failed to update user');
    }
    return data;
  },

  async deleteUser(userId: string): Promise<{ success: boolean }> {
    const res = await fetch('/api/v1/users/user/delete', {
      method: 'DELETE',
      headers: getAuthHeaders(),
      body: JSON.stringify({ id: userId })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Failed to delete user');
    }
    return data;
  },

  // Model Management
  async getModels(): Promise<EducoreModel[]> {
    const res = await fetch('/api/v1/models', {
      method: 'GET',
      headers: getAuthHeaders()
    });
    if (!res.ok) {
      // Fallback to /v1/models
      const fallback = await fetch('/v1/models');
      const d = await fallback.json();
      return (d.data || []).map((m: any) => ({
        id: m.id,
        name: m.name || m.id,
        description: m.description || '',
        requiredTier: m.requiredTier || 'public',
        targetUser: m.targetUser || 'General User'
      }));
    }
    const data = await res.json();
    return data.data || data;
  },

  async createModel(modelData: Partial<EducoreModel>): Promise<{ success: boolean; model: EducoreModel }> {
    const res = await fetch('/api/v1/models/create', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(modelData)
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Failed to create model');
    }
    return data;
  },

  async updateModel(modelData: Partial<EducoreModel>): Promise<{ success: boolean; model: EducoreModel }> {
    const res = await fetch('/api/v1/models/model/update', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(modelData)
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Failed to update model');
    }
    return data;
  },

  async deleteModel(modelId: string): Promise<{ success: boolean }> {
    const res = await fetch('/api/v1/models/model/delete', {
      method: 'DELETE',
      headers: getAuthHeaders(),
      body: JSON.stringify({ id: modelId })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || data.detail || 'Failed to delete model');
    }
    return data;
  },

  // Framework Knowledge & Governance
  async syncFramework(force: boolean = false): Promise<any> {
    const res = await fetch('/api/framework/sync', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ force })
    });
    return res.json();
  },

  async getFrameworkStatus(): Promise<SystemStatus> {
    const res = await fetch('/api/framework/status', {
      headers: getAuthHeaders()
    });
    return res.json();
  },

  async getAuditLogs(): Promise<AuditEntry[]> {
    const res = await fetch('/api/audit', {
      headers: getAuthHeaders()
    });
    return res.json();
  },

  async getHealth(): Promise<{ status: string }> {
    const res = await fetch('/health');
    return res.json();
  },

  // Streaming Chat Completion
  async streamChat(
    messages: { role: string; content: string }[],
    modelId: string,
    user: User | null,
    callbacks: StreamCallbacks,
    options?: ChatOptions,
    abortSignal?: AbortSignal
  ): Promise<void> {
    try {
      const headers = getAuthHeaders();
      const payload: any = {
        model: modelId,
        messages: messages,
        stream: true,
      };

      if (user) {
        payload.user = {
          id: user.id,
          name: user.name,
          email: user.email,
          role: user.role,
          clearance: user.clearance,
          campus: user.campus,
          groups: user.groups,
        };
      }

      if (options?.temperature !== undefined) {
        payload.temperature = options.temperature;
      }
      if (options?.systemPrompt) {
        payload.system_prompt = options.systemPrompt;
      }

      const response = await fetch('/v1/chat/completions', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
        signal: abortSignal,
      });

      if (!response.ok) {
        let errMessage = `Server returned status ${response.status}`;
        try {
          const errJson = await response.json();
          if (errJson.error) {
            errMessage = typeof errJson.error === 'string' ? errJson.error : errJson.error.message || errMessage;
          }
        } catch {
          // fallback
        }
        throw new Error(errMessage);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let capturedTelemetry: MessageTelemetry | undefined;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith(':')) continue;

          if (trimmed.startsWith('data: ')) {
            const dataStr = trimmed.slice(6).trim();
            if (dataStr === '[DONE]') {
              continue;
            }

            try {
              const parsed = JSON.parse(dataStr);
              const deltaContent = parsed.choices?.[0]?.delta?.content;
              if (deltaContent) {
                callbacks.onChunk(deltaContent);
              }
              if (parsed.educore_telemetry) {
                capturedTelemetry = parsed.educore_telemetry;
              }
            } catch {
              // ignore malformed chunks
            }
          }
        }
      }

      callbacks.onDone(capturedTelemetry);
    } catch (err: any) {
      if (err.name === 'AbortError') {
        callbacks.onDone();
      } else {
        callbacks.onError(err);
      }
    }
  }
};
