import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  CirclePlus,
  FolderKanban,
  Pencil,
  Search,
} from 'lucide-react'
import { type FormEvent, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { api, ApiError } from './api'
import { useAuth } from './auth'
import { EmptyState, PageHeader } from './components/AppShell'
import { useLocale } from './localization'
import type {
  Activity,
  ActivitySummary,
  ActivityTransaction,
  Donation,
  PageResponse,
} from './types'

const copy = {
  ar: {
    loading: 'جارٍ التحميل…',
    close: 'إغلاق',
    cancel: 'إلغاء',
    create: 'إنشاء',
    saveChanges: 'حفظ التغييرات',
    somethingWrong: 'حدث خطأ ما',
    fundAccounting: 'المحاسبة حسب الصناديق',
    projects: 'المشروعات',
    projectsDesc: 'لكل مشروع دفتر حساب خاص. الأرصدة تُحسب ولا تُخزَّن.',
    projectsDescShort: 'المشروعات المالية ودفاتر حساباتها.',
    createActivity: 'إنشاء مشروع',
    editActivity: 'تعديل مشروع',
    searchActivities: 'ابحث في المشروعات',
    allStatuses: 'كل الحالات',
    active: 'نشط',
    inactive: 'غير نشط',
    activitiesCount: 'مشروعات',
    name: 'الاسم',
    status: 'الحالة',
    income: 'الدخل',
    expense: 'المصروف',
    balance: 'الرصيد',
    transactions: 'المعاملات',
    deactivate: 'إيقاف',
    noActivities: 'لا توجد مشروعات بعد',
    noActivitiesHint: 'أنشئ مشروعاً لبدء دفتر حساباته.',
    type: 'النوع',
    description: 'الوصف',
    overview: 'نظرة عامة',
    incomeTab: 'الدخل',
    expensesTab: 'المصروفات',
    transactionsTab: 'المعاملات',
    reportsTab: 'التقارير',
    settingsTab: 'الإعدادات',
    activityLedger: 'دفتر المشروع',
    backToList: 'العودة للقائمة',
    totalIncome: 'إجمالي الدخل',
    totalExpense: 'إجمالي المصروف',
    donations: 'التبرعات',
    sales: 'المبيعات',
    grants: 'المنح',
    expenses: 'المصروفات',
    recentTransactions: 'أحدث المعاملات',
    recentTransactionsHint: 'آخر قيود دفتر هذا المشروع.',
    date: 'التاريخ',
    direction: 'الاتجاه',
    amount: 'المبلغ',
    noTransactions: 'لا توجد معاملات',
    noTransactionsHint: 'أضف دخلاً أو مصروفات لبناء الدفتر.',
    incomeHint: 'تبرعات ومنح ومبيعات ودخل يدوي.',
    addIncome: 'إضافة دخل',
    expensesHint: 'مصروفات مباشرة للمشروع (مصروفات العُهد تُسجَّل عند الاعتماد).',
    addExpense: 'إضافة مصروف',
    unifiedLedger: 'دفتر الأستاذ الموحد',
    runningBalanceHint: 'يُحسب الرصيد الجاري من القيود حسب الترتيب الزمني.',
    runningBalance: 'الرصيد الجاري',
    incomeStatement: 'قائمة الدخل',
    incomeStatementHint: 'الدخل مقابل المصروفات لهذا المشروع.',
    totalExpenses: 'إجمالي المصروفات',
    netProfitLoss: 'صافي الربح / الخسارة',
    monthlySummary: 'الملخص الشهري',
    monthlySummaryHint: 'الدخل مقابل المصروف حسب الشهر.',
    noMonthlyData: 'لا توجد بيانات شهرية',
    noMonthlyHint: 'ستظهر المعاملات في هذا الرسم.',
    settings: 'الإعدادات',
    settingsHint: 'تحديث تفاصيل المشروع وحالته.',
    saveSettings: 'حفظ الإعدادات',
    incomeType: 'نوع الدخل',
    existingDonation: 'تبرع موجود',
    chooseDonation: 'اختر تبرعاً',
    saveIncome: 'حفظ الدخل',
    expenseType: 'نوع المصروف',
    saveExpense: 'حفظ المصروف',
    donationLink: 'تبرع (ربط موجود)',
    grant: 'منحة',
    sale: 'بيع',
    manualIncome: 'دخل يدوي',
    manualExpense: 'مصروف يدوي',
    purchase: 'مشتريات',
    salary: 'رواتب',
    maintenance: 'صيانة',
    utilities: 'مرافق',
    transportation: 'مواصلات',
    marketing: 'تسويق',
    other: 'أخرى',
    incomeDir: 'دخل',
    expenseDir: 'مصروف',
  },
  en: {
    loading: 'Loading…',
    close: 'Close',
    cancel: 'Cancel',
    create: 'Create',
    saveChanges: 'Save changes',
    somethingWrong: 'Something went wrong',
    fundAccounting: 'Fund accounting',
    projects: 'Activities',
    projectsDesc: 'Each project has its own ledger. Balances are calculated, never stored.',
    projectsDescShort: 'Financial projects and their ledgers.',
    createActivity: 'Create activity',
    editActivity: 'Edit activity',
    searchActivities: 'Search activities',
    allStatuses: 'All statuses',
    active: 'Active',
    inactive: 'Inactive',
    activitiesCount: 'activities',
    name: 'Name',
    status: 'Status',
    income: 'Income',
    expense: 'Expense',
    balance: 'Balance',
    transactions: 'Transactions',
    deactivate: 'Deactivate',
    noActivities: 'No activities yet',
    noActivitiesHint: 'Create a project to start its ledger.',
    type: 'Type',
    description: 'Description',
    overview: 'Overview',
    incomeTab: 'Income',
    expensesTab: 'Expenses',
    transactionsTab: 'Transactions',
    reportsTab: 'Reports',
    settingsTab: 'Settings',
    activityLedger: 'Activity ledger',
    backToList: 'Back to list',
    totalIncome: 'Total income',
    totalExpense: 'Total expense',
    donations: 'Donations',
    sales: 'Sales',
    grants: 'Grants',
    expenses: 'Expenses',
    recentTransactions: 'Recent transactions',
    recentTransactionsHint: 'Latest ledger entries for this activity.',
    date: 'Date',
    direction: 'Direction',
    amount: 'Amount',
    noTransactions: 'No transactions',
    noTransactionsHint: 'Add income or expenses to build the ledger.',
    incomeHint: 'Donations, grants, sales, and manual income.',
    addIncome: 'Add income',
    expensesHint: 'Direct activity expenses (custody expenses post on approval).',
    addExpense: 'Add expense',
    unifiedLedger: 'Unified ledger',
    runningBalanceHint: 'Running balance is calculated from chronological entries.',
    runningBalance: 'Running balance',
    incomeStatement: 'Income statement',
    incomeStatementHint: 'Income vs expenses for this activity.',
    totalExpenses: 'Total expenses',
    netProfitLoss: 'Net / profit-loss',
    monthlySummary: 'Monthly summary',
    monthlySummaryHint: 'Income vs expense by month.',
    noMonthlyData: 'No monthly data',
    noMonthlyHint: 'Transactions will populate this chart.',
    settings: 'Settings',
    settingsHint: 'Update activity details and status.',
    saveSettings: 'Save settings',
    incomeType: 'Income type',
    existingDonation: 'Existing donation',
    chooseDonation: 'Choose a donation',
    saveIncome: 'Save income',
    expenseType: 'Expense type',
    saveExpense: 'Save expense',
    donationLink: 'Donation (link existing)',
    grant: 'Grant',
    sale: 'Sale',
    manualIncome: 'Manual income',
    manualExpense: 'Manual expense',
    purchase: 'Purchase',
    salary: 'Salary',
    maintenance: 'Maintenance',
    utilities: 'Utilities',
    transportation: 'Transportation',
    marketing: 'Marketing',
    other: 'Other',
    incomeDir: 'Income',
    expenseDir: 'Expense',
  },
} as const

type Copy = Record<keyof (typeof copy)['ar'], string>

function useCopy(): Copy {
  const { locale } = useLocale()
  return copy[locale === 'en' ? 'en' : 'ar']
}

function money(value: number | string | null | undefined) {
  const locale = document.documentElement.lang === 'ar' ? 'ar-EG' : 'en-EG'
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'EGP',
    maximumFractionDigits: 2,
  }).format(Number(value ?? 0))
}

