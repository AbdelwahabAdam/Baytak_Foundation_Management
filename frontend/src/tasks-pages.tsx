import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CirclePlus, ListTodo } from 'lucide-react'
import { useState } from 'react'

import { api } from './api'
import { useAuth } from './auth'
import { EmptyState, PageHeader } from './components/AppShell'
import type { PageResponse, Task, User } from './types'

function date(value: string | null | undefined) {
  if (!value) return '—'
  const locale = document.documentElement.lang === 'ar' ? 'ar-EG' : 'en-EG'
  return new Date(value).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short' })
}

function Status({ value }: { value: string }) {
  return <span className={`status-pill status-${value.replaceAll('_', '-')}`}>{value.replaceAll('_', ' ')}</span>
}

function ErrorNotice({ error }: { error: unknown }) {
  if (!error) return null
  const message = error instanceof Error ? error.message : 'Something went wrong'
  return <p className="form-error">{message}</p>
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="modal-card" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button type="button" className="icon-button" aria-label="Close" onClick={onClose}>×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

function PageLoading() {
  return <p className="muted">Loading…</p>
}

const STATUS_OPTIONS = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
]

export function TasksPage() {
  const { user, hasRole } = useAuth()
  const isAdmin = hasRole('admin')
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [filters, setFilters] = useState({
    assignedUserId: '',
    status: '',
    search: '',
    startDate: '',
    endDate: '',
  })

  const query = new URLSearchParams({ page_size: '100' })
  if (filters.assignedUserId) query.set('assigned_user_id', filters.assignedUserId)
  if (filters.status) query.set('status', filters.status)
  if (filters.search) query.set('search', filters.search)
  if (filters.startDate) query.set('start_date', `${filters.startDate}T00:00:00Z`)
  if (filters.endDate) query.set('end_date', `${filters.endDate}T23:59:59Z`)

  const tasks = useQuery({
    queryKey: ['tasks', filters],
    queryFn: () => api<PageResponse<Task>>(`/tasks?${query.toString()}`),
  })
  const users = useQuery({
    queryKey: ['users-for-tasks'],
    queryFn: () => api<User[]>('/users?active_only=true'),
    enabled: isAdmin,
  })

  const saveTask = useMutation({
    mutationFn: ({ taskId, payload }: { taskId?: number; payload: unknown }) =>
      taskId
        ? api<Task>(`/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify(payload) })
        : api<Task>('/tasks', { method: 'POST', body: JSON.stringify(payload) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      setShowForm(false)
      setEditingTask(null)
    },
  })

  const updateStatus = useMutation({
    mutationFn: ({ taskId, status }: { taskId: number; status: string }) =>
      api<Task>(`/tasks/${taskId}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })

  const cancelTask = useMutation({
    mutationFn: (id: number) => api(`/tasks/${id}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tasks'] }),
  })

  return (
    <>
      <PageHeader
        eyebrow="Work assignments"
        title="Tasks"
        description={
          isAdmin
            ? 'Assign work to users, filter by assignee or date range, and track progress.'
            : 'View your assigned tasks and update their status.'
        }
        action={
          isAdmin ? (
            <button
              className="button button-primary"
              onClick={() => {
                setEditingTask(null)
                setShowForm(true)
              }}
            >
              <CirclePlus size={18} /> Assign task
            </button>
          ) : undefined
        }
      />

      <section className="filter-panel">
        {isAdmin && (
          <label>
            Assigned user
            <select
              value={filters.assignedUserId}
              onChange={(event) => setFilters({ ...filters, assignedUserId: event.target.value })}
            >
              <option value="">All users</option>
              {users.data?.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.first_name} {item.last_name}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          Status
          <select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </label>
        <label>
          Search
          <input
            value={filters.search}
            onChange={(event) => setFilters({ ...filters, search: event.target.value })}
            placeholder="Title or description"
          />
        </label>
        <label>
          From
          <input
            type="date"
            value={filters.startDate}
            onChange={(event) => setFilters({ ...filters, startDate: event.target.value })}
          />
        </label>
        <label>
          To
          <input
            type="date"
            value={filters.endDate}
            onChange={(event) => setFilters({ ...filters, endDate: event.target.value })}
          />
        </label>
        <button
          className="text-button"
          type="button"
          onClick={() => setFilters({ assignedUserId: '', status: '', search: '', startDate: '', endDate: '' })}
        >
          Clear filters
        </button>
        <span>{tasks.data?.total ?? 0} tasks</span>
      </section>

      {tasks.isLoading ? (
        <PageLoading />
      ) : tasks.error ? (
        <ErrorNotice error={tasks.error} />
      ) : tasks.data?.items.length ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                {isAdmin && <th>Assigned to</th>}
                <th>Priority</th>
                <th>Due</th>
                <th>Created</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {tasks.data.items.map((item) => {
                const canChangeStatus = isAdmin || item.assigned_user_id === user?.id
                return (
                  <tr key={item.id}>
                    <td>
                      <strong>{item.title}</strong>
                      {item.description ? <small className="table-description">{item.description}</small> : null}
                    </td>
                    {isAdmin && (
                      <td>
                        {item.assigned_user.first_name} {item.assigned_user.last_name}
                      </td>
                    )}
                    <td>{item.priority}</td>
                    <td>{date(item.due_date)}</td>
                    <td>{date(item.created_at)}</td>
                    <td>
                      {canChangeStatus ? (
                        <select
                          value={item.status}
                          disabled={updateStatus.isPending}
                          onChange={(event) =>
                            updateStatus.mutate({ taskId: item.id, status: event.target.value })
                          }
                          aria-label={`Status for ${item.title}`}
                        >
                          {STATUS_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>{option.label}</option>
                          ))}
                        </select>
                      ) : (
                        <Status value={item.status} />
                      )}
                    </td>
                    <td>
                      <div className="inline-actions">
                        {isAdmin && (
                          <>
                            <button
                              className="text-button"
                              onClick={() => {
                                setEditingTask(item)
                                setShowForm(true)
                              }}
                            >
                              Edit
                            </button>
                            {item.status !== 'cancelled' && item.status !== 'completed' && (
                              <button
                                className="text-button danger"
                                onClick={() => {
                                  if (window.confirm(`Cancel task “${item.title}”?`)) {
                                    cancelTask.mutate(item.id)
                                  }
                                }}
                              >
                                Cancel
                              </button>
                            )}
                          </>
                        )}
                        {!isAdmin && <span className="muted"><ListTodo size={14} /></span>}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title="No tasks found"
          message={isAdmin ? 'Assign a task to a user to get started.' : 'No tasks are assigned to you yet.'}
        />
      )}

      {showForm && isAdmin && (
        <Modal
          title={editingTask ? 'Edit task' : 'Assign task'}
          onClose={() => {
            setShowForm(false)
            setEditingTask(null)
          }}
        >
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault()
              const form = new FormData(event.currentTarget)
              const due = String(form.get('due_date') || '')
              saveTask.mutate({
                taskId: editingTask?.id,
                payload: {
                  title: form.get('title'),
                  description: form.get('description') || null,
                  status: form.get('status'),
                  priority: form.get('priority'),
                  assigned_user_id: Number(form.get('assigned_user_id')),
                  due_date: due ? new Date(due).toISOString() : null,
                },
              })
            }}
          >
            <label className="form-span-2">
              Title
              <input name="title" defaultValue={editingTask?.title ?? ''} required autoFocus />
            </label>
            <label className="form-span-2">
              Assign to
              <select name="assigned_user_id" defaultValue={editingTask?.assigned_user_id ?? ''} required>
                <option value="">Choose a user</option>
                {users.data?.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.first_name} {item.last_name} · {item.email}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Status
              <select name="status" defaultValue={editingTask?.status ?? 'pending'}>
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </label>
            <label>
              Priority
              <select name="priority" defaultValue={editingTask?.priority ?? 'medium'}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </label>
            <label className="form-span-2">
              Due date
              <input
                name="due_date"
                type="datetime-local"
                defaultValue={
                  editingTask?.due_date
                    ? new Date(editingTask.due_date).toISOString().slice(0, 16)
                    : ''
                }
              />
            </label>
            <label className="form-span-2">
              Description
              <textarea name="description" rows={4} defaultValue={editingTask?.description ?? ''} />
            </label>
            <ErrorNotice error={saveTask.error} />
            <div className="form-actions form-span-2">
              <button
                type="button"
                className="button button-secondary"
                onClick={() => {
                  setShowForm(false)
                  setEditingTask(null)
                }}
              >
                Cancel
              </button>
              <button className="button button-primary" disabled={saveTask.isPending}>
                {editingTask ? 'Save changes' : 'Assign task'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
