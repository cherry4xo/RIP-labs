// src/components/layout/Layout.tsx
import { Outlet } from 'react-router-dom';
import { Navbar } from './Navbar';
import { Breadcrumbs } from './Breadcrumbs';
import { Container } from 'react-bootstrap';

interface LayoutProps {
  showBreadcrumbs?: boolean;
}

export function Layout({ showBreadcrumbs = true }: LayoutProps) {
  return (
    <div>
      <Container fluid className="main-container">
        <Navbar />
      </Container>

      <main>
        <Container fluid className="main-container">
          {showBreadcrumbs && <Breadcrumbs />}
          <Outlet />
        </Container>
      </main>
    </div>
  );
}