function date(value: string | null | undefined) {
  if (!value) return '—'
  return new Date(value).toLocaleString(document.documentElement.lang === 'ar' ? 'ar-EG' : 'en-EG')
}

function messageFor(error: unknown, fallback: string) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return fallback
}

function ErrorNotice({ error, fallback }: { error: unknown; fallback: string }) {
  return <div className="notice notice-danger">{messageFor(error, fallback)}</div>
}

function PageLoading({ label }: { label: string }) {
  return <div className="page-loading">{label}</div>
}

function Modal({
  title,
  onClose,
  closeLabel,
  children,
}: {
  title: string
  onClose: () => void
  closeLabel: string
  children: React.ReactNode
}) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
          <button type="button" className="button button-secondary" onClick={onClose}>
            {closeLabel}
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

function directionLabel(value: string, t: Copy) {
  return value === 'income' ? t.incomeDir : value === 'expense' ? t.expenseDir : value
}

function typeLabel(value: string, t: Copy) {
  const map: Record<string, string> = {
    donation: t.donations,
    grant: t.grant,
    sale: t.sale,
    manual_income: t.manualIncome,
    manual_expense: t.manualExpense,
    purchase: t.purchase,
    salary: t.salary,
    maintenance: t.maintenance,
    utilities: t.utilities,
    transportation: t.transportation,
    marketing: t.marketing,
    other: t.other,
  }
  return map[value] ?? value
}

