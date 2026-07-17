import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowRight,
  ArrowDownToLine,
  BookOpen,
  Check,
  ChevronRight,
  CirclePlus,
  Clock3,
  Droplets,
  Download,
  FileSpreadsheet,
  HandCoins,
  Heart,
  Landmark,
  Mail,
  MapPin,
  MessageCircle,
  Pencil,
  Search,
  ShieldCheck,
  UserPlus,
  UsersRound,
  X,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { api, ApiError, download } from './api'
import { useAuth } from './auth'
import { brand } from './branding'
import { EmptyState, PageHeader } from './components/AppShell'
import { LanguageSwitcher } from './localization'
import type {
  CustodyAssignment,
  CustodyExpense,
  DashboardSummary,
  Donation,
  DonationType,
  Donor,
  PageResponse,
  ScheduledReport,
  User,
} from './types'

const chartColors = ['#0f766e', '#d97706', '#7c3aed', '#dc2626', '#2563eb', '#65a30d']

function money(value: number | string | null | undefined, currency = 'USD') {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 2 }).format(Number(value ?? 0))
}

function date(value: string | null | undefined) {
  return value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(value)) : '—'
}

function messageFor(error: unknown) {
  return error instanceof ApiError ? error.message : 'Something went wrong. Please try again.'
}

function Status({ value }: { value: string }) {
  return <span className={`status ${value}`}>{value}</span>
}

function ErrorNotice({ error }: { error: unknown }) {
  return error ? <p className="form-error">{messageFor(error)}</p> : null
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-header"><h2>{title}</h2><button className="icon-button" type="button" onClick={onClose} aria-label="Close"><X /></button></div>
        {children}
      </section>
    </div>
  )
}

function PageLoading() {
  return <div className="page-state">Loading data…</div>
}

function ImpactCounter({ label, detail }: { label: string; detail: string }) {
  const [isVisible, setIsVisible] = useState(false)
  const counterRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const element = counterRef.current
    if (!element) return
    const observer = new IntersectionObserver(([entry]) => setIsVisible(entry.isIntersecting), { threshold: 0.35 })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return <article className={`impact-counter ${isVisible ? 'counter-visible' : ''}`} ref={counterRef}><span className="counter-placeholder">—</span><strong>{label}</strong><small>{detail}</small></article>
}

