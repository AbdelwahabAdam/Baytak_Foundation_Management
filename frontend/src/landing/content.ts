import type { LucideIcon } from 'lucide-react'
import {
  BookOpen,
  Building2,
  HandCoins,
  HeartHandshake,
  HeartPulse,
  Home,
  Stethoscope,
  Utensils,
  Wallet,
} from 'lucide-react'

export type DonationOption = {
  id: string
  title: string
  description: string
  defaultAmount: number
  fixed?: boolean
  category: 'quick' | 'monthly' | 'flexible' | 'ops'
}

export const donationOptions: DonationOption[] = [
  {
    id: 'daily-sadaqa',
    title: 'Daily sadaqa',
    description: 'A fixed daily charity of 20 EGP.',
    defaultAmount: 20,
    fixed: true,
    category: 'quick',
  },
  {
    id: 'monthly-feeding',
    title: 'Monthly share · Feeding',
    description: 'A monthly share that helps feed families in need.',
    defaultAmount: 150,
    category: 'monthly',
  },
  {
    id: 'monthly-education',
    title: 'Monthly share · Educational sponsorship',
    description: 'Support a student’s education with a monthly sponsorship share.',
    defaultAmount: 200,
    category: 'monthly',
  },
  {
    id: 'monthly-quran',
    title: 'Monthly share · Quran & needy support',
    description: 'Support Quran centres or help people in urgent need.',
    defaultAmount: 100,
    category: 'monthly',
  },
  {
    id: 'flexible-need',
    title: 'Flexible donation',
    description: 'Directed to the activities with the greatest need.',
    defaultAmount: 100,
    category: 'flexible',
  },
  {
    id: 'operating-share',
    title: 'Operating expenses share',
    description: 'Help cover the operational costs that keep Baytak running.',
    defaultAmount: 50,
    category: 'ops',
  },
]

export const activities: Array<{ title: string; copy: string; image: string; Icon: LucideIcon }> = [
  {
    title: 'Zakat distribution',
    copy: 'Delivering zakat funds to eligible families with care and accountability.',
    image: '/placeholders/activity-zakat.svg',
    Icon: HandCoins,
  },
  {
    title: 'Feeding',
    copy: 'Food parcels and meals for households facing food insecurity.',
    image: '/placeholders/activity-feeding.svg',
    Icon: Utensils,
  },
  {
    title: 'Medical services',
    copy: 'Supporting treatment pathways, exams, and recovery for patients in need.',
    image: '/placeholders/activity-medical.svg',
    Icon: HeartPulse,
  },
  {
    title: 'Ongoing charities',
    copy: 'Sadaqa jariya projects that continue to benefit communities over time.',
    image: '/placeholders/activity-ongoing.svg',
    Icon: HeartHandshake,
  },
  {
    title: 'Educational sponsorships',
    copy: 'Helping students stay in school through sustained educational support.',
    image: '/placeholders/activity-education.svg',
    Icon: BookOpen,
  },
]

export const services: Array<{ title: string; copy: string; Icon: LucideIcon }> = [
  {
    title: 'Monthly treatment service',
    copy: 'Ongoing support for patients who need regular monthly medical care.',
    Icon: Stethoscope,
  },
  {
    title: 'Medical exams & tests',
    copy: 'Helping cover check-ups, lab work, and diagnostic examinations.',
    Icon: HeartPulse,
  },
  {
    title: 'Settling patient debts',
    copy: 'Assisting with outstanding treatment or surgery debts for patients in need.',
    Icon: Wallet,
  },
  {
    title: 'Medical sponsorships',
    copy: 'Longer-term sponsorships that keep essential medical care within reach.',
    Icon: HeartHandshake,
  },
]

export const achievements: Array<{ value: string; label: string; detail: string }> = [
  { value: '1,200+', label: 'Families supported', detail: 'Through food, medical, and emergency aid' },
  { value: '850+', label: 'Food parcels', detail: 'Distributed across community programmes' },
  { value: '320+', label: 'Medical cases', detail: 'Exams, treatment support, and sponsorships' },
  { value: '95+', label: 'Educational sponsorships', detail: 'Students supported through learning pathways' },
  { value: '40+', label: 'Active volunteers', detail: 'Field and programme support' },
  { value: '12+', label: 'Ongoing projects', detail: 'Including the Baytak workshop' },
]

export const reviews: Array<{ quote: string; name: string; role: string }> = [
  {
    quote: 'Baytak reached our family with dignity. The support arrived when we needed it most.',
    name: 'Amina H.',
    role: 'Beneficiary',
  },
  {
    quote: 'Volunteering with Baytak showed me how organised, transparent community work can change lives.',
    name: 'Omar S.',
    role: 'Volunteer',
  },
  {
    quote: 'I trust Baytak because I can see where monthly shares go — feeding, education, and medical care.',
    name: 'Laila M.',
    role: 'Community donor',
  },
]

export const navLinks = [
  { href: '#about', label: 'About Baytak' },
  { href: '#activities', label: 'Activities' },
  { href: '#projects', label: 'Projects' },
  { href: '#services', label: 'Services' },
  { href: '#donate', label: 'Donate' },
  { href: '#volunteer', label: 'Volunteer' },
  { href: '#contact', label: 'Contact' },
]

export const aboutPoints = [
  {
    title: 'Community first',
    copy: 'Baytak exists to turn generosity into practical support for families facing everyday hardship.',
    Icon: Home,
  },
  {
    title: 'Direct impact',
    copy: 'From feeding and zakat to medical care and education, every programme is built around real needs.',
    Icon: HandCoins,
  },
  {
    title: 'Trusted stewardship',
    copy: 'We aim for clear reporting, careful custody of funds, and support delivered with dignity.',
    Icon: Building2,
  },
]
