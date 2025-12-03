// src/pages/Home.tsx
import { Container, Row, Col, Carousel } from 'react-bootstrap';
import './Home.css';

export function Home() {
  return (
    <div className="home-page">
      {/* Title Section */}
      <Container>
        <Row className="justify-content-center text-center">
          <Col lg={10}>
            <h1 className="home-title">
              Профессиональная оценка <br />
              <span className="text-highlight">уязвимостей</span>
            </h1>
          </Col>
        </Row>
      </Container>

      {/* Carousel Section */}
      <div className="home-carousel-section">
        <Carousel fade>
          <Carousel.Item>
            <div className="carousel-slide carousel-slide-1">
              <div className="carousel-overlay">
                <Container>
                  <div className="carousel-content">
                    <h2>Комплексная оценка безопасности</h2>
                    <p>Выявление уязвимостей на всех уровнях вашей инфраструктуры</p>
                  </div>
                </Container>
              </div>
            </div>
          </Carousel.Item>

          <Carousel.Item>
            <div className="carousel-slide carousel-slide-2">
              <div className="carousel-overlay">
                <Container>
                  <div className="carousel-content">
                    <h2>Пентестинг и аудит безопасности</h2>
                    <p>Комплексная проверка систем экспертами с многолетним опытом</p>
                  </div>
                </Container>
              </div>
            </div>
          </Carousel.Item>

          <Carousel.Item>
            <div className="carousel-slide carousel-slide-3">
              <div className="carousel-overlay">
                <Container>
                  <div className="carousel-content">
                    <h2>Детальные отчёты о безопасности</h2>
                    <p>Подробный анализ уязвимостей с рекомендациями по устранению</p>
                  </div>
                </Container>
              </div>
            </div>
          </Carousel.Item>
        </Carousel>
      </div>
    </div>
  );
}
