// src/pages/ReportsList.tsx
import { useState, useEffect } from 'react';
import { Container, Table, Button, Form, Row, Col, Badge, Alert } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { getReports, completeReport, cancelReport } from '../services/api';
import type { AssessmentReportSummary, ReportStatus } from '../types/api';
import './ReportsList.css';

const POLLING_INTERVAL = 5000; // 5 секунд

export function ReportsList() {
  const [reports, setReports] = useState<AssessmentReportSummary[]>([]);
  const [filteredReports, setFilteredReports] = useState<AssessmentReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Фильтры бэкенда
  const [statusFilter, setStatusFilter] = useState<ReportStatus | ''>('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Фильтр фронтенда
  const [creatorFilter, setCreatorFilter] = useState('');

  const [isModerator, setIsModerator] = useState(false);
  const [token, setToken] = useState('');

  // Mock токен для демонстрации
  useEffect(() => {
    const mockToken = 'demo_moderator_token';
    setToken(mockToken);
    setIsModerator(true);
  }, []);

  // Функция загрузки отчетов
  const loadReports = async () => {
    try {
      setError(null);
      const params: {
        status?: ReportStatus;
        date_from?: string;
        date_to?: string;
      } = {};

      if (statusFilter) {
        params.status = statusFilter as ReportStatus;
      }
      if (dateFrom) {
        params.date_from = dateFrom;
      }
      if (dateTo) {
        params.date_to = dateTo;
      }

      const data = await getReports(token, params);
      setReports(data);
      setLoading(false);
    } catch (err) {
      console.error('Error loading reports:', err);
      setError('Не удалось загрузить список заявок');
      setLoading(false);
    }
  };

  // Первоначальная загрузка
  useEffect(() => {
    if (token) {
      loadReports();
    }
  }, [token, statusFilter, dateFrom, dateTo]);

  // Short polling - обновление каждые 5 секунд
  useEffect(() => {
    if (!token) return;

    const interval = setInterval(() => {
      loadReports();
    }, POLLING_INTERVAL);

    return () => clearInterval(interval);
  }, [token, statusFilter, dateFrom, dateTo]);

  // Фильтрация по создателю на фронтенде
  useEffect(() => {
    if (!creatorFilter) {
      setFilteredReports(reports);
      return;
    }

    const filtered = reports.filter(report =>
      report.creator_login.toLowerCase().includes(creatorFilter.toLowerCase())
    );
    setFilteredReports(filtered);
  }, [reports, creatorFilter]);

  const handleComplete = async (reportId: number) => {
    try {
      await completeReport(token, reportId);
      await loadReports();
    } catch (err) {
      console.error('Error completing report:', err);
      setError('Не удалось завершить заявку');
    }
  };

  const handleCancel = async (reportId: number) => {
    try {
      await cancelReport(token, reportId);
      await loadReports();
    } catch (err) {
      console.error('Error canceling report:', err);
      setError('Не удалось отклонить заявку');
    }
  };

  const getStatusBadge = (status: ReportStatus) => {
    const statusMap = {
      draft: { variant: 'secondary', text: 'Черновик' },
      formed: { variant: 'primary', text: 'Сформирована' },
      completed: { variant: 'success', text: 'Завершена' },
      cancelled: { variant: 'danger', text: 'Отклонена' },
      deleted: { variant: 'dark', text: 'Удалена' },
    };

    const { variant, text } = statusMap[status] || { variant: 'secondary', text: status };
    return <Badge bg={variant}>{text}</Badge>;
  };

  const getRiskScoreBadge = (riskScore: number | undefined) => {
    if (riskScore === undefined || riskScore === null) {
      return <Badge bg="secondary">Не рассчитан</Badge>;
    }

    if (riskScore <= 3) {
      return <Badge bg="success">{riskScore} (Низкий)</Badge>;
    } else if (riskScore <= 6) {
      return <Badge bg="warning">{riskScore} (Средний)</Badge>;
    } else {
      return <Badge bg="danger">{riskScore} (Высокий)</Badge>;
    }
  };

  if (loading) {
    return (
      <Container className="mt-4">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Загрузка...</span>
          </div>
        </div>
      </Container>
    );
  }

  return (
    <Container className="mt-4 reports-list">
      <h1 className="mb-4">Список заявок</h1>

      {error && (
        <Alert variant="danger" onClose={() => setError(null)} dismissible>
          {error}
        </Alert>
      )}

      {/* Фильтры */}
      <div className="filters-section mb-4 p-3 border rounded bg-light">
        <h5 className="mb-3">Фильтры</h5>

        <Row className="mb-3">
          <Col md={4}>
            <Form.Group>
              <Form.Label>Статус (бэкенд)</Form.Label>
              <Form.Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as ReportStatus | '')}
              >
                <option value="">Все статусы</option>
                <option value="draft">Черновик</option>
                <option value="formed">Сформирована</option>
                <option value="completed">Завершена</option>
                <option value="cancelled">Отклонена</option>
              </Form.Select>
            </Form.Group>
          </Col>

          <Col md={4}>
            <Form.Group>
              <Form.Label>Дата от (бэкенд)</Form.Label>
              <Form.Control
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </Form.Group>
          </Col>

          <Col md={4}>
            <Form.Group>
              <Form.Label>Дата до (бэкенд)</Form.Label>
              <Form.Control
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </Form.Group>
          </Col>
        </Row>

        <Row>
          <Col md={4}>
            <Form.Group>
              <Form.Label>Создатель (фронтенд)</Form.Label>
              <Form.Control
                type="text"
                placeholder="Логин создателя"
                value={creatorFilter}
                onChange={(e) => setCreatorFilter(e.target.value)}
              />
            </Form.Group>
          </Col>
        </Row>
      </div>

      {/* Таблица заявок */}
      <div className="table-responsive">
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>ID</th>
              <th>Статус</th>
              <th>Создатель</th>
              <th>Дата формирования</th>
              <th>Risk Score</th>
              {isModerator && <th>Действия</th>}
            </tr>
          </thead>
          <tbody>
            {filteredReports.length === 0 ? (
              <tr>
                <td colSpan={isModerator ? 6 : 5} className="text-center">
                  Заявки не найдены
                </td>
              </tr>
            ) : (
              filteredReports.map((report) => (
                <tr key={report.id}>
                  <td>
                    <Link to={`/reports/${report.id}`}>{report.id}</Link>
                  </td>
                  <td>{getStatusBadge(report.status)}</td>
                  <td>{report.creator_login}</td>
                  <td>
                    {report.formation_date
                      ? new Date(report.formation_date).toLocaleDateString('ru-RU')
                      : '—'}
                  </td>
                  <td>{getRiskScoreBadge(report.risk_score)}</td>
                  {isModerator && (
                    <td>
                      {report.status === 'formed' && (
                        <>
                          <Button
                            size="sm"
                            variant="success"
                            className="me-2"
                            onClick={() => handleComplete(report.id)}
                          >
                            Завершить
                          </Button>
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => handleCancel(report.id)}
                          >
                            Отклонить
                          </Button>
                        </>
                      )}
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </Table>
      </div>

      <div className="text-muted mt-3">
        <small>
          Обновление списка каждые {POLLING_INTERVAL / 1000} секунд (Short Polling)
        </small>
      </div>
    </Container>
  );
}
