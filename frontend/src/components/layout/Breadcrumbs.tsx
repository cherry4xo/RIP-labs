// src/components/layout/Breadcrumbs.tsx
import { Link, useLocation } from 'react-router-dom';
import './Breadcrumbs.css';

interface BreadcrumbItem {
  label: string;
  path: string;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  const location = useLocation();

  // Если items не переданы, строим их автоматически из path
  const breadcrumbItems: BreadcrumbItem[] = items || generateBreadcrumbsFromPath(location.pathname);

  if (breadcrumbItems.length === 0) {
    return null;
  }

  return (
    <nav className="breadcrumbs" aria-label="breadcrumb">
      <ol className="breadcrumbs-list">
        {breadcrumbItems.map((item, index) => {
          const isLast = index === breadcrumbItems.length - 1;

          return (
            <li key={item.path} className={`breadcrumb-item ${isLast ? 'active' : ''}`}>
              {isLast ? (
                <span>{item.label}</span>
              ) : (
                <>
                  <Link to={item.path}>{item.label}</Link>
                  <span className="breadcrumb-separator">/</span>
                </>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function generateBreadcrumbsFromPath(pathname: string): BreadcrumbItem[] {
  const paths = pathname.split('/').filter(Boolean);

  if (paths.length === 0) {
    return [];
  }

  const breadcrumbs: BreadcrumbItem[] = [
    { label: 'Главная', path: '/' }
  ];

  let currentPath = '';
  paths.forEach((path, index) => {
    currentPath += `/${path}`;

    // Определяем label в зависимости от пути
    let label = path;
    if (path === 'services') {
      label = 'Услуги';
    } else if (/^\d+$/.test(path)) {
      label = 'Детали';
    }

    breadcrumbs.push({
      label: label.charAt(0).toUpperCase() + label.slice(1),
      path: currentPath
    });
  });

  return breadcrumbs;
}
