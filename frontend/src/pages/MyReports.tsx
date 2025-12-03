// src/pages/MyReports.tsx
import { useState, useEffect } from 'react';
import { Container, Table, Badge, Alert } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAppSelector } from '../store/hooks';
import { getReports } from '../services/api';
import type { AssessmentReportSummary, ReportStatus } from '../types/api';
import './MyReports.css';

export function MyReports() {
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAppSelector((state) => state.auth);
  const [reports, setReports] = useState<AssessmentReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    loadReports();
  }, [isAuthenticated, navigate]);

  const loadReports = async () => {
    if (!token) return;

    try {
      setLoading(true);
      setError(null);
      const data = await getReports(token, {});
      setReports(data);
    } catch (err) {
      console.error('Error loading reports:', err);
      setError('Не удалось загрузить список заявок');
    } finally {
      setLoading(false);
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
      return <Badge bg="warning" text="dark">{riskScore} (Средний)</Badge>;
    } else {
      return <Badge bg="danger">{riskScore} (Высокий)</Badge>;
    }
  };

  if (loading) {
    return (
      <Container className="mt-4 text-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Загрузка...</span>
        </div>
      </Container>
    );
  }

  return (
    <Container className="my-reports-container mt-4">
      <h1 className="mb-4">Мои заявки</h1>

      {error && (
        <Alert variant="danger" onClose={() => setError(null)} dismissible>
          {error}
        </Alert>
      )}

      {reports.length === 0 ? (
        <Alert variant="info">
          <Alert.Heading>У вас пока нет заявок</Alert.Heading>
          <p>
            Перейдите в <Link to="/services">каталог услуг</Link>, добавьте нужные услуги в{' '}
            <Link to="/cart">корзину</Link> и сформируйте заявку.
          </p>
        </Alert>
      ) : (
        <div className="table-responsive">
          <Table striped bordered hover>
            <thead>
              <tr>
                <th>ID</th>
                <th>Статус</th>
                <th>Дата формирования</th>
                <th>Risk Score</th>
                <th>Создатель</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td>
                    <Link to={`/reports/${report.id}`}>{report.id}</Link>
                  </td>
                  <td>{getStatusBadge(report.status)}</td>
                  <td>
                    {report.formation_date
                      ? new Date(report.formation_date).toLocaleDateString('ru-RU', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })
                      : '—'}
                  </td>
                  <td>{getRiskScoreBadge(report.risk_score)}</td>
                  <td>{report.creator_login}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      )}
    </Container>
  );
}
