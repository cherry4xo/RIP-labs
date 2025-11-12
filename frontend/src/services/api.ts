// src/services/api.ts
import type { VulnerabilityAssessment, VulnerabilityAssessmentType } from '../types/api';
import { mockAssessments } from './mockData';

interface GetAssessmentsParams {
  title?: string;
  assessment_type?: VulnerabilityAssessmentType;
  min_price?: number;
  max_price?: number;
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
    const url = `/api/vulnerabilities${queryString ? `?${queryString}` : ''}`;

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
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
    const response = await fetch(`/api/vulnerabilities/${id}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
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
