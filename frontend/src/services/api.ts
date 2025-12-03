// src/services/api.ts
import axios from 'axios';
import type {
  VulnerabilityAssessment,
  VulnerabilityAssessmentType,
  AssessmentReportSummary,
  AssessmentReportDetails,
  ReportStatus,
  DraftReportStatusInfo
} from '../types/api';
import { mockAssessments } from './mockData';
import { API_BASE_URL } from '../config/api.config';

interface GetAssessmentsParams {
  title?: string;
  assessment_type?: VulnerabilityAssessmentType;
  min_price?: number;
  max_price?: number;
}

interface GetReportsParams {
  status?: ReportStatus;
  date_from?: string;
  date_to?: string;
}

/**
 * Получение списка оценок уязвимостей с фильтрацией
 */
export async function getVulnerabilityAssessments(
  params: GetAssessmentsParams = {}
): Promise<VulnerabilityAssessment[]> {
  try {
    // Строим query параметры
    const queryParams = new URLSearchParams();
    if (params.title) {
      queryParams.append('title', params.title);
    }
    if (params.assessment_type) {
      queryParams.append('assessment_type', params.assessment_type);
    }
    if (params.min_price !== undefined) {
      queryParams.append('min_price', params.min_price.toString());
    }
    if (params.max_price !== undefined) {
      queryParams.append('max_price', params.max_price.toString());
    }

    const queryString = queryParams.toString();
    const url = `${API_BASE_URL}/vulnerabilities${queryString ? `?${queryString}` : ''}`;

    const response = await axios.get<VulnerabilityAssessment[]>(url);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch from API, using mock data:', error);

    // Fallback на mock данные
    let filtered = [...mockAssessments];

    if (params.title) {
      const searchLower = params.title.toLowerCase();
      filtered = filtered.filter(item =>
        item.title.toLowerCase().includes(searchLower) ||
        item.description.toLowerCase().includes(searchLower)
      );
    }

    if (params.assessment_type) {
      filtered = filtered.filter(item =>
        item.assessment_type === params.assessment_type
      );
    }

    if (params.min_price !== undefined) {
      filtered = filtered.filter(item =>
        Number(item.price) >= params.min_price!
      );
    }

    if (params.max_price !== undefined) {
      filtered = filtered.filter(item =>
        Number(item.price) <= params.max_price!
      );
    }

    return filtered;
  }
}

/**
 * Получение детальной информации об одной оценке уязвимости
 */
export async function getVulnerabilityAssessment(
  id: number
): Promise<VulnerabilityAssessment> {
  try {
    const response = await axios.get<VulnerabilityAssessment>(`${API_BASE_URL}/vulnerabilities/${id}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch from API, using mock data:', error);

    // Fallback на mock данные
    const item = mockAssessments.find(a => a.id === id);
    if (!item) {
      throw new Error(`Assessment with id ${id} not found`);
    }
    return item;
  }
}

/**
 * Получение списка отчетов с фильтрацией
 */
export async function getReports(
  token: string,
  params: GetReportsParams = {}
): Promise<AssessmentReportSummary[]> {
  const queryParams = new URLSearchParams();
  if (params.status) {
    queryParams.append('status', params.status);
  }
  if (params.date_from) {
    queryParams.append('date_from', params.date_from);
  }
  if (params.date_to) {
    queryParams.append('date_to', params.date_to);
  }

  const queryString = queryParams.toString();
  const url = `${API_BASE_URL}/reports${queryString ? `?${queryString}` : ''}`;

  const response = await axios.get<AssessmentReportSummary[]>(url, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
  return response.data;
}

/**
 * Получение детальной информации об отчете
 */
export async function getReportDetails(
  token: string,
  reportId: number
): Promise<AssessmentReportDetails> {
  const response = await axios.get<AssessmentReportDetails>(
    `${API_BASE_URL}/reports/${reportId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  );
  return response.data;
}

/**
 * Завершение отчета (модератором)
 */
export async function completeReport(
  token: string,
  reportId: number
): Promise<AssessmentReportDetails> {
  const response = await axios.put<AssessmentReportDetails>(
    `${API_BASE_URL}/reports/${reportId}/complete`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  );
  return response.data;
}

/**
 * Отклонение отчета (модератором)
 */
export async function cancelReport(
  token: string,
  reportId: number
): Promise<AssessmentReportDetails> {
  const response = await axios.put<AssessmentReportDetails>(
    `${API_BASE_URL}/reports/${reportId}/cancel`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  );
  return response.data;
}

/**
 * Получение статуса черновика отчета и количества услуг в корзине
 */
export async function getDraftReportStatus(
  token: string
): Promise<DraftReportStatusInfo> {
  const response = await axios.get<DraftReportStatusInfo>(
    `${API_BASE_URL}/report/draft/status`,
    {
      headers: {
        Authorization: `Bearer ${token}`
      }
    }
  );
  return response.data;
}
