// src/types/api.ts

export const VulnerabilityAssessmentType = {
  NETWORK_SCAN: 'network_scan',
  WEB_APP_PENTEST: 'web_app_pentest',
  INFRASTRUCTURE_AUDIT: 'infrastructure_audit',
} as const;

export type VulnerabilityAssessmentType = typeof VulnerabilityAssessmentType[keyof typeof VulnerabilityAssessmentType];

export const AssessmentStatus = {
  DELETED: 'deleted',
  AVAILABLE: 'available',
} as const;

export type AssessmentStatus = typeof AssessmentStatus[keyof typeof AssessmentStatus];

export const ProtectionLevel = {
  NONE: 'none',
  BASIC: 'basic',
  FULL: 'full',
} as const;

export type ProtectionLevel = typeof ProtectionLevel[keyof typeof ProtectionLevel];

export const ReportStatus = {
  DRAFT: 'draft',
  DELETED: 'deleted',
  FORMED: 'formed',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
} as const;

export type ReportStatus = typeof ReportStatus[keyof typeof ReportStatus];

export interface VulnerabilityAssessment {
  id: number;
  title: string;
  short_description?: string;
  description: string;
  price: string | number;
  impact_level: number;
  assessment_type: VulnerabilityAssessmentType;
  status: AssessmentStatus;
  image_url?: string;
}

export interface AssessmentBasketInfo {
  report_id: number;
  item_count: number;
}

export interface DraftReportStatusInfo {
  is_active: boolean;
  item_count: number;
}

export interface AssessmentComponent {
  vulnerability_assessment: VulnerabilityAssessment;
  protection_level: ProtectionLevel;
  comment?: string;
  price_at_order_time: string | number;
}

export interface AssessmentReportSummary {
  id: number;
  status: ReportStatus;
  formation_date?: string;
  risk_score?: number;
  creator_login: string;
}

export interface AssessmentReportDetails {
  id: number;
  status: ReportStatus;
  created_at: string;
  creator_login: string;
  created_by: number;
  moderator_login?: string;
  formation_date?: string;
  completion_date?: string;
  target_system_info?: string;
  risk_score?: number;
  components: AssessmentComponent[];
}

export interface User {
  id: number;
  login: string;
  is_moderator: boolean;
}
