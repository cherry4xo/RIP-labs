// src/pages/ServiceDetail.tsx
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Row, Col, Button } from 'react-bootstrap';
import type { VulnerabilityAssessment, VulnerabilityAssessmentType } from '../types/api';
import { VulnerabilityAssessmentType as VulnType } from '../types/api';
import { getVulnerabilityAssessment } from '../services/api';
import './ServiceDetail.css';

const ASSESSMENT_TYPE_LABELS: Record<VulnerabilityAssessmentType, string> = {
  [VulnType.NETWORK_SCAN]: 'Сетевое сканирование',
  [VulnType.WEB_APP_PENTEST]: 'Тестирование веб-приложений',
  [VulnType.INFRASTRUCTURE_AUDIT]: 'Аудит инфраструктуры',
};

export function ServiceDetail() {
  const { id } = useParams<{ id: string }>();
  const [service, setService] = useState<VulnerabilityAssessment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadService(parseInt(id, 10));
    }
  }, [id]);

  async function loadService(serviceId: number) {
    setLoading(true);
    setError(null);

    try {
      const data = await getVulnerabilityAssessment(serviceId);
      setService(data);
    } catch (err) {
      setError('Не удалось загрузить информацию об услуге');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function formatPrice(price: string | number): string {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(Number(price));
  }

  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="text-secondary">Загрузка...</div>
      </div>
    );
  }

  if (error || !service) {
    return (
      <div className="text-center py-5">
        <div className="text-danger">{error || 'Услуга не найдена'}</div>
        <Link to="/services">
          <Button className="btn-primary mt-3">Вернуться к списку</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="service-detail-page">
      <h1 className="page-title">{service.title}</h1>

      <Row className="detail-container">
        <Col lg={6}>
          <div className="detail-image">
            <img
              src={service.image_url || '/images/services/placeholder.png'}
              alt={service.title}
            />
          </div>
        </Col>

        <Col lg={6}>
          <div className="detail-info">
            <div className="detail-meta">
              <span className="badge">
                {ASSESSMENT_TYPE_LABELS[service.assessment_type]}
              </span>
              <span className="impact-level">
                Уровень воздействия: {service.impact_level}/3
              </span>
            </div>

            <div className="detail-section">
              <h2>Описание</h2>
              <p>{service.description}</p>
            </div>

            <div className="detail-price-section">
              <div className="detail-price-label">Стоимость:</div>
              <div className="detail-price-value">{formatPrice(service.price)}</div>
            </div>

            <div className="detail-actions">
              <Link to="/services">
                <Button variant="outline" className="btn-outline">
                  Назад к списку
                </Button>
              </Link>
            </div>
          </div>
        </Col>
      </Row>
    </div>
  );
}
