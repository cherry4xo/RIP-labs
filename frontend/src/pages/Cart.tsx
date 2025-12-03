// src/pages/Cart.tsx
import { useEffect, useState } from 'react';
import { Container, Card, Table, Button, Form, Alert, Modal } from 'react-bootstrap';
import { useNavigate, Link } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import {
  fetchBasketInfo,
  removeFromCart,
  updateCartItem,
  submitCart,
  clearError,
} from '../store/cartSlice';
import { getReportDetails } from '../services/api';
import type { AssessmentReportDetails, ProtectionLevel } from '../types/api';
import './Cart.css';

export function Cart() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAppSelector((state) => state.auth);
  const { basketInfo, loading, error } = useAppSelector((state) => state.cart);

  const [cartDetails, setCartDetails] = useState<AssessmentReportDetails | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [targetSystem, setTargetSystem] = useState('');
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    dispatch(fetchBasketInfo());
  }, [dispatch, isAuthenticated, navigate]);

  useEffect(() => {
    const loadCartDetails = async () => {
      if (basketInfo && basketInfo.report_id !== -1 && token) {
        setLoadingDetails(true);
        try {
          const details = await getReportDetails(token, basketInfo.report_id);
          setCartDetails(details);
        } catch (err) {
          console.error('Error loading cart details:', err);
        } finally {
          setLoadingDetails(false);
        }
      }
    };

    loadCartDetails();
  }, [basketInfo, token]);

  const handleRemove = async (assessmentId: number) => {
    await dispatch(removeFromCart(assessmentId));
    // Перезагружаем детали корзины
    if (basketInfo && basketInfo.report_id !== -1 && token) {
      const details = await getReportDetails(token, basketInfo.report_id);
      setCartDetails(details);
    }
  };

  const handleUpdateProtection = async (
    assessmentId: number,
    protectionLevel: ProtectionLevel,
    comment?: string
  ) => {
    await dispatch(
      updateCartItem({
        assessmentId,
        data: { protection_level: protectionLevel, comment },
      })
    );
    // Перезагружаем детали корзины
    if (basketInfo && basketInfo.report_id !== -1 && token) {
      const details = await getReportDetails(token, basketInfo.report_id);
      setCartDetails(details);
    }
  };

  const handleSubmitCart = async () => {
    if (!targetSystem || targetSystem.length < 5) {
      alert('Введите информацию о целевой системе (минимум 5 символов)');
      return;
    }

    setSubmitting(true);
    const result = await dispatch(submitCart(targetSystem));

    if (submitCart.fulfilled.match(result)) {
      setShowSubmitModal(false);
      alert('Заявка успешно сформирована! Расчет risk_score начнется автоматически.');
      navigate('/my-reports');
    }
    setSubmitting(false);
  };

  const hasItems = basketInfo && basketInfo.report_id !== -1 && basketInfo.item_count > 0;

  if (loadingDetails) {
    return (
      <Container className="mt-4 text-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Загрузка...</span>
        </div>
      </Container>
    );
  }

  return (
    <Container className="cart-container mt-4">
      <h1 className="mb-4">Корзина (Черновик заявки)</h1>

      {error && (
        <Alert variant="danger" onClose={() => dispatch(clearError())} dismissible>
          {error}
        </Alert>
      )}

      {!hasItems ? (
        <Card>
          <Card.Body className="text-center py-5">
            <h4 className="text-muted mb-3">Корзина пуста</h4>
            <p className="text-muted mb-4">
              Добавьте услуги оценки уязвимостей в корзину, чтобы сформировать заявку
            </p>
            <Button as={Link} to="/services" variant="primary">
              Перейти к услугам
            </Button>
          </Card.Body>
        </Card>
      ) : (
        <>
          <Card className="mb-4">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5>Услуги в заявке ({basketInfo?.item_count})</h5>
                <Button
                  variant="success"
                  onClick={() => setShowSubmitModal(true)}
                  disabled={loading}
                >
                  Сформировать заявку
                </Button>
              </div>

              <Table responsive striped bordered hover>
                <thead>
                  <tr>
                    <th>Услуга</th>
                    <th>Тип</th>
                    <th>Уровень защиты</th>
                    <th>Комментарий</th>
                    <th>Цена</th>
                    <th>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {cartDetails?.components.map((component) => (
                    <tr key={component.vulnerability_assessment.id}>
                      <td>
                        <Link to={`/services/${component.vulnerability_assessment.id}`}>
                          {component.vulnerability_assessment.title}
                        </Link>
                      </td>
                      <td>{component.vulnerability_assessment.assessment_type}</td>
                      <td>
                        <Form.Select
                          size="sm"
                          value={component.protection_level}
                          onChange={(e) =>
                            handleUpdateProtection(
                              component.vulnerability_assessment.id,
                              e.target.value as ProtectionLevel,
                              component.comment
                            )
                          }
                          disabled={loading}
                        >
                          <option value="none">Нет</option>
                          <option value="basic">Базовая</option>
                          <option value="full">Полная</option>
                        </Form.Select>
                      </td>
                      <td>
                        <Form.Control
                          size="sm"
                          as="textarea"
                          rows={1}
                          value={component.comment || ''}
                          onChange={(e) =>
                            handleUpdateProtection(
                              component.vulnerability_assessment.id,
                              component.protection_level,
                              e.target.value
                            )
                          }
                          placeholder="Комментарий"
                          disabled={loading}
                        />
                      </td>
                      <td>{Number(component.price_at_order_time).toFixed(2)} ₽</td>
                      <td>
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() =>
                            handleRemove(component.vulnerability_assessment.id)
                          }
                          disabled={loading}
                        >
                          Удалить
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card.Body>
          </Card>
        </>
      )}

      {/* Модальное окно для подтверждения заявки */}
      <Modal show={showSubmitModal} onHide={() => setShowSubmitModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Формирование заявки</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group>
            <Form.Label>Информация о целевой системе</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              placeholder="Введите информацию о целевой системе (минимум 5 символов)"
              value={targetSystem}
              onChange={(e) => setTargetSystem(e.target.value)}
              disabled={submitting}
            />
            <Form.Text className="text-muted">
              Укажите название системы, версию, описание и другую необходимую информацию
            </Form.Text>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button
            variant="secondary"
            onClick={() => setShowSubmitModal(false)}
            disabled={submitting}
          >
            Отмена
          </Button>
          <Button variant="primary" onClick={handleSubmitCart} disabled={submitting}>
            {submitting ? (
              <>
                <span className="spinner-border spinner-border-sm me-2" />
                Формирование...
              </>
            ) : (
              'Сформировать'
            )}
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
}
