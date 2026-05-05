import { BrowserRouter, Route, Routes } from 'react-router-dom';

import { AuthProvider } from './auth/AuthContext';
import AuthLayout from './components/AuthLayout';
import Layout from './components/Layout';
import AuthLandingPage from './pages/AuthLandingPage';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';
import ProfilePage from './pages/ProfilePage';
import ProjectsPage from './pages/ProjectsPage';
import ProjectPage from './pages/ProjectPage';
import RegisterPage from './pages/RegisterPage';
import SeniorPage from './pages/SeniorPage';
import ScrumLiveAgent from './components/ScrumLiveAgent';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AuthLayout />}>
            <Route path="/" element={<AuthLandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
          <Route element={<Layout />}>
            <Route path="/home" element={<HomePage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/:projectId" element={<ProjectPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/senior" element={<SeniorPage />} />
            <Route path="/scrum-live" element={<ScrumLiveAgent />} />
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
