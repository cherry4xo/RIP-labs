// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Home } from './pages/Home';
import { ServicesList } from './pages/ServicesList';
import { ServiceDetail } from './pages/ServiceDetail';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/global.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout showBreadcrumbs={false} />}>
          <Route index element={<Home />} />
        </Route>

        <Route path="/" element={<Layout showBreadcrumbs={true} />}>
          <Route path="services" element={<ServicesList />} />
          <Route path="services/:id" element={<ServiceDetail />} />
        </Route>

        {/* Redirect any unknown routes to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
