// src/pages/Register.tsx
import { useState, useEffect } from 'react';
import { Container, Form, Button, Alert, Card } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { register, clearError } from '../store/authSlice';
import './Register.css';

export function Register() {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validationError, setValidationError] = useState('');
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { loading, error } = useAppSelector((state) => state.auth);

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');

    if (password !== confirmPassword) {
      setValidationError('Пароли не совпадают');
      return;
    }

    if (password.length < 4) {
      setValidationError('Пароль должен быть не менее 4 символов');
      return;
    }

    if (login.length < 3) {
      setValidationError('Логин должен быть не менее 3 символов');
      return;
    }

    const result = await dispatch(register({ login, password }));

    if (register.fulfilled.match(result)) {
      alert('Регистрация успешна! Теперь вы можете войти.');
      navigate('/login');
    }
  };

  return (
    <Container className="register-container mt-5">
      <div className="register-wrapper">
        <Card className="register-card">
          <Card.Body>
            <h2 className="text-center mb-4">Регистрация</h2>

            {(error || validationError) && (
              <Alert
                variant="danger"
                onClose={() => {
                  dispatch(clearError());
                  setValidationError('');
                }}
                dismissible
              >
                {error || validationError}
              </Alert>
            )}

            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3">
                <Form.Label>Логин</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Введите логин (минимум 3 символа)"
                  value={login}
                  onChange={(e) => setLogin(e.target.value)}
                  required
                  disabled={loading}
                  minLength={3}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Пароль</Form.Label>
                <Form.Control
                  type="password"
                  placeholder="Введите пароль (минимум 4 символа)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                  minLength={4}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Подтверждение пароля</Form.Label>
                <Form.Control
                  type="password"
                  placeholder="Повторите пароль"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={loading}
                />
              </Form.Group>

              <Button
                variant="primary"
                type="submit"
                className="w-100 mb-3"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" />
                    Регистрация...
                  </>
                ) : (
                  'Зарегистрироваться'
                )}
              </Button>

              <div className="text-center">
                <span className="text-muted">Уже есть аккаунт? </span>
                <Link to="/login">Войти</Link>
              </div>
            </Form>
          </Card.Body>
        </Card>
      </div>
    </Container>
  );
}