export function LandingPage() {
  const navigate = useNavigate()
  const [contactNotice, setContactNotice] = useState<string | null>(null)
  const campaigns = [
    ['Emergency Relief', 'Rapid support for people facing urgent hardship.', 'Campaign details and donation target to be confirmed.'],
    ['Food Security', 'Helping families access essential food and household supplies.', 'Campaign details and donation target to be confirmed.'],
    ['Community Care', 'Supporting practical local initiatives with dignity and care.', 'Campaign details and donation target to be confirmed.'],
  ]
  const programs: Array<[LucideIcon, string, string]> = [
    [HandCoins, 'Emergency Relief', 'Prepared to respond when a community faces urgent needs.'],
    [Heart, 'Food Aid', 'Food parcels and essential supplies for families.'],
    [ShieldCheck, 'Medical Support', 'Help with treatment, medicine, and recovery.'],
    [BookOpen, 'Education', 'Learning resources and opportunities for children.'],
    [UsersRound, 'Orphan Sponsorship', 'Long-term care and opportunity for children.'],
    [Droplets, 'Water Projects', 'Safe water initiatives for communities in need.'],
    [Clock3, 'Ramadan & Eid Campaigns', 'Seasonal giving with meaningful local impact.'],
  ]
  return (
    <div className="landing foundation-landing">
      <main>
        <section className="foundation-hero">
          <header className="landing-nav foundation-nav">
            <a className="brand landing-brand" href="#top"><img className="brand-logo" src={brand.logoPath} alt={`${brand.appName} logo`} /><span><strong>{brand.appName}</strong><small>مؤسسة بيتك · Together, we restore hope</small></span></a>
            <div className="foundation-nav-links"><a href="#about">About us</a><a href="#programs">Our projects</a><a href="#contact">Contact</a></div>
            <div className="landing-actions"><LanguageSwitcher /><button className="button button-quiet" type="button" onClick={() => navigate('/login')}>Staff sign in <ChevronRight size={17} /></button></div>
          </header>
          <div id="top" className="foundation-hero-content">
            <p className="eyebrow">Baytak Foundation · مؤسسة بيتك</p>
            <h1>Together, We Restore Hope.</h1>
            <p>Every donation creates a better future. Baytak Foundation brings people together around practical, compassionate community support.</p>
            <div className="foundation-hero-actions">
              <a className="button button-primary" href="#contact">Donate <Heart size={17} /></a>
              <a className="button button-secondary" href="#programs">Our Projects <ArrowRight size={17} /></a>
              <a className="button button-secondary" href="#help">Become a Volunteer</a>
              <a className="button button-quiet hero-about-link" href="#about">About Us</a>
            </div>
            <p className="hero-disclaimer">Online donation and volunteer sign-up channels are being prepared. Contact us directly to take part.</p>
          </div>
        </section>

        <section id="about" className="foundation-section foundation-about">
          <div className="section-intro"><p className="eyebrow">Who we are</p><h2>Direct help, delivered with dignity.</h2><p>Baytak Foundation is a community-focused charitable initiative. Its publicly visible work centres on aid distribution, volunteer activities, charity campaigns, and documenting support reaching beneficiaries.</p></div>
          <div className="about-points">
            <article><span>01</span><h3>Why we exist</h3><p>To turn generosity into practical support for people and communities facing everyday hardship.</p></article>
            <article><span>02</span><h3>What makes us different</h3><p>We put people first, focus on direct action, and aim to show the human impact behind every contribution.</p></article>
            <article><span>03</span><h3>Where we work</h3><p>Current regions and formal programme locations are being verified and will be published here.</p></article>
          </div>
        </section>

        <section className="foundation-section mission-vision">
          <article><p className="eyebrow">Mission</p><h2>Mobilise compassionate support for people who need it most.</h2><p>We aim to connect donors, volunteers, and local communities through transparent, practical charitable action.</p></article>
          <article><p className="eyebrow">Vision</p><h2>A future where every community can meet essential needs with hope.</h2><p>Our long-term ambition is sustained community wellbeing, stronger local participation, and a culture of accountable giving.</p></article>
        </section>

        <section className="foundation-section values-section">
          <div className="section-intro"><p className="eyebrow">Core values</p><h2>The principles behind every act of support.</h2></div>
          <div className="values-grid">{[['Transparency', 'Clear communication about how support is delivered.'], ['Compassion', 'People are treated with care, empathy, and respect.'], ['Dignity', 'Aid protects the choices and worth of every beneficiary.'], ['Accountability', 'We take responsibility for every contribution entrusted to us.'], ['Community', 'Local people and volunteers are part of the solution.'], ['Sustainability', 'We seek support that strengthens communities beyond one moment.']].map(([title, copy]) => <article key={title}><ShieldCheck size={20} /><h3>{title}</h3><p>{copy}</p></article>)}</div>
        </section>

        <section id="impact" className="foundation-section impact-section-new">
          <div className="section-intro"><p className="eyebrow">Our impact</p><h2>Every figure represents a person, family, and community.</h2><p>Verified impact figures will be published as the foundation’s reporting information becomes available.</p></div>
          <div className="impact-counter-grid">
            <ImpactCounter label="Families helped" detail="Impact figure to be verified" />
            <ImpactCounter label="Food packages distributed" detail="Impact figure to be verified" />
            <ImpactCounter label="Water projects" detail="Impact figure to be verified" />
            <ImpactCounter label="Volunteers" detail="Impact figure to be verified" />
            <ImpactCounter label="Regions served" detail="Impact figure to be verified" />
            <ImpactCounter label="Donations delivered" detail="Impact figure to be verified" />
          </div>
        </section>

        <section id="campaigns" className="foundation-section campaigns-section">
          <div className="section-heading-row"><div className="section-intro"><p className="eyebrow">Current campaigns</p><h2>Campaign information is being prepared.</h2></div><span className="placeholder-badge">Verified campaign data pending</span></div>
          <div className="campaign-grid">{campaigns.map(([title, copy, note], index) => <article className="campaign-card" key={title}><div className={`campaign-image image-placeholder image-${index + 1}`}><span>Campaign image placeholder</span></div><div className="campaign-card-body"><p className="campaign-kicker">Active campaign · details pending</p><h3>{title}</h3><p>{copy}</p><div className="campaign-progress"><div style={{ width: '0%' }} /></div><small>{note}</small><a className="text-button" href="#contact">Donate to this campaign <ArrowRight size={15} /></a></div></article>)}</div>
        </section>

        <section id="programs" className="foundation-section programs-section">
          <div className="section-intro"><p className="eyebrow">Our programs</p><h2>Areas of support we are ready to grow.</h2><p>These programme areas reflect the foundation’s visible community-centred work and will be refined as formal programme information is published.</p></div>
          <div className="program-grid">{programs.map(([Icon, title, copy]) => <article key={title}><Icon size={23} /><h3>{title}</h3><p>{copy}</p></article>)}</div>
        </section>

        <section className="foundation-section stories-section">
          <div className="section-intro"><p className="eyebrow">Success stories</p><h2>Stories of change will live here.</h2><p>With beneficiary consent and verified information, this area will share the people and communities behind the work.</p></div>
          <div className="before-after"><article className="image-placeholder"><span>Before photo placeholder</span></article><div><p className="eyebrow">Before / after</p><h3>From immediate need to renewed stability.</h3><p>Impact stories and documented outcomes are not yet available for publication.</p></div><article className="image-placeholder"><span>After photo placeholder</span></article></div>
        </section>

        <section className="foundation-section testimonials-gallery">
          <div><p className="eyebrow">Testimonials</p><h2>Voices from the community.</h2><blockquote>“Testimonial content will be added after verified consent and publication approval.”</blockquote><small>— Placeholder for beneficiary, volunteer, or donor story</small></div>
          <div><p className="eyebrow">Gallery & media</p><h2>Field moments, photos, and video.</h2><div className="gallery-grid">{['Gallery image placeholder', 'Video placeholder', 'Event photo placeholder', 'Volunteer activity placeholder'].map((label) => <div className="image-placeholder" key={label}><span>{label}</span></div>)}</div></div>
        </section>

        <section id="help" className="foundation-section help-section">
          <div className="section-intro"><p className="eyebrow">How you can help</p><h2>Make meaningful action possible.</h2></div>
          <div className="help-grid"><article><HandCoins size={27} /><h3>Donate</h3><p>Support a campaign or programme when donation channels are published.</p><a href="#contact">Ask about donating <ArrowRight size={15} /></a></article><article><UsersRound size={27} /><h3>Volunteer</h3><p>Offer your time, skills, and local knowledge to community initiatives.</p><a href="#contact">Volunteer with us <ArrowRight size={15} /></a></article><article><Heart size={27} /><h3>Partner with us</h3><p>Build practical partnerships that strengthen community support.</p><a href="#contact">Start a partnership <ArrowRight size={15} /></a></article></div>
        </section>

        <section className="foundation-section transparency-section">
          <div className="section-intro"><p className="eyebrow">Transparency</p><h2>Trust is built through openness.</h2><p>Formal public reports, policies, registration information, and partner lists were not available at the time this page was prepared. This section is reserved for their publication.</p></div>
          <div className="transparency-grid">{['Annual reports', 'Financial reports', 'Donation process', 'Frequently asked questions', 'Policies', 'Partners'].map((item) => <article key={item}><FileSpreadsheet size={19} /><span>{item}</span><small>Publication pending</small></article>)}</div>
        </section>

        <section className="foundation-section news-section">
          <div className="section-heading-row"><div className="section-intro"><p className="eyebrow">News & events</p><h2>Latest updates from Baytak.</h2></div><span className="placeholder-badge">Updates will be published here</span></div>
          <div className="news-grid"><article><p>FIELD UPDATE</p><h3>Community activity update</h3><span>Published updates are currently shared on the foundation’s Facebook page.</span></article><article><p>UPCOMING EVENT</p><h3>Event details to be announced</h3><span>Dates, location, and registration information will be added here.</span></article></div>
        </section>

        <section id="contact" className="foundation-section contact-section">
          <div className="contact-intro"><p className="eyebrow">Contact</p><h2>Let’s create a better future together.</h2><p>Reach out to ask about donations, volunteering, partnerships, or the foundation’s community work.</p><div className="contact-list"><a href={`mailto:${brand.contactEmail}`}><Mail size={18} /> {brand.contactEmail}</a><span><MessageCircle size={18} /> WhatsApp contact to be added</span><span><MapPin size={18} /> Address and service locations to be added</span><span><UsersRound size={18} /> Facebook is currently the foundation’s primary public channel</span></div></div>
          <form className="contact-form" onSubmit={(event) => { event.preventDefault(); setContactNotice('Form delivery is being configured. Please contact the foundation by email in the meantime.') }}><label>Name<input required placeholder="Your name" /></label><label>Email<input type="email" required placeholder="you@example.com" /></label><label>How can we help?<textarea required rows={4} placeholder="Tell us how you would like to support Baytak Foundation" /></label><button className="button button-primary" type="submit">Send message <ArrowRight size={17} /></button>{contactNotice && <p className="contact-notice">{contactNotice}</p>}</form>
        </section>
      </main>
      <footer className="foundation-footer"><div className="brand"><img className="brand-logo" src={brand.logoPath} alt="" /><span><strong>{brand.appName}</strong><small>مؤسسة بيتك</small></span></div><span>© {new Date().getFullYear()} {brand.appName}. Built around compassion, dignity, and accountability.</span><a href="#top">Back top</a></footer>
    </div>
  )
}

