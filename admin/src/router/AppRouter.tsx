import { Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute } from './ProtectedRoute'
import { LoginPage } from '@/pages/auth/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { StudentsPage } from '@/pages/users/StudentsPage'
import { MentorsPage } from '@/pages/users/MentorsPage'
import { AssignmentsPage } from '@/pages/assignments/AssignmentsPage'
import { SessionsPage } from '@/pages/sessions/SessionsPage'
import { ResultsPage } from '@/pages/results/ResultsPage'
import { HealthPage } from '@/pages/health/HealthPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export const AppRouter = () => (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route
      path="/"
      element={
        <ProtectedRoute>
          <AppShell />
        </ProtectedRoute>
      }
    >
      <Route index element={<Navigate to="/dashboard" replace />} />
      <Route path="dashboard" element={<DashboardPage />} />
      <Route path="students" element={<StudentsPage />} />
      <Route path="mentors" element={<MentorsPage />} />
      <Route path="assignments" element={<AssignmentsPage />} />
      <Route path="sessions" element={<SessionsPage />} />
      <Route path="results" element={<ResultsPage />} />
      <Route path="health" element={<HealthPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Route>
  </Routes>
)
