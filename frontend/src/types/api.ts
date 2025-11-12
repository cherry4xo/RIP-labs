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
