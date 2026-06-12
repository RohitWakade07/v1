import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { RoleGuard } from './RoleGuard'
import { useAuthStore } from '@/store/authStore'
import { StudentLayout } from '@/layouts/StudentLayout'
import { MentorLayout } from '@/layouts/MentorLayout'
import { AdminLayout } from '@/layouts/AdminLayout'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

// ── Auth pages (public) ────────────────────────────────────────────
const LoginPage    = lazy(() => import('@/pages/auth/LoginPage'))
const RegisterPage = lazy(() => import('@/pages/auth/RegisterPage'))

// ── Student pages ──────────────────────────────────────────────────
const StudentDashboard     = lazy(() => import('@/pages/student/DashboardPage'))
const StudentAssignments   = lazy(() => import('@/pages/student/AssignmentsPage'))
const StudentAssignmentDetail = lazy(() => import('@/pages/student/AssignmentDetailPage'))
const StudentSessions      = lazy(() => import('@/pages/student/SessionsPage'))
const StudentSessionDetail = lazy(() => import('@/pages/student/SessionDetailPage'))
const StudentSubmissionDetail = lazy(() => import('@/pages/student/SubmissionDetailPage'))
const StudentProofSubmit   = lazy(() => import('@/pages/student/ProofSubmitPage'))
const StudentResults       = lazy(() => import('@/pages/student/ResultsPage'))
const StudentResultDetail  = lazy(() => import('@/pages/student/ResultDetailPage'))
const StudentProfile       = lazy(() => import('@/pages/student/ProfilePage'))

// ── Mentor pages ───────────────────────────────────────────────────
const MentorDashboard    = lazy(() => import('@/pages/mentor/DashboardPage'))
const MentorProfile      = lazy(() => import('@/pages/mentor/ProfilePage'))
const MentorClassrooms   = lazy(() => import('@/pages/mentor/classrooms/ClassroomsPage'))
const MentorAssignments  = lazy(() => import('@/pages/mentor/assignments/AssignmentsPage'))
const MentorManageAssignments = lazy(() => import('@/pages/mentor/assignments/AssignmentManagePage'))
const MentorCreateAssignment = lazy(() => import('@/pages/mentor/assignments/CreateAssignmentPage'))
const MentorAssignmentDetail = lazy(() => import('@/pages/mentor/assignments/AssignmentDetailPage'))
const MentorStudents     = lazy(() => import('@/pages/mentor/students/StudentsPage'))
const MentorSessions     = lazy(() => import('@/pages/mentor/sessions/SessionsPage'))
const MentorSubmissions  = lazy(() => import('@/pages/mentor/submissions/SubmissionsPage'))
const MentorResults      = lazy(() => import('@/pages/mentor/results/ResultsPage'))
const MentorAnalytics    = lazy(() => import('@/pages/mentor/analytics/AnalyticsPage'))
const MentorEvaluators   = lazy(() => import('@/pages/mentor/evaluators/EvaluatorsPage'))
const MentorCertificates = lazy(() => import('@/pages/mentor/certificates/CertificatesPage'))

// ── Admin pages ────────────────────────────────────────────────────
const AdminDashboard    = lazy(() => import('@/pages/admin/DashboardPage'))
const AdminStudents     = lazy(() => import('@/pages/admin/users/StudentsPage'))
const AdminMentors      = lazy(() => import('@/pages/admin/users/MentorsPage'))
const AdminAssignments  = lazy(() => import('@/pages/admin/assignments/AssignmentsPage'))
const AdminSessions     = lazy(() => import('@/pages/admin/sessions/SessionsPage'))
const AdminResults      = lazy(() => import('@/pages/admin/results/ResultsPage'))
const AdminHealth       = lazy(() => import('@/pages/admin/health/HealthPage'))

const Fallback = () => (
  <div className="flex h-screen items-center justify-center">
    <LoadingSpinner />
  </div>
)

/** Root redirect based on current auth role */
const RoleHome = () => {
  const role = useAuthStore((s) => s.role)
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (role === 'mentor') return <Navigate to="/mentor" replace />
  if (role === 'admin')  return <Navigate to="/admin" replace />
  return <Navigate to="/student" replace />
}

export const AppRouter = () => (
  <Suspense fallback={<Fallback />}>
    <Routes>
      {/* ── Root ────────────────────────────────────────────── */}
      <Route path="/" element={<RoleHome />} />

      {/* ── Public ──────────────────────────────────────────── */}
      <Route path="/login"    element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* ── Student routes ──────────────────────────────────── */}
      <Route element={<RoleGuard allowedRoles={['student']} />}>
        <Route path="/student" element={<StudentLayout />}>
          <Route index element={<StudentDashboard />} />
          <Route path="assignments"      element={<StudentAssignments />} />
          <Route path="assignments/:id"  element={<StudentAssignmentDetail />} />
          <Route path="sessions"         element={<StudentSessions />} />
          <Route path="sessions/:id"     element={<StudentSessionDetail />} />
          <Route path="submissions/:id"  element={<StudentSubmissionDetail />} />
          <Route path="proof/submit"     element={<StudentProofSubmit />} />
          <Route path="results"          element={<StudentResults />} />
          <Route path="results/:id"      element={<StudentResultDetail />} />
          <Route path="profile"          element={<StudentProfile />} />
        </Route>
      </Route>

      {/* ── Mentor routes ────────────────────────────────────── */}
      <Route element={<RoleGuard allowedRoles={['mentor', 'admin']} />}>
        <Route path="/mentor" element={<MentorLayout />}>
          <Route index element={<MentorDashboard />} />
          <Route path="profile"              element={<MentorProfile />} />
          <Route path="classrooms"           element={<MentorClassrooms />} />
          <Route path="assignments"          element={<MentorAssignments />} />
          <Route path="assignments/manage"   element={<MentorManageAssignments />} />
          <Route path="assignments/create"   element={<MentorCreateAssignment />} />
          <Route path="assignments/:id"      element={<MentorAssignmentDetail />} />
          <Route path="students"             element={<MentorStudents />} />
          <Route path="sessions"             element={<MentorSessions />} />
          <Route path="submissions"          element={<MentorSubmissions />} />
          <Route path="results"              element={<MentorResults />} />
          <Route path="analytics"            element={<MentorAnalytics />} />
          <Route path="evaluators"           element={<MentorEvaluators />} />
          <Route path="certificates"         element={<MentorCertificates />} />
        </Route>
      </Route>

      {/* ── Admin routes ─────────────────────────────────────── */}
      <Route element={<RoleGuard allowedRoles={['admin']} />}>
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="students"    element={<AdminStudents />} />
          <Route path="mentors"     element={<AdminMentors />} />
          <Route path="assignments" element={<AdminAssignments />} />
          <Route path="sessions"    element={<AdminSessions />} />
          <Route path="results"     element={<AdminResults />} />
          <Route path="health"      element={<AdminHealth />} />
        </Route>
      </Route>

      {/* ── Catch-all ────────────────────────────────────────── */}
      <Route path="*" element={<RoleHome />} />
    </Routes>
  </Suspense>
)
