import { Routes, Route, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { ProtectedRoute } from './ProtectedRoute'
import LoginPage from '@/pages/auth/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import AssignmentsPage from '@/pages/assignments/AssignmentsPage'
import CreateAssignmentPage from '@/pages/assignments/CreateAssignmentPage'
import AssignmentDetailPage from '@/pages/assignments/AssignmentDetailPage'
import ProfilePage from '@/pages/ProfilePage'

// Phase 2 Placeholders
import StudentsPage from '@/pages/students/StudentsPage'
import SessionsPage from '@/pages/sessions/SessionsPage'
import ResultsPage from '@/pages/results/ResultsPage'
import EvaluatorsPage from '@/pages/evaluators/EvaluatorsPage'
import CertificatesPage from '@/pages/certificates/CertificatesPage'
import AnalyticsPage from '@/pages/analytics/AnalyticsPage'

export const AppRouter = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />

          {/* Assignments Module */}
          <Route path="/assignments" element={<AssignmentsPage />} />
          <Route path="/assignments/create" element={<CreateAssignmentPage />} />
          <Route path="/assignments/:id" element={<AssignmentDetailPage />} />

          {/* Phase 2 Modules */}
          <Route path="/students" element={<StudentsPage />} />
          <Route path="/sessions" element={<SessionsPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/evaluators" element={<EvaluatorsPage />} />
          <Route path="/certificates" element={<CertificatesPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
