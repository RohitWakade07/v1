import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { Eye, Loader2, Save, Send } from 'lucide-react'
import { PageWrapper } from '@/components/shared/PageWrapper'
import { PageHeader } from '@/components/shared/PageHeader'
import { createAssignmentSchema } from '@/lib/schemas'
import { useCreateAssignment } from '@/hooks/mentor/useCreateAssignment'
import { usePublishAssignment } from '@/hooks/mentor/usePublishAssignment'
import { useNotificationStore } from '@/store/notificationStore'
import { Globe, Lock } from 'lucide-react'

type CreateFormValues = z.infer<typeof createAssignmentSchema>

const generateSlug = (title: string) => {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)+/g, '')
}

export const CreateAssignmentPage = () => {
  const navigate = useNavigate()
  const createMutation = useCreateAssignment()
  const publishMutation = usePublishAssignment()
  const addNotification = useNotificationStore((s) => s.addNotification)

  const {
    register,
    handleSubmit,
    control,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<CreateFormValues>({
    resolver: zodResolver(createAssignmentSchema),
    defaultValues: {
      title: '',
      slug: '',
      description: '',
      category: 'artifact_validation',
      max_score: 100,
      deadline: '',
      publish_immediately: false,
    },
  })

  const formValues = useWatch({ control })
  const [isAutoSlug, setIsAutoSlug] = useState(true)

  // Auto-generate slug from title
  useEffect(() => {
    if (isAutoSlug && formValues.title !== undefined) {
      setValue('slug', generateSlug(formValues.title), { shouldValidate: true })
    }
  }, [formValues.title, isAutoSlug, setValue])

  const onSubmit = async (data: CreateFormValues) => {
    try {
      // 1. Create Draft
      const newAssignment = await createMutation.mutateAsync({
        title: data.title,
        slug: data.slug,
        description: data.description,
        category: data.category,
        max_score: data.max_score,
        deadline: data.deadline || undefined,
      })

      // 2. Publish if toggled
      if (data.publish_immediately) {
        await publishMutation.mutateAsync(newAssignment.id)
      } else {
        addNotification({
          type: 'success',
          title: 'Draft created',
          message: 'Assignment saved as draft successfully.',
        })
      }

      // 3. Navigate to detail
      navigate(`/assignments/${newAssignment.id}`)
    } catch (error: unknown) {
      // Errors handled by API client globally, but we could set form errors here if it's a 422
      const err = error as { response?: { status?: number } };
      if (err?.response?.status === 409) {
        // Slug conflict
      }
    }
  }

  const isSaving = isSubmitting || createMutation.isPending || publishMutation.isPending

  return (
    <PageWrapper>
      <PageHeader
        title="Create Assignment"
        description="Configure a new assignment. You can save it as a draft or publish it immediately."
        backTo="/assignments"
        backLabel="Back to Assignments"
      />

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <div className="card-dark p-6">
            <form id="create-assignment-form" onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              
              <div className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-text-primary" htmlFor="title">
                    Assignment Title <span className="text-status-danger">*</span>
                  </label>
                  <input
                    id="title"
                    type="text"
                    className="input-dark"
                    placeholder="e.g. React Fundamentals Lab"
                    {...register('title')}
                  />
                  {errors.title && <p className="mt-1 text-xs text-status-danger">{errors.title.message}</p>}
                </div>

                <div>
                  <label className="mb-1.5 flex items-center justify-between text-sm font-medium text-text-primary" htmlFor="slug">
                    <span>URL Slug <span className="text-status-danger">*</span></span>
                    <button 
                      type="button" 
                      onClick={() => setIsAutoSlug(!isAutoSlug)}
                      className="text-xs text-accent-blue hover:underline"
                    >
                      {isAutoSlug ? 'Manual edit' : 'Auto-generate'}
                    </button>
                  </label>
                  <div className="flex items-center gap-2">
                    <span className="text-text-secondary bg-navy-950 px-3 py-2 rounded-lg border border-navy-800 font-mono text-sm hidden sm:block">
                      /assignments/
                    </span>
                    <input
                      id="slug"
                      type="text"
                      className="input-dark font-mono flex-1"
                      placeholder="react-fundamentals-lab"
                      disabled={isAutoSlug}
                      {...register('slug')}
                      onChange={(e) => {
                        setIsAutoSlug(false)
                        setValue('slug', e.target.value, { shouldValidate: true })
                      }}
                    />
                  </div>
                  {errors.slug && <p className="mt-1 text-xs text-status-danger">{errors.slug.message}</p>}
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-text-primary" htmlFor="description">
                    Description
                  </label>
                  <textarea
                    id="description"
                    className="input-dark min-h-[120px] resize-y"
                    placeholder="Provide instructions and context for this assignment..."
                    {...register('description')}
                  />
                  <div className="mt-1 flex justify-between">
                    {errors.description ? (
                      <p className="text-xs text-status-danger">{errors.description.message}</p>
                    ) : <span />}
                    <span className="text-xs text-text-secondary">
                      {(formValues.description || '').length} / 2000
                    </span>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-text-primary" htmlFor="category">
                      Category <span className="text-status-danger">*</span>
                    </label>
                    <select id="category" className="input-dark" {...register('category')}>
                      <option value="artifact_validation">Artifact Validation</option>
                      <option value="deterministic_execution">Deterministic Execution</option>
                      <option value="filesystem_validation">Filesystem Validation</option>
                      <option value="git_validation">Git Validation</option>
                      <option value="network_validation">Network Validation</option>
                      <option value="documentation_review">Documentation Review</option>
                      <option value="manual_review">Manual Review</option>
                    </select>
                    {errors.category && <p className="mt-1 text-xs text-status-danger">{errors.category.message}</p>}
                  </div>

                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-text-primary" htmlFor="max_score">
                      Max Score <span className="text-status-danger">*</span>
                    </label>
                    <input
                      id="max_score"
                      type="number"
                      className="input-dark"
                      {...register('max_score', { valueAsNumber: true })}
                    />
                    {errors.max_score && <p className="mt-1 text-xs text-status-danger">{errors.max_score.message}</p>}
                  </div>
                </div>

                <div>
                  <label className="mb-1.5 block text-sm font-medium text-text-primary" htmlFor="deadline">
                    Deadline (Optional)
                  </label>
                  <input
                    id="deadline"
                    type="datetime-local"
                    className="input-dark"
                    {...register('deadline')}
                  />
                  {errors.deadline && <p className="mt-1 text-xs text-status-warning">{errors.deadline.message}</p>}
                </div>

                <div className="mt-4 rounded-lg border border-navy-800 bg-navy-950 p-4">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-navy-800 bg-navy-900 text-accent-teal focus:ring-accent-teal"
                      {...register('publish_immediately')}
                    />
                    <div>
                      <p className="text-sm font-medium text-text-primary">Publish Immediately</p>
                      <p className="text-xs text-text-secondary">Make this assignment visible to students right away.</p>
                    </div>
                  </label>
                </div>
              </div>

              <div className="mt-8 flex items-center justify-end gap-3 border-t border-navy-800 pt-5">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => navigate(-1)}
                  disabled={isSaving}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  form="create-assignment-form"
                  className={formValues.publish_immediately ? "btn-primary bg-accent-teal hover:bg-[#159e82]" : "btn-primary"}
                  disabled={isSaving}
                >
                  {isSaving ? (
                    <><Loader2 size={16} className="animate-spin" /> Saving...</>
                  ) : formValues.publish_immediately ? (
                    <><Send size={16} /> Save & Publish</>
                  ) : (
                    <><Save size={16} /> Save as Draft</>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* Live Preview Panel */}
        <div className="lg:col-span-2">
          <div className="sticky top-6">
            <div className="mb-4 flex items-center gap-2">
              <Eye size={18} className="text-text-secondary" />
              <h3 className="font-display text-base font-semibold text-text-primary">Student Preview</h3>
            </div>
            
            <div className="card-dark overflow-hidden transition-all duration-300">
              <div className="border-b border-navy-800 bg-navy-900/50 p-5">
                <div className="mb-2 flex items-center justify-between">
                  <span className="rounded-full bg-navy-800 px-2 py-0.5 text-xs font-medium text-text-secondary">
                    {(formValues.category || 'artifact_validation').replace('_', ' ')}
                  </span>
                  {formValues.publish_immediately ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-accent-teal">
                      <Globe size={12} /> Published
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-status-warning">
                      <Lock size={12} /> Draft
                    </span>
                  )}
                </div>
                <h4 className="font-display text-xl font-bold text-text-primary break-words">
                  {formValues.title || 'Assignment Title'}
                </h4>
                <div className="mt-3 flex items-center gap-4 text-sm text-text-secondary">
                  <span>Max Score: <strong className="text-text-primary">{formValues.max_score || 0}</strong></span>
                  {formValues.deadline && (
                    <span>Due: <strong className="text-text-primary">{new Date(formValues.deadline).toLocaleDateString()}</strong></span>
                  )}
                </div>
              </div>
              <div className="p-5">
                <p className="text-sm text-text-secondary whitespace-pre-wrap break-words">
                  {formValues.description || 'Assignment description will appear here...'}
                </p>
                <div className="mt-6 flex w-full justify-end">
                  <div className="rounded bg-accent-blue/50 px-4 py-2 text-sm font-medium text-white opacity-50">
                    Start Session
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}

export default CreateAssignmentPage