export function LoginPage() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<unknown>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    setError(null)
    setIsSubmitting(true)
    try {
      await signIn(String(form.get('email')), String(form.get('password')))
      navigate('/dashboard')
    } catch (caught) {
      setError(caught)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-intro"><button type="button" className="brand brand-button" onClick={() => navigate('/')}><img className="brand-logo" src={brand.logoPath} alt={`${brand.appName} logo`} /><span><strong>{brand.appName}</strong><small>{brand.tagline}</small></span></button><div><p className="eyebrow">Welcome back</p><h1>Good work starts with a clear record.</h1><p>Sign in to manage the people, gifts, and funds entrusted to your organisation.</p></div><small>{brand.description}</small></section>
      <section className="auth-card-wrap"><form className="auth-card" onSubmit={submit}><div className="auth-card-heading"><div><p className="eyebrow">Secure sign in</p><h2>Access your workspace</h2><p>Use the administrator account configured for this environment.</p></div><LanguageSwitcher /></div><label>Email<input name="email" type="email" defaultValue="admin@charity.local" required autoComplete="email" /></label><label>Password<input name="password" type="password" defaultValue="ChangeMe123!" required autoComplete="current-password" /></label><ErrorNotice error={error} /><button className="button button-primary button-full" disabled={isSubmitting}>{isSubmitting ? 'Signing in…' : 'Sign in'} <ChevronRight size={17} /></button><button className="text-button" type="button" onClick={() => navigate('/forgot-password')}>Forgot password?</button></form></section>
    </div>
  )
}

export function DashboardPage() {
  const [period, setPeriod] = useState('month')
  const summary = useQuery({ queryKey: ['dashboard-summary', period], queryFn: () => api<DashboardSummary>(`/dashboard/summary?period=${period}`) })
  const byType = useQuery({ queryKey: ['donations-by-type', period], queryFn: () => api<Array<{ id: number; type_name: string; amount: number; count: number }>>(`/dashboard/donations-by-type?period=${period}`) })
  const recent = useQuery({ queryKey: ['recent-donors', period], queryFn: () => api<Array<{ id: number; name: string; last_donation_at: string; total_amount: number }>>(`/dashboard/recent-donors?period=${period}`) })
  if (summary.isLoading) return <PageLoading />
  if (summary.error) return <><PageHeader title="Overview" description="Your charity’s activity at a glance." /><ErrorNotice error={summary.error} /></>
  const stats = [
    ['Donations received', money(summary.data?.total_donations), HandCoins, 'confirmed in period'],
    ['Active donors', String(summary.data?.total_donors ?? 0), UsersRound, 'gave in this period'],
    ['Custody available', money(summary.data?.custody_balance), Landmark, 'after approved expenses'],
    ['Pending approvals', String(summary.data?.pending_custody_expenses ?? 0), Clock3, 'awaiting a decision'],
  ]
  return (
    <>
      <PageHeader eyebrow="Operations overview" title="Good morning." description="Here is what is happening across your charity." action={<div className="period-toggle">{['day', 'week', 'month'].map((item) => <button key={item} className={period === item ? 'selected' : ''} onClick={() => setPeriod(item)}>{item}</button>)}</div>} />
      <section className="stats-grid">{stats.map(([label, value, Icon, hint]) => { const StatIcon = Icon as typeof HandCoins; return <article className="stat-card" key={label as string}><div className="stat-icon"><StatIcon size={20} /></div><p>{label as string}</p><strong>{value as string}</strong><small>{hint as string}</small></article> })}</section>
      <section className="dashboard-grid">
        <article className="panel chart-panel"><div className="panel-heading"><div><h2>Giving by fund</h2><p>Confirmed donations for the selected period.</p></div></div>{byType.isLoading ? <PageLoading /> : (byType.data?.length ? <ResponsiveContainer width="100%" height={300}><PieChart><Pie data={byType.data} dataKey="amount" nameKey="type_name" innerRadius={72} outerRadius={108} paddingAngle={4}>{byType.data.map((entry, index) => <Cell key={entry.id} fill={chartColors[index % chartColors.length]} />)}</Pie><Tooltip formatter={(value) => money(value as number)} /></PieChart></ResponsiveContainer> : <EmptyState title="No donations yet" message="Donation totals will appear here." />)}<div className="chart-legend">{byType.data?.map((item, index) => <span key={item.id}><i style={{ background: chartColors[index % chartColors.length] }} />{item.type_name} <strong>{money(item.amount)}</strong></span>)}</div></article>
        <article className="panel recent-panel"><div className="panel-heading"><div><h2>Recently active donors</h2><p>People who gave most recently.</p></div></div>{recent.isLoading ? <PageLoading /> : recent.data?.length ? <div className="activity-list">{recent.data.map((donor) => <div className="activity-item" key={donor.id}><span className="avatar avatar-teal">{donor.name.split(' ').map((word) => word[0]).join('').slice(0, 2)}</span><div><strong>{donor.name}</strong><small>{date(donor.last_donation_at)}</small></div><b>{money(donor.total_amount)}</b></div>)}</div> : <EmptyState title="No activity yet" message="New donors will appear here." />}</article>
      </section>
      <article className="panel bar-panel"><div className="panel-heading"><div><h2>Donation distribution</h2><p>See the balance of support across active funds.</p></div></div>{byType.data?.length ? <ResponsiveContainer width="100%" height={270}><BarChart data={byType.data}><XAxis dataKey="type_name" tickLine={false} axisLine={false} /><YAxis tickFormatter={(value) => `${value}`} tickLine={false} axisLine={false} /><Tooltip formatter={(value) => money(value as number)} /><Bar dataKey="amount" radius={[6, 6, 0, 0]} fill="#0f766e" /></BarChart></ResponsiveContainer> : <EmptyState title="No donation data yet" message="Record a donation to start seeing distribution." />}</article>
    </>
  )
}

