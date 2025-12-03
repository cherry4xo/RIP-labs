// src/pages/Profile.tsx
import { useState, useEffect } from 'react';
import { Container, Card, Form, Button, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { updateProfile, clearError } from '../store/authSlice';
import './Profile.css';

export function Profile() {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { user, isAuthenticated, loading, error } = useAppSelector((state) => state.auth);

  const [login, setLogin] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (user) {
      setLogin(user.login);
    }
  }, [user]);

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMessage('');

    const result = await dispatch(updateProfile({ login }));

    if (updateProfile.fulfilled.match(result)) {
      setSuccessMessage('Профиль успешно обновлен!');
      setTimeout(() => setSuccessMessage(''), 3000);
    }
  };

  if (!user) {
    return null;
  }

  return (
    <Container className="profile-container mt-5">
      <div className="profile-wrapper">
        <Card className="profile-card">
          <Card.Body>
            <h2 className="text-center mb-4">Личный кабинет</h2>

            {error && (
              <Alert variant="danger" onClose={() => dispatch(clearError())} dismissible>
                {error}
              </Alert>
            )}

            {successMessage && (
              <Alert variant="success" onClose={() => setSuccessMessage('')} dismissible>
                {successMessage}
              </Alert>
            )}

            <div className="mb-4">
              <div className="mb-2">
                <strong>ID:</strong> {user.id}
              </div>
              <div className="mb-2">
                <strong>Роль:</strong>{' '}
                <span className={user.is_moderator ? 'text-success' : ''}>
                  {user.is_moderator ? 'Модератор' : 'Пользователь'}
                </span>
              </div>
            </div>

            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3">
                <Form.Label>Логин</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Введите логин"
                  value={login}
                  onChange={(e) => setLogin(e.target.value)}
                  required
                  disabled={loading}
                  minLength={3}
                />
                <Form.Text className="text-muted">
                  Минимум 3 символа
                </Form.Text>
              </Form.Group>

              <Button
                variant="primary"
                type="submit"
                className="w-100"
                disabled={loading || login === user.login}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" />
                    Сохранение...
                  </>
                ) : (
                  'Сохранить изменения'
                )}
              </Button>
            </Form>

            <hr className="my-4" />

            <div className="text-muted">
              <small>
                <strong>Примечание:</strong> Здесь вы можете изменить свой логин.
                В будущих версиях будет возможность смены пароля и других настроек.
              </small>
            </div>
          </Card.Body>
        </Card>
      </div>
    </Container>
  );
}