function statusLabel(value: string, t: Copy) {
  return value === 'active' ? t.active : value === 'inactive' ? t.inactive : value
}

export function ActivitiesPage() {
  const t = useCopy()
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Activity | null>(null)

  const query = useMemo(() => {
    const params = new URLSearchParams({ page_size: '50' })
    if (search.trim()) params.set('search', search.trim())
    if (status) params.set('status', status)
    return params.toString()
  }, [search, status])

  const activities = useQuery({
    queryKey: ['activities', query],
    queryFn: () => api<PageResponse<Activity>>(`/activities?${query}`),
  })

  const saveActivity = useMutation({
    mutationFn: ({ id, payload }: { id?: number; payload: unknown }) =>
      id
        ? api<Activity>(`/activities/${id}`, { method: 'PATCH', body: JSON.stringify(payload) })
        : api<Activity>('/activities', { method: 'POST', body: JSON.stringify(payload) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      setShowForm(false)
      setEditing(null)
    },
  })

  const deactivate = useMutation({
    mutationFn: (id: number) => api(`/activities/${id}`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['activities'] }),
  })

  if (activities.isLoading) return <PageLoading label={t.loading} />
  if (activities.error) {
    return (
      <>
        <PageHeader title={t.projects} description={t.projectsDescShort} />
        <ErrorNotice error={activities.error} fallback={t.somethingWrong} />
      </>
    )
  }

  return (
    <>
      <PageHeader
        eyebrow={t.fundAccounting}
        title={t.projects}
        description={t.projectsDesc}
        action={
          hasRole('admin', 'finance', 'staff') ? (
            <button
              className="button button-primary"
              onClick={() => {
                setEditing(null)
                setShowForm(true)
              }}
            >
              <CirclePlus size={18} /> {t.createActivity}
            </button>
          ) : undefined
        }
      />
      <section className="filter-panel">
        <label>
          <Search size={16} />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t.searchActivities}
          />
        </label>
        <select value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">{t.allStatuses}</option>
          <option value="active">{t.active}</option>
          <option value="inactive">{t.inactive}</option>
        </select>
        <span>
          {activities.data?.total ?? 0} {t.activitiesCount}
        </span>
      </section>
      <div className="table-wrap panel">
        <table>
          <thead>
            <tr>
              <th>{t.name}</th>
              <th>{t.status}</th>
              <th>{t.income}</th>
              <th>{t.expense}</th>
              <th>{t.balance}</th>
              <th>{t.transactions}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {activities.data?.items.length ? (
              activities.data.items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <button className="link-button" onClick={() => navigate(`/activities/${item.id}`)}>
                      <strong>{item.name}</strong>
                      <small>{item.activity_type}</small>
                    </button>
                  </td>
                  <td>
                    <span className={`status ${item.status}`}>{statusLabel(item.status, t)}</span>
                  </td>
                  <td>{money(item.total_income)}</td>
                  <td>{money(item.total_expense)}</td>
                  <td>{money(item.balance)}</td>
                  <td>{item.transaction_count}</td>
                  <td className="table-actions">
                    {hasRole('admin', 'finance') && (
                      <>
                        <button
                          className="button button-secondary"
                          onClick={() => {
                            setEditing(item)
                            setShowForm(true)
                          }}
                        >
                          <Pencil size={16} />
                        </button>
                        {item.status === 'active' && (
                          <button
                            className="button button-secondary"
                            onClick={() => deactivate.mutate(item.id)}
                          >
                            {t.deactivate}
                          </button>
                        )}
                      </>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7}>
                  <EmptyState title={t.noActivities} message={t.noActivitiesHint} />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {showForm && (
        <Modal
          title={editing ? t.editActivity : t.createActivity}
          closeLabel={t.close}
          onClose={() => {
            setShowForm(false)
            setEditing(null)
          }}
        >
          <form
            className="form-grid"
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault()
              const form = new FormData(event.currentTarget)
              saveActivity.mutate({
                id: editing?.id,
                payload: {
                  name: String(form.get('name') || '').trim(),
                  description: form.get('description') || null,
                  activity_type: String(form.get('activity_type') || '').trim(),
                  status: form.get('status') || 'active',
                },
              })
            }}
          >
            <label className="form-span-2">
              {t.name}
              <input name="name" defaultValue={editing?.name ?? ''} required />
            </label>
            <label>
              {t.type}
              <input name="activity_type" defaultValue={editing?.activity_type ?? ''} required />
            </label>
            <label>
              {t.status}
              <select name="status" defaultValue={editing?.status ?? 'active'}>
                <option value="active">{t.active}</option>
                <option value="inactive">{t.inactive}</option>
              </select>
            </label>
            <label className="form-span-2">
              {t.description}
              <textarea name="description" rows={3} defaultValue={editing?.description ?? ''} />
            </label>
            {saveActivity.error && <ErrorNotice error={saveActivity.error} fallback={t.somethingWrong} />}
            <div className="form-actions form-span-2">
              <button
                type="button"
                className="button button-secondary"
                onClick={() => {
                  setShowForm(false)
                  setEditing(null)
                }}
              >
                {t.cancel}
              </button>
              <button className="button button-primary" disabled={saveActivity.isPending}>
                {editing ? t.saveChanges : t.create}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}

export function ActivityDetailPage() {
  const t = useCopy()
  const { activityId } = useParams()
  const id = Number(activityId)
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<
    'overview' | 'income' | 'expenses' | 'transactions' | 'reports' | 'settings'
  >('overview')
  const [incomeType, setIncomeType] = useState<string>('grant')
  const [showIncome, setShowIncome] = useState(false)
  const [showExpense, setShowExpense] = useState(false)

  const incomeTypes = [
    { value: 'donation', label: t.donationLink },
    { value: 'grant', label: t.grant },
    { value: 'sale', label: t.sale },
    { value: 'manual_income', label: t.manualIncome },
  ]
  const expenseTypes = [
    { value: 'manual_expense', label: t.manualExpense },
    { value: 'purchase', label: t.purchase },
    { value: 'salary', label: t.salary },
    { value: 'maintenance', label: t.maintenance },
    { value: 'utilities', label: t.utilities },
    { value: 'transportation', label: t.transportation },
    { value: 'marketing', label: t.marketing },
    { value: 'other', label: t.other },
  ]

  const activity = useQuery({
    queryKey: ['activity', id],
    queryFn: () => api<Activity>(`/activities/${id}`),
    enabled: Number.isFinite(id),
  })
  const summary = useQuery({
    queryKey: ['activity-summary', id],
    queryFn: () => api<ActivitySummary>(`/activities/${id}/summary`),
    enabled: Number.isFinite(id),
  })
  const transactions = useQuery({
    queryKey: ['activity-transactions', id],
    queryFn: () =>
      api<PageResponse<ActivityTransaction>>(`/activities/${id}/transactions?page_size=100`),
    enabled: Number.isFinite(id),
  })
  const reports = useQuery({
    queryKey: ['activity-reports', id],
    queryFn: () => api<Record<string, unknown>>(`/activities/${id}/reports`),
    enabled: Number.isFinite(id) && tab === 'reports',
  })
  const donations = useQuery({
    queryKey: ['donations-for-activity-link'],
    queryFn: () => api<PageResponse<Donation>>('/donations?page_size=100&status=confirmed'),
    enabled: showIncome && incomeType === 'donation',
  })

  const createTx = useMutation({
    mutationFn: (payload: unknown) =>
      api<ActivityTransaction>(`/activities/${id}/transactions`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity', id] })
      queryClient.invalidateQueries({ queryKey: ['activity-summary', id] })
      queryClient.invalidateQueries({ queryKey: ['activity-transactions', id] })
      queryClient.invalidateQueries({ queryKey: ['activity-reports', id] })
      queryClient.invalidateQueries({ queryKey: ['activities'] })
      setShowIncome(false)
      setShowExpense(false)
    },
  })

  const updateActivity = useMutation({
    mutationFn: (payload: unknown) =>
      api<Activity>(`/activities/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['activity', id] })
      queryClient.invalidateQueries({ queryKey: ['activities'] })
    },
  })

  if (activity.isLoading || summary.isLoading) return <PageLoading label={t.loading} />
  if (activity.error) return <ErrorNotice error={activity.error} fallback={t.somethingWrong} />
  if (!activity.data) return null

  const monthly =
    ((reports.data?.monthly_summary as Array<{
      month: string
      income: number
      expense: number
    }>) ??
      [])

  const tabs = [
    ['overview', t.overview],
    ['income', t.incomeTab],
    ['expenses', t.expensesTab],
    ['transactions', t.transactionsTab],
    ['reports', t.reportsTab],
    ['settings', t.settingsTab],
  ] as const

  return (
    <>
      <PageHeader
        eyebrow={t.activityLedger}
        title={activity.data.name}
        description={activity.data.description || activity.data.activity_type}
        action={
          <Link className="button button-secondary" to="/activities">
            <ArrowLeft size={16} /> {t.backToList}
          </Link>
        }
      />
      <div className="period-toggle" style={{ marginBottom: '1rem' }}>
        {tabs.map(([key, label]) => (
          <button key={key} className={tab === key ? 'selected' : ''} onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <>
          <section className="stats-grid">
            {[
              [t.totalIncome, money(summary.data?.total_income)],
              [t.totalExpense, money(summary.data?.total_expense)],
              [t.balance, money(summary.data?.balance)],
              [t.donations, money(summary.data?.donations)],
              [t.sales, money(summary.data?.sales)],
              [t.grants, money(summary.data?.grants)],
              [t.expenses, money(summary.data?.expenses)],
            ].map(([label, value]) => (
              <article className="stat-card" key={label as string}>
                <div className="stat-icon">
                  <FolderKanban size={20} />
                </div>
                <p>{label as string}</p>
                <strong>{value as string}</strong>
              </article>
            ))}
          </section>
          <article className="panel">
            <div className="panel-heading">
              <div>
                <h2>{t.recentTransactions}</h2>
                <p>{t.recentTransactionsHint}</p>
              </div>
            </div>
            {transactions.data?.items.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>{t.date}</th>
                      <th>{t.direction}</th>
                      <th>{t.type}</th>
                      <th>{t.description}</th>
                      <th>{t.amount}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.data.items.slice(0, 8).map((item) => (
                      <tr key={item.id}>
                        <td>{date(item.transaction_date)}</td>
                        <td>{directionLabel(item.transaction_direction, t)}</td>
                        <td>{typeLabel(item.transaction_type, t)}</td>
                        <td>{item.description || '—'}</td>
                        <td>{money(item.amount)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState title={t.noTransactions} message={t.noTransactionsHint} />
            )}
          </article>
        </>
      )}

      {tab === 'income' && (
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>{t.incomeTab}</h2>
              <p>{t.incomeHint}</p>
            </div>
            {hasRole('admin', 'finance', 'staff') && (
              <button className="button button-primary" onClick={() => setShowIncome(true)}>
                <CirclePlus size={16} /> {t.addIncome}
              </button>
            )}
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t.date}</th>
                  <th>{t.type}</th>
                  <th>{t.description}</th>
                  <th>{t.amount}</th>
                </tr>
              </thead>
              <tbody>
                {transactions.data?.items
                  .filter((item) => item.transaction_direction === 'income')
                  .map((item) => (
                    <tr key={item.id}>
                      <td>{date(item.transaction_date)}</td>
                      <td>{typeLabel(item.transaction_type, t)}</td>
                      <td>{item.description || '—'}</td>
                      <td>{money(item.amount)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </article>
      )}

      {tab === 'expenses' && (
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>{t.expensesTab}</h2>
              <p>{t.expensesHint}</p>
            </div>
            {hasRole('admin', 'finance', 'staff') && (
              <button className="button button-primary" onClick={() => setShowExpense(true)}>
                <CirclePlus size={16} /> {t.addExpense}
              </button>
            )}
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t.date}</th>
                  <th>{t.type}</th>
                  <th>{t.description}</th>
                  <th>{t.amount}</th>
                </tr>
              </thead>
              <tbody>
                {transactions.data?.items
                  .filter((item) => item.transaction_direction === 'expense')
                  .map((item) => (
                    <tr key={item.id}>
                      <td>{date(item.transaction_date)}</td>
                      <td>{typeLabel(item.transaction_type, t)}</td>
                      <td>{item.description || '—'}</td>
                      <td>{money(item.amount)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </article>
      )}

      {tab === 'transactions' && (
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>{t.unifiedLedger}</h2>
              <p>{t.runningBalanceHint}</p>
            </div>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>{t.date}</th>
                  <th>{t.direction}</th>
                  <th>{t.type}</th>
                  <th>{t.description}</th>
                  <th>{t.income}</th>
                  <th>{t.expense}</th>
                  <th>{t.runningBalance}</th>
                </tr>
              </thead>
              <tbody>
                {[...(transactions.data?.items ?? [])]
                  .sort(
                    (a, b) =>
                      new Date(a.transaction_date).getTime() -
                      new Date(b.transaction_date).getTime(),
                  )
                  .map((item) => (
                    <tr key={item.id}>
                      <td>{date(item.transaction_date)}</td>
                      <td>{directionLabel(item.transaction_direction, t)}</td>
                      <td>{typeLabel(item.transaction_type, t)}</td>
                      <td>{item.description || '—'}</td>
                      <td>
                        {item.transaction_direction === 'income' ? money(item.amount) : '—'}
                      </td>
                      <td>
                        {item.transaction_direction === 'expense' ? money(item.amount) : '—'}
                      </td>
                      <td>{money(item.running_balance)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </article>
      )}

      {tab === 'reports' && (
        <div className="dashboard-grid">
          <article className="panel">
            <div className="panel-heading">
              <div>
                <h2>{t.incomeStatement}</h2>
                <p>{t.incomeStatementHint}</p>
              </div>
            </div>
            {reports.isLoading ? (
              <PageLoading label={t.loading} />
            ) : (
              <div className="activity-list">
                <div className="activity-item">
                  <div>
                    <strong>{t.totalIncome}</strong>
                  </div>
                  <b>
                    {money(
                      (reports.data?.income_statement as { income?: { total?: number } })?.income
                        ?.total,
                    )}
                  </b>
                </div>
                <div className="activity-item">
                  <div>
                    <strong>{t.totalExpenses}</strong>
                  </div>
                  <b>
                    {money(
                      (reports.data?.income_statement as { expenses?: { total?: number } })
                        ?.expenses?.total,
                    )}
                  </b>
                </div>
                <div className="activity-item">
                  <div>
                    <strong>{t.netProfitLoss}</strong>
                  </div>
                  <b>
                    {money(
                      (reports.data?.profit_loss as { profit_loss?: number })?.profit_loss,
                    )}
                  </b>
                </div>
              </div>
            )}
          </article>
          <article className="panel chart-panel">
            <div className="panel-heading">
              <div>
                <h2>{t.monthlySummary}</h2>
                <p>{t.monthlySummaryHint}</p>
              </div>
            </div>
            {monthly.length ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={monthly}>
                  <XAxis dataKey="month" tickLine={false} axisLine={false} />
                  <YAxis tickLine={false} axisLine={false} />
                  <Tooltip formatter={(value) => money(value as number)} />
                  <Bar dataKey="income" fill="#0f766e" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="expense" fill="#ae3f34" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState title={t.noMonthlyData} message={t.noMonthlyHint} />
            )}
          </article>
        </div>
      )}

      {tab === 'settings' && hasRole('admin', 'finance') && (
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>{t.settings}</h2>
              <p>{t.settingsHint}</p>
            </div>
          </div>
          <form
            className="form-grid"
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault()
              const form = new FormData(event.currentTarget)
              updateActivity.mutate({
                name: String(form.get('name') || '').trim(),
                description: form.get('description') || null,
                activity_type: String(form.get('activity_type') || '').trim(),
                status: form.get('status'),
              })
            }}
          >
            <label className="form-span-2">
              {t.name}
              <input name="name" defaultValue={activity.data.name} required />
            </label>
            <label>
              {t.type}
              <input name="activity_type" defaultValue={activity.data.activity_type} required />
            </label>
            <label>
              {t.status}
              <select name="status" defaultValue={activity.data.status}>
                <option value="active">{t.active}</option>
                <option value="inactive">{t.inactive}</option>
              </select>
            </label>
            <label className="form-span-2">
              {t.description}
              <textarea name="description" rows={3} defaultValue={activity.data.description ?? ''} />
            </label>
            {updateActivity.error && (
              <ErrorNotice error={updateActivity.error} fallback={t.somethingWrong} />
            )}
            <div className="form-actions form-span-2">
              <button className="button button-primary" disabled={updateActivity.isPending}>
                {t.saveSettings}
              </button>
            </div>
          </form>
        </article>
      )}

      {showIncome && (
        <Modal title={t.addIncome} closeLabel={t.close} onClose={() => setShowIncome(false)}>
          <form
            className="form-grid"
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault()
              const form = new FormData(event.currentTarget)
              const transactionType = String(form.get('transaction_type'))
              if (transactionType === 'donation') {
                createTx.mutate({
                  transaction_type: 'donation',
                  reference_id: Number(form.get('reference_id')),
                })
                return
              }
              createTx.mutate({
                transaction_type: transactionType,
                amount: Number(form.get('amount')),
                description: form.get('description') || null,
                transaction_date: new Date(String(form.get('transaction_date'))).toISOString(),
              })
            }}
          >
            <label className="form-span-2">
              {t.incomeType}
              <select
                name="transaction_type"
                value={incomeType}
                onChange={(event) => setIncomeType(event.target.value)}
                required
              >
                {incomeTypes.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            {incomeType === 'donation' ? (
              <label className="form-span-2">
                {t.existingDonation}
                <select name="reference_id" required>
                  <option value="">{t.chooseDonation}</option>
                  {donations.data?.items
                    .filter((item) => !item.activity_id || item.activity_id === id)
                    .map((item) => (
                      <option key={item.id} value={item.id}>
                        #{item.id} · {money(item.amount)} · {item.donation_type.type_name}
                      </option>
                    ))}
                </select>
              </label>
            ) : (
              <>
                <label>
                  {t.amount}
                  <input name="amount" type="number" min="0.01" step="0.01" required />
                </label>
                <label>
                  {t.date}
                  <input
                    name="transaction_date"
                    type="datetime-local"
                    defaultValue={new Date().toISOString().slice(0, 16)}
                    required
                  />
                </label>
                <label className="form-span-2">
                  {t.description}
                  <textarea name="description" rows={3} />
                </label>
              </>
            )}
            {createTx.error && <ErrorNotice error={createTx.error} fallback={t.somethingWrong} />}
            <div className="form-actions form-span-2">
              <button type="button" className="button button-secondary" onClick={() => setShowIncome(false)}>
                {t.cancel}
              </button>
              <button className="button button-primary" disabled={createTx.isPending}>
                {t.saveIncome}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {showExpense && (
        <Modal title={t.addExpense} closeLabel={t.close} onClose={() => setShowExpense(false)}>
          <form
            className="form-grid"
            onSubmit={(event: FormEvent<HTMLFormElement>) => {
              event.preventDefault()
              const form = new FormData(event.currentTarget)
              createTx.mutate({
                transaction_type: form.get('transaction_type'),
                amount: Number(form.get('amount')),
                description: form.get('description') || null,
                transaction_date: new Date(String(form.get('transaction_date'))).toISOString(),
              })
            }}
          >
            <label className="form-span-2">
              {t.expenseType}
              <select name="transaction_type" required>
                {expenseTypes.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              {t.amount}
              <input name="amount" type="number" min="0.01" step="0.01" required />
            </label>
            <label>
              {t.date}
              <input
                name="transaction_date"
                type="datetime-local"
                defaultValue={new Date().toISOString().slice(0, 16)}
                required
              />
            </label>
            <label className="form-span-2">
              {t.description}
              <textarea name="description" rows={3} />
            </label>
            {createTx.error && <ErrorNotice error={createTx.error} fallback={t.somethingWrong} />}
            <div className="form-actions form-span-2">
              <button type="button" className="button button-secondary" onClick={() => setShowExpense(false)}>
                {t.cancel}
              </button>
              <button className="button button-primary" disabled={createTx.isPending}>
                {t.saveExpense}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
