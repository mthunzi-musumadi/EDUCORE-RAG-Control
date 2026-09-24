export type ClearanceTier = 'public' | 'staff' | 'counselor' | 'finance' | 'devops' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
  clearance: ClearanceTier;
  campus: string;
  groups: string[];
  profile_image_url?: string;
  created_at?: number;
}

export interface AuthResponse {
  token: string;
  token_type: string;
  user: User;
}

export interface EducoreModel {
  id: string;
  name: string;
  targetUser?: string;
  clearanceLevel?: string;
  requiredTier?: ClearanceTier;
  description?: string;
  base_model_id?: string;
  system_prompt?: string;
  temperature?: number;
  top_p?: number;
  is_custom?: boolean;
  is_active?: boolean;
}

export interface RetrievedDocument {
  id: string;
  title: string;
  campus: string;
  clearance: string;
  classification: string;
  purview_label: string;
  source_file: string;
  content?: string;
  score?: number;
}

export interface MessageTelemetry {
  tps?: number;
  latency_ms?: number;
  generation_time_s?: number;
  retrieved_records?: RetrievedDocument[];
  guardrail_code?: string;
  user_profile?: any;
  suggested_followups?: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  telemetry?: MessageTelemetry;
  isStreaming?: boolean;
}

export interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  modelId: string;
  messages: ChatMessage[];
  pinned?: boolean;
}

export interface UserSettings {
  default_model: string;
  temperature: number;
  system_prompt: string;
  streaming: boolean;
  theme: 'dark' | 'light';
  auto_scroll: boolean;
}

export interface SystemStatus {
  status: string;
  service?: string;
  compliance?: string;
  available_models?: number;
  total_vector_count?: number;
  shard_vector_counts?: Record<string, number>;
  tracked_files?: Record<string, any>;
  last_sync_time?: number;
}

export interface AuditEntry {
  timestamp: string;
  user_email: string;
  campus: string;
  clearance: string;
  query: string;
  response_summary?: string;
  retrieved_count?: number;
  guardrail_status: string;
  latency_ms: number;
  tps?: number;
  model: string;
}

export const EDUCORE_DEFAULT_MODELS: EducoreModel[] = [
  {
    id: 'educore-enterprise-all',
    name: 'Educore Enterprise RAG',
    targetUser: 'All Institutional Staff',
    clearanceLevel: 'Adaptive / Universal',
    requiredTier: 'public',
    description: 'Universal enterprise model; dynamically adapts to authenticated clearance and Purview boundaries.'
  },
  {
    id: 'educore-socratic-student',
    name: 'Educore Socratic Student',
    targetUser: 'Students & Learners',
    clearanceLevel: 'Tier C (Public)',
    requiredTier: 'public',
    description: 'Socratic diagnostic hints only (Guardrail Stu-01). Prohibits homework answer dumping; enforces cognitive ownership.'
  },
  {
    id: 'educore-faculty-academic',
    name: 'Educore Faculty & Academic',
    targetUser: 'Teaching Faculty & Curriculum Leads',
    clearanceLevel: 'Tier B (Staff)',
    requiredTier: 'staff',
    description: 'Cambridge IGCSE Math 0580 syllabus, lesson planning, and rubric design. Automated grading strictly blocked (Edu-01).'
  },
  {
    id: 'educore-pastoral-counselor',
    name: 'Educore Pastoral Counselor',
    targetUser: 'Campus Pastoral Counselors',
    clearanceLevel: 'Tier A (Confidential)',
    requiredTier: 'counselor',
    description: 'Authorized review of confidential student welfare cases (e.g. Case #402). Zambian phone & NRC shielding.'
  },
  {
    id: 'educore-finance-audit',
    name: 'Educore Finance & Audit',
    targetUser: 'Bursars & Finance Officers',
    clearanceLevel: 'Tier A (Finance)',
    requiredTier: 'finance',
    description: 'M365 Copilot Finance emulation with Guardrail Fin-01 Dual-Key Manual Audit notices and partner subsidy masking.'
  },
  {
    id: 'educore-it-devops',
    name: 'Educore IT & DevOps',
    targetUser: 'IT Engineers & Systems Admins',
    clearanceLevel: 'Tier A (Restricted IT)',
    requiredTier: 'devops',
    description: 'GitHub Copilot Enterprise emulation; enforces IT-01 secret scanning and SAST peer review rules.'
  },
  {
    id: 'educore-admin-governance',
    name: 'Educore Admin & Governance',
    targetUser: 'Campus Heads & Executives',
    clearanceLevel: 'Tier A (Executive)',
    requiredTier: 'admin',
    description: 'Cross-campus multi-tenant governance (Sentinel, Trident, Frontier), AIIA management, and ISO 42001 telemetry.'
  }
];
