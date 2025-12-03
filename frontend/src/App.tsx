// src/App.tsx
import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Home } from './pages/Home';
import { ServicesList } from './pages/ServicesList';
import { ServiceDetail } from './pages/ServiceDetail';
import { ReportsList } from './pages/ReportsList';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Profile } from './pages/Profile';
import { Cart } from './pages/Cart';
import { MyReports } from './pages/MyReports';
import { useAppDispatch, useAppSelector } from './store/hooks';
import { loadUser } from './store/authSlice';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/global.css';

function App() {
  const dispatch = useAppDispatch();
  const { token } = useAppSelector((state) => state.auth);

  // Загружаем пользователя при старте приложения, если есть токен
  useEffect(() => {
    if (token) {
      dispatch(loadUser());
    }
  }, [dispatch, token]);

  // Проверяем, запущено ли приложение в Tauri
  // @ts-ignore
  const isTauri = typeof window !== 'undefined' && window.__TAURI__;

  // Для Tauri всегда используем '/', для веб - '/RIP-frontend/' в production
  const basename = import.meta.env.MODE === 'production' && !isTauri ? '/RIP-frontend/' : '/';

  console.log('App initialized:', {
    mode: import.meta.env.MODE,
    isTauri,
    basename,
    hasTauriGlobal: typeof window !== 'undefined' && 'window.__TAURI__' in window
  });

  return (
    <BrowserRouter basename={basename}>
      <Routes>
        <Route path="/" element={<Layout showBreadcrumbs={false} />}>
          <Route index element={<Home />} />
        </Route>

        <Route path="/" element={<Layout showBreadcrumbs={true} />}>
          <Route path="services" element={<ServicesList />} />
          <Route path="services/:id" element={<ServiceDetail />} />
          <Route path="reports" element={<ReportsList />} />
          <Route path="my-reports" element={<MyReports />} />
          <Route path="cart" element={<Cart />} />
          <Route path="profile" element={<Profile />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
        </Route>

        {/* Redirect any unknown routes to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
