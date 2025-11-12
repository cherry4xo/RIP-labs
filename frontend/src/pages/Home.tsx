// src/pages/Home.tsx
import { Link } from 'react-router-dom';
import { Container, Row, Col, Button } from 'react-bootstrap';
import './Home.css';

export function Home() {
  return (
    <div className="home-page">
      <Container>
        <Row className="justify-content-center text-center">
          <Col lg={10}>
            <h1 className="home-title">
              Профессиональная оценка <br />
              <span className="text-highlight">уязвимостей</span>
            </h1>

            <p className="home-description">
              Мы предоставляем комплексные услуги по анализу безопасности вашей
              IT-инфраструктуры. Наша команда экспертов поможет выявить и устранить
              уязвимости, обеспечив надежную защиту ваших данных и систем.
            </p>

            <div className="home-features">
              <Row className="g-4">
                <Col md={4}>
                  <div className="feature-card">
                    <div className="feature-icon">🔍</div>
                    <h3>Глубокий анализ</h3>
                    <p>
                      Тщательное исследование всех компонентов системы с использованием
                      современных методик и инструментов
                    </p>
                  </div>
                </Col>

                <Col md={4}>
                  <div className="feature-card">
                    <div className="feature-icon">🛡️</div>
                    <h3>Надежная защита</h3>
                    <p>
                      Разработка индивидуальных рекомендаций по усилению безопасности
                      вашей инфраструктуры
                    </p>
                  </div>
                </Col>

                <Col md={4}>
                  <div className="feature-card">
                    <div className="feature-icon">📊</div>
                    <h3>Детальные отчеты</h3>
                    <p>
                      Подробная документация с описанием найденных уязвимостей и путей
                      их устранения
                    </p>
                  </div>
                </Col>
              </Row>
            </div>

            <div className="home-cta">
              <Link to="/services">
                <Button className="btn-primary btn-lg">
                  Посмотреть услуги
                </Button>
              </Link>
            </div>
          </Col>
        </Row>
      </Container>
    </div>
  );
}