export function DonorsPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState({ name: '', phone: '', id: '' })
  const [showForm, setShowForm] = useState(false)
  const [editingDonor, setEditingDonor] = useState<Donor | null>(null)
  const donorQuery = new URLSearchParams({ page_size: '100' })
  if (filters.name) donorQuery.set('name', filters.name)
  if (filters.phone) donorQuery.set('phone', filters.phone)
  if (filters.id) donorQuery.set('id', filters.id)
  const donors = useQuery({ queryKey: ['donors', filters], queryFn: () => api<PageResponse<Donor>>(`/donors?${donorQuery.toString()}`) })
  const saveDonor = useMutation({
    mutationFn: ({ donorId, payload }: { donorId?: number; payload: unknown }) => donorId
      ? api<Donor>(`/donors/${donorId}`, { method: 'PATCH', body: JSON.stringify(payload) })
      : api<Donor>('/donors', { method: 'POST', body: JSON.stringify(payload) }),
    onSuccess: () => { queryClient.invalidateQueries(); setShowForm(false); setEditingDonor(null) },
  })
  const deleteDonor = useMutation({ mutationFn: (id: number) => api(`/donors/${id}`, { method: 'DELETE' }), onSuccess: () => queryClient.invalidateQueries() })

  return <>
    <PageHeader eyebrow="Relationships" title="Donors" description="Keep complete, searchable records of the people who support your work." action={<button className="button button-primary" onClick={() => { setEditingDonor(null); setShowForm(true) }}><UserPlus size={18} /> Add donor</button>} />
    <section className="filter-panel"><label className="search-field"><Search size={18} /><input value={filters.name} onChange={(event) => setFilters({ ...filters, name: event.target.value })} placeholder="Search by donor name" /></label><label>Phone<input value={filters.phone} onChange={(event) => setFilters({ ...filters, phone: event.target.value })} placeholder="e.g. 555" /></label><label>Donor ID<input value={filters.id} onChange={(event) => setFilters({ ...filters, id: event.target.value.replace(/\D/g, '') })} placeholder="e.g. 12" /></label><button className="text-button" type="button" onClick={() => setFilters({ name: '', phone: '', id: '' })}>Clear filters</button><span>{donors.data?.total ?? 0} donors</span></section>
    {donors.isLoading ? <PageLoading /> : donors.error ? <ErrorNotice error={donors.error} /> : donors.data?.items.length ? <div className="table-wrap"><table><thead><tr><th>Donor</th><th>Phone</th><th>Giving to date</th><th>Last fund</th><th>Added</th>{hasRole('admin') && <th>Actions</th>}</tr></thead><tbody>{donors.data.items.map((donor) => <tr key={donor.id}><td><div className="person-cell"><span className="avatar avatar-teal">{donor.first_name[0]}{donor.last_name[0]}</span><div><strong>{donor.first_name} {donor.last_name}</strong><small>ID #{donor.id}</small></div></div></td><td>{donor.phones[0]?.phone_number ?? '—'}</td><td><strong>{money(donor.total_amount_donated)}</strong></td><td>{donor.last_donation_type ?? '—'}</td><td>{date(donor.created_at)}</td>{hasRole('admin') && <td><div className="inline-actions"><button className="text-button" onClick={() => { setEditingDonor(donor); setShowForm(true) }}>Edit</button><button className="text-button danger" onClick={() => { if (window.confirm(`Archive ${donor.first_name} ${donor.last_name}?`)) deleteDonor.mutate(donor.id) }}>Archive</button></div></td>}</tr>)}</tbody></table></div> : <EmptyState title="No donors found" message="Adjust the filters or add a donor to begin." />}
    {showForm && <DonorForm donor={editingDonor ?? undefined} onClose={() => { setShowForm(false); setEditingDonor(null) }} onSubmit={(payload) => saveDonor.mutate({ donorId: editingDonor?.id, payload })} isSubmitting={saveDonor.isPending} error={saveDonor.error} />}
  </>
}

function DonorForm({ donor, onClose, onSubmit, isSubmitting, error }: { donor?: Donor; onClose: () => void; onSubmit: (payload: unknown) => void; isSubmitting: boolean; error: unknown }) {
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    onSubmit({ first_name: form.get('first_name'), last_name: form.get('last_name'), phones: form.get('phone') ? [{ phone_number: form.get('phone'), is_primary: true }] : [], addresses: form.get('address') ? [{ address_line: form.get('address'), city: form.get('city'), country: form.get('country'), is_primary: true }] : [] })
  }
  const primaryPhone = donor?.phones[0]
  const primaryAddress = donor?.addresses?.[0]
  return <Modal title={donor ? 'Edit donor' : 'Add a donor'} onClose={onClose}><form className="form-grid" onSubmit={submit}><label>First name<input name="first_name" defaultValue={donor?.first_name} required autoFocus /></label><label>Last name<input name="last_name" defaultValue={donor?.last_name} required /></label><label>Primary phone<input name="phone" type="tel" defaultValue={primaryPhone?.phone_number} /></label><label>City<input name="city" defaultValue={primaryAddress?.city ?? ''} /></label><label className="form-span-2">Address<input name="address" defaultValue={primaryAddress?.address_line ?? ''} /></label><label className="form-span-2">Country<input name="country" defaultValue={primaryAddress?.country ?? ''} /></label><ErrorNotice error={error} /><div className="form-actions form-span-2"><button type="button" className="button button-secondary" onClick={onClose}>Cancel</button><button className="button button-primary" disabled={isSubmitting}>{isSubmitting ? 'Saving…' : donor ? 'Save donor' : 'Create donor'}</button></div></form></Modal>
}

export function DonationTypesPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingType, setEditingType] = useState<DonationType | null>(null)
  const types = useQuery({ queryKey: ['donation-types'], queryFn: () => api<DonationType[]>('/donation-types') })
  const saveType = useMutation({ mutationFn: ({ typeId, payload }: { typeId?: number; payload: unknown }) => typeId ? api<DonationType>(`/donation-types/${typeId}`, { method: 'PATCH', body: JSON.stringify(payload) }) : api<DonationType>('/donation-types', { method: 'POST', body: JSON.stringify(payload) }), onSuccess: () => { queryClient.invalidateQueries(); setShowForm(false); setEditingType(null) } })
  const deactivateType = useMutation({ mutationFn: (id: number) => api(`/donation-types/${id}`, { method: 'DELETE' }), onSuccess: () => queryClient.invalidateQueries() })
  return <>
    <PageHeader eyebrow="Fund setup" title="Donation types" description="Define the funds and causes donors can support." action={hasRole('admin') ? <button className="button button-primary" onClick={() => { setEditingType(null); setShowForm(true) }}><CirclePlus size={18} /> Add type</button> : undefined} />
    {types.isLoading ? <PageLoading /> : types.error ? <ErrorNotice error={types.error} /> : <section className="type-grid">{types.data?.map((item, index) => <article className="type-card" key={item.id}><span className="type-index">0{index + 1}</span><Status value={item.is_active ? 'active' : 'inactive'} /><h2>{item.type_name}</h2><p>{item.description || 'No description supplied for this fund.'}</p>{hasRole('admin') && <div className="card-actions"><button className="text-button" onClick={() => { setEditingType(item); setShowForm(true) }}>Edit</button>{item.is_active && <button className="text-button danger" onClick={() => { if (window.confirm(`Deactivate ${item.type_name}? Existing donations remain intact.`)) deactivateType.mutate(item.id) }}>Deactivate</button>}</div>}</article>)}{!types.data?.length && <EmptyState title="No donation types" message="Create a fund before recording a donation." />}</section>}
    {showForm && <Modal title={editingType ? 'Edit donation type' : 'Add donation type'} onClose={() => { setShowForm(false); setEditingType(null) }}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); saveType.mutate({ typeId: editingType?.id, payload: { type_name: form.get('type_name'), description: form.get('description'), is_active: form.get('is_active') === 'on' } }) }}><label className="form-span-2">Fund name<input name="type_name" defaultValue={editingType?.type_name} required autoFocus placeholder="e.g. Food aid" /></label><label className="form-span-2">Description<textarea name="description" defaultValue={editingType?.description ?? ''} rows={4} /></label><label className="form-span-2 checkbox-label"><input name="is_active" type="checkbox" defaultChecked={editingType?.is_active ?? true} /> Active and available for new donations</label><ErrorNotice error={saveType.error} /><div className="form-actions form-span-2"><button type="button" className="button button-secondary" onClick={() => { setShowForm(false); setEditingType(null) }}>Cancel</button><button className="button button-primary" disabled={saveType.isPending}>{editingType ? 'Save changes' : 'Create type'}</button></div></form></Modal>}
  </>
}

