import { useState } from 'react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { GlobalQueueView } from './GlobalQueueView'
import { ClassroomHierarchyView } from './ClassroomHierarchyView'

export const SubmissionsPage = () => {
  const [activeTab, setActiveTab] = useState<'HIERARCHY' | 'GLOBAL'>('HIERARCHY')

  return (
    <PageWrapper>
      <PageHeader
        title="Submissions"
        description="Monitor student progress and submission history."
      />

      <div className="flex space-x-6 border-b border-navy-700 mt-2">
        <button
          className={`pb-3 text-sm font-medium transition-colors relative ${
            activeTab === 'HIERARCHY'
              ? 'text-accent-teal'
              : 'text-text-secondary hover:text-text-primary'
          }`}
          onClick={() => setActiveTab('HIERARCHY')}
        >
          Classroom View
          {activeTab === 'HIERARCHY' && (
            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-accent-teal rounded-t-full" />
          )}
        </button>
        <button
          className={`pb-3 text-sm font-medium transition-colors relative ${
            activeTab === 'GLOBAL'
              ? 'text-accent-teal'
              : 'text-text-secondary hover:text-text-primary'
          }`}
          onClick={() => setActiveTab('GLOBAL')}
        >
          Global Queue
          {activeTab === 'GLOBAL' && (
            <span className="absolute bottom-0 left-0 w-full h-0.5 bg-accent-teal rounded-t-full" />
          )}
        </button>
      </div>

      {activeTab === 'HIERARCHY' ? <ClassroomHierarchyView /> : <GlobalQueueView />}
    </PageWrapper>
  )
}

export default SubmissionsPage
