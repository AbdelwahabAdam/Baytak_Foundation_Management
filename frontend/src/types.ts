export type RoleName = 'admin' | 'finance' | 'staff' | 'viewer'

export interface Role {
  id: number
  name: RoleName
  description?: string | null
}

export interface User {
  id: number
  first_name: string
  last_name: string
  phone_number?: string | null
  email: string
  is_active: boolean
  roles: Role[]
  created_at: string
  updated_at: string
}

export interface Phone {
  id?: number
  phone_number: string
  is_primary: boolean
}

export interface Address {
  id?: number
  address_line: string
  city?: string | null
  country?: string | null
  is_primary: boolean
}

export interface Donor {
  id: number
  first_name: string
  last_name: string
  normalized_full_name: string
  phones: Phone[]
  addresses?: Address[]
  notes?: Array<{ id: number; note: string; created_at: string }>
  total_amount_donated: number
  last_donation_type?: string | null
  created_at: string
  updated_at: string
}

export interface DonationType {
  id: number
  type_name: string
  description?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Donation {
  id: number
  donor_id: number
  donation_type_id: number
  activity_id?: number | null
  amount: number
  currency: string
  donation_date: string
  payment_method?: string | null
  receipt_number?: string | null
  status: 'confirmed' | 'cancelled' | 'refunded'
  created_by_user_id: number
  created_at: string
  updated_at: string
  donor: Pick<Donor, 'id' | 'first_name' | 'last_name'>
  donation_type: DonationType
  activity?: { id: number; name: string; status: 'active' | 'inactive' } | null
}

export interface CustodyExpense {
  id: number
  custody_assignment_id: number
  user_id: number
  activity_id?: number | null
  title: string
  description?: string | null
  amount: number
  expense_date: string
  status: 'pending' | 'approved' | 'rejected'
  submitted_at: string
  approvals: Array<{ id: number; decision: string; comment?: string | null; decided_at: string }>
}

export interface CustodyAssignment {
  id: number
  user_id: number
  recipient_name: string
  recipient_email: string
  donation_type_id?: number | null
  donation_type_name?: string | null
  activity_id?: number | null
  activity_name?: string | null
  amount: number
  assigned_by_user_id: number
  assigned_by_name: string
  assigned_at: string
  description?: string | null
  status: 'active' | 'closed' | 'cancelled'
  available_balance: number
  expenses: CustodyExpense[]
}

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface DashboardSummary {
  period: { start_date: string; end_date: string }
  total_donations: number
  total_donors: number
  total_custody: number
  custody_balance: number
  pending_custody_expenses: number
  activities_count?: number
  activity_total_income?: number
  activity_total_expense?: number
}

export interface ActivitiesDashboardSummary {
  activities_count: number
  total_income: number
  total_expense: number
  balance: number
  top_activities: Array<{ id: number; name: string; income: number; expense: number; balance: number }>
  income_by_activity: Array<{ id: number; name: string; amount: number }>
  expense_by_activity: Array<{ id: number; name: string; amount: number }>
}

export interface Activity {
  id: number
  name: string
  description?: string | null
  activity_type: string
  status: 'active' | 'inactive'
  created_by_user_id: number
  created_at: string
  updated_at: string
  total_income: number
  total_expense: number
  balance: number
  transaction_count: number
}

export interface ActivitySummary {
  total_income: number
  total_expense: number
  balance: number
  donations: number
  sales: number
  grants: number
  expenses: number
}

export interface ActivityTransaction {
  id: number
  activity_id: number
  transaction_direction: 'income' | 'expense'
  transaction_type: string
  amount: number
  description?: string | null
  reference_type?: string | null
  reference_id?: number | null
  transaction_date: string
  created_by_user_id: number
  created_at: string
  updated_at: string
  running_balance?: number | null
}

export interface ScheduledReport {
  id: number
  name: string
  report_type: 'donations' | 'donors' | 'custody'
  frequency: 'weekly' | 'monthly' | 'yearly' | 'custom'
  cron_expression?: string | null
  filters_json: Record<string, unknown>
  recipients_json: string[]
  format: 'csv' | 'pdf' | 'excel'
  is_active: boolean
  last_run_at?: string | null
  next_run_at?: string | null
  created_by_user_id: number
  created_at: string
  updated_at: string
}

export interface WarehouseItem {
  id: number
  name: string
  sku?: string | null
  quantity: number
  unit: string
  location?: string | null
  notes?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AidCase {
  id: number
  case_number: string
  beneficiary_name: string
  phone?: string | null
  category: string
  status: 'open' | 'in_progress' | 'closed' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  description?: string | null
  requested_amount?: number | null
  approved_amount?: number | null
  created_by_user_id: number
  assigned_user_id?: number | null
  created_at: string
  updated_at: string
}