export function DonationsPage() {
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingDonation, setEditingDonation] = useState<Donation | null>(null)
  const [filters, setFilters] = useState({ donorId: '', typeId: '', status: '', amountMin: '', amountMax: '', startDate: '', endDate: '' })
  const donationQuery = new URLSearchParams({ page_size: '100' })
  if (filters.donorId) donationQuery.set('donor_id', filters.donorId)
  if (filters.typeId) donationQuery.set('donation_type_id', filters.typeId)
  if (filters.status) donationQuery.set('status', filters.status)
  if (filters.amountMin) donationQuery.set('amount_min', filters.amountMin)
  if (filters.amountMax) donationQuery.set('amount_max', filters.amountMax)
  if (filters.startDate) donationQuery.set('start_date', `${filters.startDate}T00:00:00Z`)
  if (filters.endDate) donationQuery.set('end_date', `${filters.endDate}T23:59:59Z`)
  const donations = useQuery({ queryKey: ['donations', filters], queryFn: () => api<PageResponse<Donation>>(`/donations?${donationQuery.toString()}`) })
  const donors = useQuery({ queryKey: ['donors-for-donation'], queryFn: () => api<PageResponse<Donor>>('/donors?page_size=100') })
  const types = useQuery({ queryKey: ['donation-types-all'], queryFn: () => api<DonationType[]>('/donation-types?include_inactive=true') })
  const saveDonation = useMutation({ mutationFn: ({ donationId, payload }: { donationId?: number; payload: unknown }) => donationId ? api<Donation>(`/donations/${donationId}`, { method: 'PATCH', body: JSON.stringify(payload) }) : api<Donation>('/donations', { method: 'POST', body: JSON.stringify(payload) }), onSuccess: () => { queryClient.invalidateQueries(); setShowForm(false); setEditingDonation(null) } })
  const cancelDonation = useMutation({ mutationFn: (id: number) => api(`/donations/${id}`, { method: 'DELETE' }), onSuccess: () => queryClient.invalidateQueries() })
  return <>
    <PageHeader eyebrow="Income records" title="Donations" description="Record contributions accurately and keep every receipt traceable." action={<button className="button button-primary" onClick={() => { setEditingDonation(null); setShowForm(true) }}><CirclePlus size={18} /> Record donation</button>} />
    <section className="filter-panel donation-filters"><label>Donor<select value={filters.donorId} onChange={(event) => setFilters({ ...filters, donorId: event.target.value })}><option value="">All donors</option>{donors.data?.items.map((donor) => <option key={donor.id} value={donor.id}>{donor.first_name} {donor.last_name}</option>)}</select></label><label>Donation type<select value={filters.typeId} onChange={(event) => setFilters({ ...filters, typeId: event.target.value })}><option value="">All types</option>{types.data?.map((type) => <option key={type.id} value={type.id}>{type.type_name}</option>)}</select></label><label>Status<select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}><option value="">All statuses</option><option value="confirmed">Confirmed</option><option value="cancelled">Cancelled</option><option value="refunded">Refunded</option></select></label><label>Minimum amount<input type="number" min="0" step="0.01" value={filters.amountMin} onChange={(event) => setFilters({ ...filters, amountMin: event.target.value })} /></label><label>Maximum amount<input type="number" min="0" step="0.01" value={filters.amountMax} onChange={(event) => setFilters({ ...filters, amountMax: event.target.value })} /></label><label>From<input type="date" value={filters.startDate} onChange={(event) => setFilters({ ...filters, startDate: event.target.value })} /></label><label>To<input type="date" value={filters.endDate} onChange={(event) => setFilters({ ...filters, endDate: event.target.value })} /></label><button className="text-button" type="button" onClick={() => setFilters({ donorId: '', typeId: '', status: '', amountMin: '', amountMax: '', startDate: '', endDate: '' })}>Clear filters</button><span>{donations.data?.total ?? 0} donations</span></section>
    {donations.isLoading ? <PageLoading /> : donations.error ? <ErrorNotice error={donations.error} /> : donations.data?.items.length ? <div className="table-wrap"><table><thead><tr><th>Date</th><th>Donor</th><th>Fund</th><th>Receipt</th><th>Status</th><th>Amount</th>{hasRole('admin', 'finance') && <th>Actions</th>}</tr></thead><tbody>{donations.data.items.map((item) => <tr key={item.id}><td>{date(item.donation_date)}</td><td><strong>{item.donor.first_name} {item.donor.last_name}</strong></td><td>{item.donation_type.type_name}</td><td>{item.receipt_number || '—'}</td><td><Status value={item.status} /></td><td><strong>{money(item.amount, item.currency)}</strong></td>{hasRole('admin', 'finance') && <td><div className="inline-actions"><button className="text-button" onClick={() => { setEditingDonation(item); setShowForm(true) }}>Edit</button>{item.status === 'confirmed' && <button className="text-button danger" onClick={() => { if (window.confirm('Cancel this donation? The record will be retained for audit.')) cancelDonation.mutate(item.id) }}>Cancel</button>}</div></td>}</tr>)}</tbody></table></div> : <EmptyState title="No donations found" message="Adjust the filters or record a donation." />}
    {showForm && <Modal title={editingDonation ? 'Edit donation' : 'Record a donation'} onClose={() => { setShowForm(false); setEditingDonation(null) }}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); saveDonation.mutate({ donationId: editingDonation?.id, payload: { donor_id: Number(form.get('donor_id')), donation_type_id: Number(form.get('donation_type_id')), amount: Number(form.get('amount')), currency: form.get('currency'), donation_date: new Date(String(form.get('donation_date'))).toISOString(), payment_method: form.get('payment_method') || null, receipt_number: form.get('receipt_number') || null, status: form.get('status') } }) }}><label className="form-span-2">Donor<select name="donor_id" defaultValue={editingDonation?.donor_id ?? ''} required><option value="">Choose a donor</option>{donors.data?.items.map((donor) => <option key={donor.id} value={donor.id}>{donor.first_name} {donor.last_name}</option>)}</select></label><label className="form-span-2">Donation type<select name="donation_type_id" defaultValue={editingDonation?.donation_type_id ?? ''} required><option value="">Choose a fund</option>{types.data?.map((type) => <option key={type.id} value={type.id} disabled={!type.is_active && type.id !== editingDonation?.donation_type_id}>{type.type_name}{type.is_active ? '' : ' (inactive)'}</option>)}</select></label><label>Amount<input name="amount" type="number" min="0.01" step="0.01" defaultValue={editingDonation?.amount} required /></label><label>Currency<select name="currency" defaultValue={editingDonation?.currency ?? 'USD'}><option>USD</option><option>EUR</option><option>GBP</option></select></label><label>Received at<input name="donation_date" type="datetime-local" defaultValue={editingDonation ? new Date(editingDonation.donation_date).toISOString().slice(0, 16) : new Date().toISOString().slice(0, 16)} required /></label><label>Payment method<input name="payment_method" defaultValue={editingDonation?.payment_method ?? ''} placeholder="Cash, transfer…" /></label><label>Record status<select name="status" defaultValue={editingDonation?.status ?? 'confirmed'}><option value="confirmed">Confirmed</option><option value="cancelled">Cancelled</option><option value="refunded">Refunded</option></select></label><label>Receipt number<input name="receipt_number" defaultValue={editingDonation?.receipt_number ?? ''} /></label><ErrorNotice error={saveDonation.error} /><div className="form-actions form-span-2"><button type="button" className="button button-secondary" onClick={() => { setShowForm(false); setEditingDonation(null) }}>Cancel</button><button className="button button-primary" disabled={saveDonation.isPending}>{editingDonation ? 'Save changes' : 'Save donation'}</button></div></form></Modal>}
  </>
}

