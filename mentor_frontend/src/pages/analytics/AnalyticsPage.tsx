import { BarChart3, Users, CheckCircle, Brain, BookOpen } from 'lucide-react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { StatCard } from '@/components/dashboard/StatCard'
import { SkeletonStatCard } from '@/components/shared/SkeletonCard'
import { useMentorAnalytics } from '@/hooks/useMentor'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

export const AnalyticsPage = () => {
  const { data: analytics, isLoading } = useMentorAnalytics()

  const distributionData = analytics ? Object.entries(analytics.score_distribution).map(([range, count]) => ({
    name: range,
    students: count
  })) : []

  const categoryData = analytics ? Object.entries(analytics.category_breakdown).map(([category, count]) => ({
    name: category.replace('_', ' '),
    assignments: count
  })) : []

  return (
    <PageWrapper>
      <PageHeader
        title="Analytics"
        description="Educational insights across your assignments."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4 mb-6">
        {isLoading || !analytics ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonStatCard key={i} />)
        ) : (
          <>
            <StatCard
              title="Total Students"
              value={analytics.total_students}
              icon={<Users size={18} />}
              accent="blue"
              subtitle="Unique participants"
            />
            <StatCard
              title="Completion Rate"
              value={`${analytics.completion_rate.toFixed(1)}%`}
              icon={<CheckCircle size={18} />}
              accent="teal"
              subtitle="Of total sessions"
            />
            <StatCard
              title="Avg. Score"
              value={analytics.avg_score.toFixed(1)}
              icon={<Brain size={18} />}
              accent="blue"
              subtitle="Across all assignments"
            />
            <StatCard
              title="Total Submissions"
              value={analytics.total_submissions}
              icon={<BarChart3 size={18} />}
              accent="warning"
              subtitle="All time sessions"
            />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card-dark p-6">
          <h3 className="mb-6 font-display text-lg font-semibold text-text-primary">Score Distribution</h3>
          {isLoading ? (
            <div className="h-[300px] animate-pulse rounded-lg bg-navy-900" />
          ) : (
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={distributionData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#253545" vertical={false} />
                  <XAxis dataKey="name" stroke="#8CA0B3" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#8CA0B3" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    cursor={{ fill: '#253545', opacity: 0.4 }}
                    contentStyle={{ backgroundColor: '#0F1923', borderColor: '#253545', color: '#E8EDF2', borderRadius: '8px' }} 
                  />
                  <Bar dataKey="students" fill="#2E86C1" radius={[4, 4, 0, 0]} barSize={40} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="card-dark p-6">
          <h3 className="mb-6 font-display text-lg font-semibold text-text-primary">Categories Used</h3>
          {isLoading ? (
            <div className="h-[300px] animate-pulse rounded-lg bg-navy-900" />
          ) : categoryData.length > 0 ? (
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData} layout="vertical" margin={{ top: 10, right: 10, left: 20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#253545" horizontal={false} />
                  <XAxis type="number" stroke="#8CA0B3" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis dataKey="name" type="category" stroke="#8CA0B3" fontSize={12} tickLine={false} axisLine={false} width={120} />
                  <Tooltip 
                    cursor={{ fill: '#253545', opacity: 0.4 }}
                    contentStyle={{ backgroundColor: '#0F1923', borderColor: '#253545', color: '#E8EDF2', borderRadius: '8px' }} 
                  />
                  <Bar dataKey="assignments" fill="#1ABC9C" radius={[0, 4, 4, 0]} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex h-[300px] flex-col items-center justify-center text-text-secondary">
              <BookOpen size={48} className="mb-4 opacity-20" />
              <p>No category data available.</p>
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  )
}

export default AnalyticsPage
