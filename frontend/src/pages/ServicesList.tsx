// src/pages/ServicesList.tsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Row, Col, Card, Form, Button, InputGroup } from 'react-bootstrap';
import type { VulnerabilityAssessment, VulnerabilityAssessmentType } from '../types/api';
import { VulnerabilityAssessmentType as VulnType } from '../types/api';
import { getVulnerabilityAssessments } from '../services/api';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { setSearchQuery, resetFilters, selectSearchQuery } from '../store/filtersSlice';
import { CartButton } from '../components/CartButton';
import './ServicesList.css';

const ASSESSMENT_TYPE_LABELS: Record<VulnerabilityAssessmentType, string> = {
  [VulnType.NETWORK_SCAN]: 'Сетевое сканирование',
  [VulnType.WEB_APP_PENTEST]: 'Тестирование веб-приложений',
  [VulnType.INFRASTRUCTURE_AUDIT]: 'Аудит инфраструктуры',
};

export function ServicesList() {
  const dispatch = useAppDispatch();
  const searchQuery = useAppSelector(selectSearchQuery);

  const [services, setServices] = useState<VulnerabilityAssessment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Загрузка данных только при монтировании компонента
  useEffect(() => {
    loadInitialServices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Начальная загрузка всех услуг без фильтров
  async function loadInitialServices() {
    setLoading(true);
    setError(null);

    try {
      const data = await getVulnerabilityAssessments({});
      setServices(data);
    } catch (err) {
      setError('Не удалось загрузить список услуг');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  // Загрузка услуг с применением фильтра
  async function loadServices() {
    setLoading(true);
    setError(null);

    try {
      const params: {
        title?: string;
      } = {};
      if (searchQuery) params.title = searchQuery;

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

  function handleResetFilters() {
    dispatch(resetFilters());
    // После сброса фильтров загружаем все услуги
    loadInitialServices();
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
        <div className="d-flex justify-content-between align-items-center">
          <h1 className="page-title">Виды анализа</h1>
          <CartButton />
        </div>
      </div>

      {/* Фильтры */}
      <Form onSubmit={handleSearchSubmit} className="filters-section">
        <Row className="g-3">
          <Col md={10}>
            <Form.Label className="text-secondary">Поиск по названию</Form.Label>
            <InputGroup>
              <Form.Control
                type="text"
                placeholder="Поиск по наименованию..."
                value={searchQuery}
                onChange={(e) => dispatch(setSearchQuery(e.target.value))}
                className="form-control"
              />
            </InputGroup>
          </Col>

          <Col md={2} className="d-flex align-items-end gap-2">
            <Button type="submit" className="btn-primary flex-grow-1">
              Поиск
            </Button>
            <Button
              type="button"
              className="btn-outline"
              onClick={handleResetFilters}
              title="Сбросить фильтры"
            >
              ✕
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