export function CustodyPage() {
  const { user, hasRole } = useAuth()
  const queryClient = useQueryClient()
  const [showAssignment, setShowAssignment] = useState(false)
  const [expenseAssignmentId, setExpenseAssignmentId] = useState<number | null>(null)
  const [editingCustody, setEditingCustody] = useState<CustodyAssignment | null>(null)
  const custody = useQuery<PageResponse<CustodyAssignment> | CustodyAssignment[]>({ queryKey: ['custody'], queryFn: () => hasRole('admin', 'finance') ? api<PageResponse<CustodyAssignment>>('/custody?page_size=100') : api<CustodyAssignment[]>('/profile/custody') })
  const users = useQuery({ queryKey: ['active-users'], enabled: hasRole('admin'), queryFn: () => api<User[]>('/users?active_only=true') })
  const createAssignment = useMutation({ mutationFn: (payload: unknown) => api<CustodyAssignment>('/custody', { method: 'POST', body: JSON.stringify(payload) }), onSuccess: () => { queryClient.invalidateQueries(); setShowAssignment(false) } })
  const updateCustody = useMutation({ mutationFn: ({ assignmentId, payload }: { assignmentId: number; payload: unknown }) => api<CustodyAssignment>(`/custody/${assignmentId}`, { method: 'PATCH', body: JSON.stringify(payload) }), onSuccess: () => { queryClient.invalidateQueries(); setEditingCustody(null) } })
  const createExpense = useMutation({ mutationFn: ({ assignmentId, payload }: { assignmentId: number; payload: unknown }) => api<CustodyExpense>(`/custody/${assignmentId}/expenses`, { method: 'POST', body: JSON.stringify(payload) }), onSuccess: () => { queryClient.invalidateQueries(); setExpenseAssignmentId(null) } })
  const assignments = useMemo<CustodyAssignment[]>(() => Array.isArray(custody.data) ? custody.data : custody.data?.items ?? [], [custody.data])
  return <>
    <PageHeader eyebrow="Expense funds" title="Custody" description={hasRole('admin', 'finance') ? 'Assign funds, monitor available balance, and review submitted expenses.' : 'View the funds assigned to you and their remaining balance.'} action={hasRole('admin') ? <button className="button button-primary" onClick={() => setShowAssignment(true)}><CirclePlus size={18} /> Assign custody</button> : undefined} />
    {custody.isLoading ? <PageLoading /> : custody.error ? <ErrorNotice error={custody.error} /> : assignments.length ? <div className="custody-grid">{assignments.map((assignment) => <article className="custody-card" key={assignment.id}><div className="card-top"><span className="type-index">#{assignment.id}</span><Status value={assignment.status} /></div><p>Assigned amount</p><h2>{money(assignment.amount)}</h2><div className="balance-strip"><span>Available</span><strong>{money(assignment.available_balance)}</strong></div><dl><div><dt>Recipient</dt><dd>{assignment.recipient_name}</dd></div><div><dt>Assigned by</dt><dd>{assignment.assigned_by_name}</dd></div><div><dt>Assigned</dt><dd>{date(assignment.assigned_at)}</dd></div><div><dt>Expenses</dt><dd>{assignment.expenses.length}</dd></div></dl>{assignment.expenses.slice(0, 2).map((expense) => <div className="expense-row" key={expense.id}><span>{expense.title}</span><Status value={expense.status} /></div>)}<p className="card-description">{assignment.description || 'No assignment description.'}</p><div className="card-actions">{assignment.user_id === user?.id && assignment.status === 'active' && <button className="button button-secondary button-small" onClick={() => setExpenseAssignmentId(assignment.id)}>Submit expense</button>}{hasRole('admin') && <button className="text-button" onClick={() => setEditingCustody(assignment)}>Edit</button>}</div></article>)}</div> : <EmptyState title="No custody assigned" message={hasRole('admin') ? 'Assign custody to a user when they need funds for expenses.' : 'An assigned fund will appear here.'} />}
    {showAssignment && <Modal title="Assign custody" onClose={() => setShowAssignment(false)}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); createAssignment.mutate({ user_id: Number(form.get('user_id')), amount: Number(form.get('amount')), assigned_at: new Date(String(form.get('assigned_at'))).toISOString(), description: form.get('description') || null }) }}><label className="form-span-2">Recipient<select name="user_id" required><option value="">Choose a user</option>{users.data?.map((item) => <option key={item.id} value={item.id}>{item.first_name} {item.last_name} · {item.email}</option>)}</select></label><label>Amount<input name="amount" type="number" min="0.01" step="0.01" required /></label><label>Assigned at<input name="assigned_at" type="datetime-local" defaultValue={new Date().toISOString().slice(0, 16)} required /></label><label className="form-span-2">Description<textarea name="description" rows={3} placeholder="Purpose or usage guidance" /></label><ErrorNotice error={createAssignment.error} /><div className="form-actions form-span-2"><button type="button" className="button button-secondary" onClick={() => setShowAssignment(false)}>Cancel</button><button className="button button-primary" disabled={createAssignment.isPending}>Assign custody</button></div></form></Modal>}
    {editingCustody && <Modal title={`Edit custody #${editingCustody.id}`} onClose={() => setEditingCustody(null)}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); updateCustody.mutate({ assignmentId: editingCustody.id, payload: { description: form.get('description') || null, status: form.get('status') } }) }}><label className="form-span-2">Recipient<input value={`${editingCustody.recipient_name} · ${editingCustody.recipient_email}`} disabled /></label><label className="form-span-2">Status<select name="status" defaultValue={editingCustody.status}><option value="active">Active</option><option value="closed">Closed (only when fully spent)</option><option value="cancelled">Cancelled</option></select></label><label className="form-span-2">Description<textarea name="description" defaultValue={editingCustody.description ?? ''} rows={4} /></label><ErrorNotice error={updateCustody.error} /><div className="form-actions form-span-2"><button type="button" className="button button-secondary" onClick={() => setEditingCustody(null)}>Cancel</button><button className="button button-primary" disabled={updateCustody.isPending}>Save custody</button></div></form></Modal>}
    {expenseAssignmentId && <Modal title="Submit custody expense" onClose={() => setExpenseAssignmentId(null)}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); createExpense.mutate({ assignmentId: expenseAssignmentId, payload: { title: form.get('title'), description: form.get('description') || null, amount: Number(form.get('amount')), expense_date: new Date(String(form.get('expense_date'))).toISOString() } }) }}><label className="form-span-2">Expense title<input name="title" required autoFocus placeholder="e.g. Food supplies" /></label><label>Amount<input name="amount" type="number" min="0.01" step="0.01" required /></label><label>Expense date<input name="expense_date" type="datetime-local" defaultValue={new Date().toISOString().slice(0, 16)} required /></label><label className="form-span-2">Description<textarea name="description" rows={3} /></label><ErrorNotice error={createExpense.error} /><div className="form-actions form-span-2"><button type="button" className="button button-secondary" onClick={() => setExpenseAssignmentId(null)}>Cancel</button><button className="button button-primary" disabled={createExpense.isPending}>Submit for approval</button></div></form></Modal>}
  </>
}

