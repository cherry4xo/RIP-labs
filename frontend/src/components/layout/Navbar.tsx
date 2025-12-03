// src/components/layout/Navbar.tsx
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Navbar as BSNavbar, Nav, Container, NavDropdown, Badge, Button } from 'react-bootstrap';
import { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { logout } from '../../store/authSlice';
import { fetchBasketInfo, clearCart } from '../../store/cartSlice';
import { resetFilters } from '../../store/filtersSlice';

export function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const baseUrl = import.meta.env.BASE_URL;
  const [expanded, setExpanded] = useState(false);

  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const { basketInfo } = useAppSelector((state) => state.cart);

  const handleToggle = () => setExpanded(!expanded);
  const handleNavClick = () => setExpanded(false);

  // Загружаем информацию о корзине при монтировании, если пользователь авторизован
  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchBasketInfo());
    }
  }, [dispatch, isAuthenticated]);

  const handleLogout = () => {
    dispatch(logout());
    dispatch(clearCart());
    dispatch(resetFilters());
    handleNavClick();
    navigate('/');
  };

  const cartItemCount = basketInfo?.item_count || 0;
  const hasCart = basketInfo && basketInfo.report_id !== -1 && cartItemCount > 0;

  return (
    <BSNavbar
      expanded={expanded}
      onToggle={handleToggle}
      className="py-4"
      expand="md"
    >
      <Container fluid className="main-container">
        <BSNavbar.Brand as={Link} to="/" className="d-flex align-items-center gap-3">
          <img
            src={`${baseUrl}logo.svg`}
            alt="Positive Technologies"
            height="28"
          />
          <span>Positive Tech</span>
        </BSNavbar.Brand>

        <BSNavbar.Toggle aria-controls="basic-navbar-nav" />

        <BSNavbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            <Nav.Link
              as={Link}
              to="/"
              className={location.pathname === '/' ? 'active' : ''}
              onClick={handleNavClick}
            >
              Главная
            </Nav.Link>
            <Nav.Link
              as={Link}
              to="/services"
              className={location.pathname.startsWith('/services') ? 'active' : ''}
              onClick={handleNavClick}
            >
              Услуги
            </Nav.Link>

            {/* Отображаем дополнительные ссылки только для авторизованных */}
            {isAuthenticated && (
              <>
                <Nav.Link
                  as={Link}
                  to="/my-reports"
                  className={location.pathname === '/my-reports' ? 'active' : ''}
                  onClick={handleNavClick}
                >
                  Мои заявки
                </Nav.Link>

                {user?.is_moderator && (
                  <Nav.Link
                    as={Link}
                    to="/reports"
                    className={location.pathname === '/reports' ? 'active' : ''}
                    onClick={handleNavClick}
                  >
                    Все заявки (Модератор)
                  </Nav.Link>
                )}

                <Nav.Link
                  as={Link}
                  to="/cart"
                  className={location.pathname === '/cart' ? 'active' : ''}
                  onClick={handleNavClick}
                  style={{ position: 'relative' }}
                >
                  Корзина
                  {hasCart && (
                    <Badge
                      bg="danger"
                      pill
                      style={{
                        position: 'absolute',
                        top: '5px',
                        right: '-10px',
                        fontSize: '0.7rem'
                      }}
                    >
                      {cartItemCount}
                    </Badge>
                  )}
                </Nav.Link>
              </>
            )}
          </Nav>

          {/* Кнопки входа/профиля */}
          <div className="ms-3 d-flex align-items-center gap-2">
            {isAuthenticated ? (
              <NavDropdown
                title={user?.login || 'Пользователь'}
                id="user-dropdown"
                align="end"
              >
                <NavDropdown.Item as={Link} to="/profile" onClick={handleNavClick}>
                  Профиль
                </NavDropdown.Item>
                <NavDropdown.Divider />
                <NavDropdown.Item onClick={handleLogout}>
                  Выйти
                </NavDropdown.Item>
              </NavDropdown>
            ) : (
              <>
                <Button
                  as={Link}
                  to="/login"
                  variant="outline-primary"
                  size="sm"
                  onClick={handleNavClick}
                >
                  Вход
                </Button>
                <Button
                  as={Link}
                  to="/register"
                  variant="primary"
                  size="sm"
                  onClick={handleNavClick}
                >
                  Регистрация
                </Button>
              </>
            )}

            <Link
              to="/"
              className="d-flex align-items-center"
              onClick={handleNavClick}
            >
              <img
                src={`${baseUrl}home.svg`}
                alt="Home"
                height="24"
                style={{ opacity: 0.8, transition: 'opacity 0.3s' }}
                onMouseEnter={e => e.currentTarget.style.opacity = '1'}
                onMouseLeave={e => e.currentTarget.style.opacity = '0.8'}
              />
            </Link>
          </div>
        </BSNavbar.Collapse>
      </Container>
    </BSNavbar>
  );
}
