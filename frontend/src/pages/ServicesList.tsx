// src/pages/ServicesList.tsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Row, Col, Card, Form, Button, InputGroup } from 'react-bootstrap';
import type { VulnerabilityAssessment, VulnerabilityAssessmentType } from '../types/api';
import { VulnerabilityAssessmentType as VulnType } from '../types/api';
import { getVulnerabilityAssessments } from '../services/api';
import './ServicesList.css';

const ASSESSMENT_TYPE_LABELS: Record<VulnerabilityAssessmentType, string> = {
  [VulnType.NETWORK_SCAN]: 'Сетевое сканирование',
  [VulnType.WEB_APP_PENTEST]: 'Тестирование веб-приложений',
  [VulnType.INFRASTRUCTURE_AUDIT]: 'Аудит инфраструктуры',
};

export function ServicesList() {
  const [services, setServices] = useState<VulnerabilityAssessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Состояния фильтров
  const [titleFilter, setTitleFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState<VulnerabilityAssessmentType | ''>('');
  const [minPriceFilter, setMinPriceFilter] = useState('');
  const [maxPriceFilter, setMaxPriceFilter] = useState('');

  // Загрузка данных при изменении фильтров
  useEffect(() => {
    loadServices();
  }, [titleFilter, typeFilter, minPriceFilter, maxPriceFilter]);

  async function loadServices() {
    setLoading(true);
    setError(null);

    try {
      const params: any = {};
      if (titleFilter) params.title = titleFilter;
      if (typeFilter) params.assessment_type = typeFilter;
      if (minPriceFilter) params.min_price = Number(minPriceFilter);
      if (maxPriceFilter) params.max_price = Number(maxPriceFilter);

      const data = await getVulnerabilityAssessments(params);
      setServices(data);
    } catch (err) {
      setError('Не удалось загрузить список услуг');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    loadServices();
  }

  function formatPrice(price: string | number): string {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(Number(price));
  }

  return (
    <div className="services-list-page">
      <div className="hero-section">
        <h1 className="page-title">Виды анализа</h1>
      </div>

      {/* Фильтры */}
      <Form onSubmit={handleSearchSubmit} className="filters-section">
        <Row className="g-3">
          <Col md={6}>
            <Form.Label className="text-secondary">Поиск по названию</Form.Label>
            <InputGroup>
              <Form.Control
                type="text"
                placeholder="Поиск по наименованию..."
                value={titleFilter}
                onChange={(e) => setTitleFilter(e.target.value)}
                className="form-control"
              />
            </InputGroup>
          </Col>

          <Col md={6}>
            <Form.Label className="text-secondary">Тип анализа</Form.Label>
            <Form.Select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as VulnerabilityAssessmentType | '')}
              className="form-select"
            >
              <option value="">Все типы анализа</option>
              {Object.entries(ASSESSMENT_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Form.Select>
          </Col>

          <Col md={5}>
            <Form.Label className="text-secondary">Минимальная цена (₽)</Form.Label>
            <Form.Control
              type="number"
              placeholder="От"
              value={minPriceFilter}
              onChange={(e) => setMinPriceFilter(e.target.value)}
              className="form-control"
              min="0"
            />
          </Col>

          <Col md={5}>
            <Form.Label className="text-secondary">Максимальная цена (₽)</Form.Label>
            <Form.Control
              type="number"
              placeholder="До"
              value={maxPriceFilter}
              onChange={(e) => setMaxPriceFilter(e.target.value)}
              className="form-control"
              min="0"
            />
          </Col>

          <Col md={2} className="d-flex align-items-end">
            <Button type="submit" className="btn-primary w-100">
              Применить
            </Button>
          </Col>
        </Row>
      </Form>

      {/* Список услуг */}
      {loading ? (
        <div className="text-center py-5">
          <div className="text-secondary">Загрузка...</div>
        </div>
      ) : error ? (
        <div className="text-center py-5">
          <div className="text-danger">{error}</div>
        </div>
      ) : services.length === 0 ? (
        <div className="text-center py-5">
          <div className="text-secondary">Услуги не найдены</div>
        </div>
      ) : (
        <Row xs={1} md={2} lg={3} className="g-4 services-grid">
          {services.map((service) => (
            <Col key={service.id}>
              <Link to={`/services/${service.id}`} className="service-card-link">
                <Card className="service-card h-100">
                  <div className="service-card-image">
                    <Card.Img
                      variant="top"
                      src={service.image_url || '/images/services/placeholder.png'}
                      alt={service.title}
                    />
                  </div>
                  <Card.Body className="d-flex flex-column">
                    <Card.Title>{service.title}</Card.Title>
                    {service.short_description && (
                      <Card.Text className="text-secondary">
                        {service.short_description}
                      </Card.Text>
                    )}
                    <div className="mt-auto">
                      <div className="price">{formatPrice(service.price)}</div>
                      <div className="service-meta">
                        <span className="badge">{ASSESSMENT_TYPE_LABELS[service.assessment_type]}</span>
                        <span className="impact-level">Уровень: {service.impact_level}</span>
                      </div>
                    </div>
                  </Card.Body>
                </Card>
              </Link>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
}