export function ApprovalsPage() {
  const queryClient = useQueryClient()
  const expenses = useQuery({ queryKey: ['pending-expenses'], queryFn: () => api<CustodyExpense[]>('/approvals/custody-expenses') })
  const decide = useMutation({ mutationFn: ({ id, decision }: { id: number; decision: 'approve' | 'reject' }) => api(`/approvals/custody-expenses/${id}/${decision}`, { method: 'POST', body: JSON.stringify({}) }), onSuccess: () => queryClient.invalidateQueries() })
  return <><PageHeader eyebrow="Financial review" title="Approvals" description="Review submitted expenses before they reduce available custody." />{expenses.isLoading ? <PageLoading /> : expenses.error ? <ErrorNotice error={expenses.error} /> : expenses.data?.length ? <div className="table-wrap"><table><thead><tr><th>Expense</th><th>Assignment</th><th>Submitted</th><th>Amount</th><th>Decision</th></tr></thead><tbody>{expenses.data.map((expense) => <tr key={expense.id}><td><strong>{expense.title}</strong><small className="table-description">{expense.description}</small></td><td>#{expense.custody_assignment_id}</td><td>{date(expense.submitted_at)}</td><td><strong>{money(expense.amount)}</strong></td><td><div className="inline-actions"><button className="button button-small button-secondary" disabled={decide.isPending} onClick={() => decide.mutate({ id: expense.id, decision: 'reject' })}>Reject</button><button className="button button-small button-primary" disabled={decide.isPending} onClick={() => decide.mutate({ id: expense.id, decision: 'approve' })}><Check size={15} /> Approve</button></div></td></tr>)}</tbody></table></div> : <EmptyState title="Nothing awaiting approval" message="New expense submissions will appear here." />}</>
}

export function UsersPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const users = useQuery({ queryKey: ['users'], queryFn: () => api<User[]>('/users') })
  const roles = useQuery({ queryKey: ['roles'], queryFn: () => api<Array<{ id: number; name: string }>>('/users/roles') })
  const createUser = useMutation({ mutationFn: (payload: unknown) => api<User>('/users', { method: 'POST', body: JSON.stringify(payload) }), onSuccess: () => { queryClient.invalidateQueries(); setShowForm(false) } })
  return <><PageHeader eyebrow="Access control" title="Users" description="Manage team members and their access to financial records." action={<button className="button button-primary" onClick={() => setShowForm(true)}><UserPlus size={18} /> Add user</button>} />{users.isLoading ? <PageLoading /> : users.error ? <ErrorNotice error={users.error} /> : <div className="table-wrap"><table><thead><tr><th>Team member</th><th>Roles</th><th>Status</th><th>Created</th></tr></thead><tbody>{users.data?.map((item) => <tr key={item.id}><td><div className="person-cell"><span className="avatar">{item.first_name[0]}{item.last_name[0]}</span><div><strong>{item.first_name} {item.last_name}</strong><small>{item.email}</small></div></div></td><td><div className="role-list">{item.roles.map((role) => <span key={role.id}>{role.name}</span>)}</div></td><td><Status value={item.is_active ? 'active' : 'inactive'} /></td><td>{date(item.created_at)}</td></tr>)}</tbody></table></div>}{showForm && <Modal title="Add team member" onClose={() => setShowForm(false)}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); const selectedRoles = roles.data?.filter((role) => form.get(`role-${role.id}`)).map((role) => role.id) ?? []; createUser.mutate({ first_name: form.get('first_name'), last_name: form.get('last_name'), email: form.get('email'), phone_number: form.get('phone') || null, password: form.get('password'), role_ids: selectedRoles }) }}><label>First name<input name="first_name" required autoFocus /></label><label>Last name<input name="last_name" required /></label><label className="form-span-2">Email<input name="email" type="email" required /></label><label>Phone<input name="phone" /></label><label>Password<input name="password" type="password" minLength={8} required /></label><fieldset className="form-span-2"><legend>Roles</legend><div className="checkbox-row">{roles.data?.map((role) => <label key={role.id}><input name={`role-${role.id}`} type="checkbox" defaultChecked={role.name === 'staff'} /> {role.name}</label>)}</div></fieldset><ErrorNotice error={createUser.error} /><div className="form-actions form-span-2"><button type="button" className="button button-secondary" onClick={() => setShowForm(false)}>Cancel</button><button className="button button-primary" disabled={createUser.isPending}>Create user</button></div></form></Modal>}</>
}

export function ProfilePage() {
  const { user, reloadProfile } = useAuth()
  const queryClient = useQueryClient()
  const [notice, setNotice] = useState<string | null>(null)
  const updateProfile = useMutation({ mutationFn: (payload: unknown) => api<User>('/profile', { method: 'PATCH', body: JSON.stringify(payload) }), onSuccess: () => { queryClient.invalidateQueries(); reloadProfile(); setNotice('Your profile was updated.') } })
  const changePassword = useMutation({ mutationFn: (payload: unknown) => api('/auth/change-password', { method: 'POST', body: JSON.stringify(payload) }), onSuccess: () => setNotice('Password updated. Please sign in again to continue.') })
  return <><PageHeader eyebrow="Your account" title="Profile & settings" description="Update your contact details and keep your account secure." /><section className="settings-grid"><form className="panel settings-panel" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); updateProfile.mutate({ first_name: form.get('first_name'), last_name: form.get('last_name'), phone_number: form.get('phone') || null }) }}><div className="panel-heading"><div><h2>Personal details</h2><p>How your name appears on operational records.</p></div><Pencil size={18} /></div><label>First name<input name="first_name" defaultValue={user?.first_name} required /></label><label>Last name<input name="last_name" defaultValue={user?.last_name} required /></label><label>Phone number<input name="phone" defaultValue={user?.phone_number ?? ''} /></label><label>Email<input value={user?.email ?? ''} disabled /></label><button className="button button-primary" disabled={updateProfile.isPending}>Save changes</button></form><form className="panel settings-panel" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); changePassword.mutate({ current_password: form.get('current_password'), new_password: form.get('new_password') }) }}><div className="panel-heading"><div><h2>Security</h2><p>Use a unique password with at least 8 characters.</p></div><ShieldCheck size={18} /></div><label>Current password<input name="current_password" type="password" required /></label><label>New password<input name="new_password" type="password" minLength={8} required /></label><button className="button button-secondary" disabled={changePassword.isPending}>Update password</button></form></section>{(notice || updateProfile.error || changePassword.error) && <p className={notice ? 'success-notice' : 'form-error'}>{notice ?? messageFor(updateProfile.error ?? changePassword.error)}</p>}</>
}

