/**
 * Root application component with routing and layout.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import BatchOverviewPage from './pages/BatchOverviewPage';
import AnomalyResultsPage from './pages/AnomalyResultsPage';
import DriftResultsPage from './pages/DriftResultsPage';
import ComponentDetailPage from './pages/ComponentDetailPage';
import ModelMetricsPage from './pages/ModelMetricsPage';
import ReportPage from './pages/ReportPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <div className="app-main">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/batch" element={<BatchOverviewPage />} />
            <Route path="/anomaly" element={<AnomalyResultsPage />} />
            <Route path="/drift" element={<DriftResultsPage />} />
            <Route path="/component" element={<ComponentDetailPage />} />
            <Route path="/metrics" element={<ModelMetricsPage />} />
            <Route path="/report" element={<ReportPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