export function ReportsPage() {
  const [reportType, setReportType] = useState<'donations' | 'donors' | 'custody'>('donations')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [notice, setNotice] = useState<string | null>(null)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const reports = useQuery({ queryKey: ['generated-reports'], queryFn: () => api<Array<{ id: number; report_type: string; format: string; generated_at: string; download_url: string }>>('/reports/generated') })
  const generate = useMutation({ mutationFn: () => api<{ id: number; download_url: string; report_type: string }>('/reports/generate', { method: 'POST', body: JSON.stringify({ report_type: reportType, format: 'csv', start_date: `${startDate}T00:00:00Z`, end_date: `${endDate}T23:59:59Z` }) }), onSuccess: (data) => { setNotice(`${data.report_type} report generated.`); queryClient.invalidateQueries({ queryKey: ['generated-reports'] }); download(data.download_url.replace('/api/v1', ''), `${data.report_type}-report.csv`) } })
  const hasWindow = Boolean(startDate && endDate)
  return <><PageHeader eyebrow="Insights & exports" title="Reports" description="Generate a CSV export for a specific reporting period." action={<button className="button button-secondary" onClick={() => navigate('/reports/scheduled')}><Clock3 size={18} /> Scheduled reports</button>} /><section className="report-builder"><div><span className="report-icon"><FileSpreadsheet size={24} /></span><p className="eyebrow">Manual export</p><h2>Build a time-bound report</h2><p>Choose the report contents and a start/end date. The exported CSV includes only records in that reporting window.</p></div><div className="report-controls"><label>Report contents<select value={reportType} onChange={(event) => setReportType(event.target.value as typeof reportType)}><option value="donations">Donation ledger</option><option value="donors">Donor summary</option><option value="custody">Custody assignments</option></select></label><div className="report-date-grid"><label>Start date<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} required /></label><label>End date<input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} required min={startDate} /></label></div>{!hasWindow && <p className="form-error">Choose both dates before generating a report.</p>}<button className="button button-primary" disabled={generate.isPending || !hasWindow} onClick={() => generate.mutate()}><Download size={18} /> {generate.isPending ? 'Generating…' : 'Generate CSV'}</button><ErrorNotice error={generate.error} />{notice && <p className="success-notice">{notice}</p>}</div></section><section className="panel"><div className="panel-heading"><div><h2>Generated reports</h2><p>Files are kept in the local application report volume.</p></div></div>{reports.isLoading ? <PageLoading /> : reports.data?.length ? <div className="activity-list">{reports.data.map((item) => <div className="activity-item" key={item.id}><span className="avatar avatar-teal"><ArrowDownToLine size={16} /></span><div><strong>{item.report_type} report</strong><small>{date(item.generated_at)} · {item.format.toUpperCase()}</small></div><button className="text-button" onClick={() => download(item.download_url.replace('/api/v1', ''), `${item.report_type}-${item.id}.csv`)}>Download</button></div>)}</div> : <EmptyState title="No reports generated" message="Your generated files will appear here." />}</section></>
}

export function ScheduledReportsPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingReport, setEditingReport] = useState<ScheduledReport | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const scheduledReports = useQuery({ queryKey: ['scheduled-reports'], queryFn: () => api<ScheduledReport[]>('/scheduled-reports') })
  const saveSchedule = useMutation({ mutationFn: ({ reportId, payload }: { reportId?: number; payload: unknown }) => reportId ? api<ScheduledReport>(`/scheduled-reports/${reportId}`, { method: 'PATCH', body: JSON.stringify(payload) }) : api<ScheduledReport>('/scheduled-reports', { method: 'POST', body: JSON.stringify(payload) }), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['scheduled-reports'] }); setShowForm(false); setEditingReport(null) } })
  const disableSchedule = useMutation({ mutationFn: (id: number) => api(`/scheduled-reports/${id}`, { method: 'DELETE' }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scheduled-reports'] }) })
  const runNow = useMutation({ mutationFn: (id: number) => api<{ status: 'completed' | 'failed'; error_message?: string | null; download_url: string }>(`/scheduled-reports/${id}/run`, { method: 'POST' }), onSuccess: (result) => { queryClient.invalidateQueries(); setNotice(result.status === 'completed' ? 'Report generated and sent by SMTP.' : `Report generated, but SMTP delivery failed: ${result.error_message}`); download(result.download_url.replace('/api/v1', ''), 'scheduled-report.csv') } })
  const defaultWindow = String(editingReport?.filters_json.window ?? 'last_30_days')
  return <><PageHeader eyebrow="Automated delivery" title="Scheduled reports" description="Create recurring CSV reports and send them through your configured SMTP server." action={<button className="button button-primary" onClick={() => { setEditingReport(null); setShowForm(true) }}><CirclePlus size={18} /> Schedule report</button>} />{notice && <p className="success-notice">{notice}</p>}<section className="smtp-notice"><ShieldCheck size={18} /><span>SMTP delivery uses the <code>SMTP_*</code> values in `.env`. Use <strong>Run now</strong> to test a schedule immediately.</span></section>{scheduledReports.isLoading ? <PageLoading /> : scheduledReports.error ? <ErrorNotice error={scheduledReports.error} /> : scheduledReports.data?.length ? <div className="table-wrap"><table><thead><tr><th>Name</th><th>Report</th><th>Window</th><th>Recipients</th><th>Next run</th><th>Status</th><th>Actions</th></tr></thead><tbody>{scheduledReports.data.map((report) => <tr key={report.id}><td><strong>{report.name}</strong><small className="table-description">{report.frequency}</small></td><td>{report.report_type}</td><td>{String(report.filters_json.window ?? 'custom range').replaceAll('_', ' ')}</td><td>{report.recipients_json.join(', ')}</td><td>{date(report.next_run_at)}</td><td><Status value={report.is_active ? 'active' : 'inactive'} /></td><td><div className="inline-actions"><button className="text-button" onClick={() => { setEditingReport(report); setShowForm(true) }}>Edit</button>{report.is_active && <button className="text-button" disabled={runNow.isPending} onClick={() => runNow.mutate(report.id)}>Run now</button>}{report.is_active && <button className="text-button danger" onClick={() => { if (window.confirm(`Disable ${report.name}?`)) disableSchedule.mutate(report.id) }}>Disable</button>}</div></td></tr>)}</tbody></table></div> : <EmptyState title="No scheduled reports" message="Schedule a recurring report for finance or leadership." />}{showForm && <Modal title={editingReport ? 'Edit scheduled report' : 'Schedule a report'} onClose={() => { setShowForm(false); setEditingReport(null) }}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); const recipients = String(form.get('recipients')).split(',').map((item) => item.trim()).filter(Boolean); saveSchedule.mutate({ reportId: editingReport?.id, payload: { name: form.get('name'), report_type: form.get('report_type'), frequency: form.get('frequency'), filters_json: { window: form.get('window') }, recipients_json: recipients, format: 'csv', is_active: form.get('is_active') === 'on' } }) }}><label className="form-span-2">Schedule name<input name="name" defaultValue={editingReport?.name} required autoFocus placeholder="e.g. Monthly donation summary" /></label><label>Report contents<select name="report_type" defaultValue={editingReport?.report_type ?? 'donations'}><option value="donations">Donation ledger</option><option value="donors">Donor summary</option><option value="custody">Custody assignments</option></select></label><label>Frequency<select name="frequency" defaultValue={editingReport?.frequency ?? 'monthly'}><option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="yearly">Yearly</option></select></label><label className="form-span-2">Reporting window<select name="window" defaultValue={defaultWindow}><option value="last_7_days">Previous 7 days</option><option value="last_30_days">Previous 30 days</option><option value="last_365_days">Previous 365 days</option></select></label><label className="form-span-2">Email recipients<input name="recipients" type="text" defaultValue={editingReport?.recipients_json.join(', ')} required placeholder="finance@example.org, director@example.org" /></label><label className="form-span-2 checkbox-label"><input name="is_active" type="checkbox" defaultChecked={editingReport?.is_active ?? true} /> Active schedule</label><ErrorNotice error={saveSchedule.error} /><div className="form-actions form-span-2"><button type="button" className="button button-secondary" onClick={() => { setShowForm(false); setEditingReport(null) }}>Cancel</button><button className="button button-primary" disabled={saveSchedule.isPending}>{editingReport ? 'Save schedule' : 'Create schedule'}</button></div></form></Modal>}</>
}
