import {
  ArrowRight,
  ChevronRight,
  Heart,
  Mail,
  MapPin,
  MessageCircle,
  UsersRound,
} from 'lucide-react'
import { type FormEvent, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { brand } from '../branding'
import { LanguageSwitcher } from '../localization'
import { aboutPoints, achievements, activities, navLinks, reviews, services } from './content'
import { DonationPanel } from './DonationPanel'

function ImpactCounter({ value, label, detail }: { value: string; label: string; detail: string }) {
  const [isVisible, setIsVisible] = useState(false)
  const counterRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const element = counterRef.current
    if (!element) return
    const observer = new IntersectionObserver(([entry]) => setIsVisible(entry.isIntersecting), { threshold: 0.35 })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return (
    <article className={`impact-counter ${isVisible ? 'counter-visible' : ''}`} ref={counterRef}>
      <span className="counter-placeholder">{value}</span>
      <strong>{label}</strong>
      <small>{detail}</small>
    </article>
  )
}

export function LandingPage() {
  const navigate = useNavigate()
  const [contactNotice, setContactNotice] = useState<string | null>(null)
  const [volunteerNotice, setVolunteerNotice] = useState<string | null>(null)
  const [navScrolled, setNavScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setNavScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="landing foundation-landing">
      <header className={`landing-nav foundation-nav ${navScrolled ? 'is-scrolled' : ''}`}>
        <a className="brand landing-brand" href="#top">
          <img className="brand-logo" src={brand.logoPath} alt={`${brand.appName} logo`} />
          <span>
            <strong>{brand.appName}</strong>
            <small>مؤسسة بيتك · Together, we restore hope</small>
          </span>
        </a>
        <nav className="foundation-nav-links" aria-label="Primary">
          {navLinks.map((link) => (
            <a key={link.href} href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>
        <div className="landing-actions">
          <LanguageSwitcher />
          <a className="button button-primary nav-donate" href="#donate">
            Donate now <Heart size={16} />
          </a>
          <button className="button button-quiet" type="button" onClick={() => navigate('/login')}>
            Staff sign in <ChevronRight size={17} />
          </button>
        </div>
      </header>

      <main>
        <section id="top" className="foundation-hero">
          <div className="foundation-hero-content">
            <div className="hero-copy">
              <p className="eyebrow">Baytak Foundation · مؤسسة بيتك</p>
              <h1>Together, We Restore Hope.</h1>
              <p>
                Practical charity for families in need — feeding, medical care, education, and community support delivered with dignity.
              </p>
              <div className="foundation-hero-actions">
                <a className="button button-primary" href="#donate">
                  Donate now <Heart size={17} />
                </a>
                <a className="button button-secondary" href="#zakat">
                  Calculate your zakat
                </a>
                <a className="button button-quiet hero-about-link" href="#volunteer">
                  Volunteer with Baytak
                </a>
              </div>
            </div>
            <aside className="hero-donate-card">
              <p className="eyebrow">Give today</p>
              <h2>Daily sadaqa · 20 EGP</h2>
              <p>Start with a simple daily gift, or choose a monthly share for feeding, education, or community support.</p>
              <div className="hero-quick-amounts">
                <a href="#donate">20 EGP daily</a>
                <a href="#donate">Monthly share</a>
                <a href="#donate">Flexible gift</a>
              </div>
              <a className="button button-primary button-full" href="#donate">
                Open donation card <ArrowRight size={17} />
              </a>
            </aside>
          </div>
        </section>

        <section id="about" className="foundation-section foundation-about">
          <div className="section-intro">
            <p className="eyebrow">About Baytak</p>
            <h2>A home for compassionate community support.</h2>
            <p>
              Baytak Foundation is a community-focused charitable initiative. We distribute zakat, feed families, support medical needs,
              sustain ongoing charities, and invest in educational sponsorships.
            </p>
          </div>
          <div className="about-feature-grid">
            {aboutPoints.map(({ title, copy, Icon }) => (
              <article key={title}>
                <Icon size={22} />
                <h3>{title}</h3>
                <p>{copy}</p>
              </article>
            ))}
          </div>
          <div className="about-media image-placeholder about-media-ph">
            <span>About Baytak image placeholder</span>
          </div>
        </section>

        <section id="activities" className="foundation-section activities-section">
          <div className="section-intro">
            <p className="eyebrow">Baytak activities</p>
            <h2>Where generosity becomes action.</h2>
            <p>Our core activities turn donations into tangible support for people and families.</p>
          </div>
          <div className="activity-grid">
            {activities.map(({ title, copy, image, Icon }) => (
              <article key={title} className="activity-card">
                <div className="activity-image">
                  <img src={image} alt="" />
                  <Icon size={22} />
                </div>
                <div className="activity-body">
                  <h3>{title}</h3>
                  <p>{copy}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="projects" className="foundation-section projects-section">
          <div className="project-panel">
            <div className="project-media image-placeholder project-media-ph">
              <span>Baytak workshop image placeholder</span>
            </div>
            <div>
              <p className="eyebrow">Baytak projects</p>
              <h2>The workshop · المشغل</h2>
              <p>
                The Baytak workshop is a flagship project that builds livelihood pathways, skills, and sustainable community value.
                It stands alongside our aid programmes as a longer-term investment in dignity and opportunity.
              </p>
              <ul className="project-list">
                <li>Skills development and productive work opportunities</li>
                <li>Support for local families through sustained activity</li>
                <li>A practical project visitors can follow and fund</li>
              </ul>
              <a className="button button-primary" href="#donate">
                Support this project <ArrowRight size={16} />
              </a>
            </div>
          </div>
        </section>

        <section id="services" className="foundation-section services-section">
          <div className="section-intro">
            <p className="eyebrow">Baytak services</p>
            <h2>Medical care that reaches people in need.</h2>
            <p>Specialised medical services help patients access treatment, exams, and financial relief for care debts.</p>
          </div>
          <div className="service-grid">
            {services.map(({ title, copy, Icon }) => (
              <article key={title}>
                <div className="service-icon">
                  <Icon size={22} />
                </div>
                <h3>{title}</h3>
                <p>{copy}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="donate" className="foundation-section donate-section">
          <div className="section-heading-row">
            <div className="section-intro">
              <p className="eyebrow">Donate now</p>
              <h2>Choose a donation type and checkout.</h2>
              <p>
                Add daily sadaqa, monthly shares, flexible gifts, operating support, or calculated zakat to your cart — then complete checkout.
              </p>
            </div>
          </div>
          <DonationPanel />
        </section>

        <section id="impact" className="foundation-section impact-section-new">
          <div className="section-intro">
            <p className="eyebrow">What we have achieved</p>
            <h2>Activities completed with your support.</h2>
            <p>These figures reflect the scale of Baytak’s community work and will continue to grow as programmes expand.</p>
          </div>
          <div className="impact-counter-grid">
            {achievements.map((item) => (
              <ImpactCounter key={item.label} value={item.value} label={item.label} detail={item.detail} />
            ))}
          </div>
        </section>

        <section id="reviews" className="foundation-section reviews-section">
          <div className="section-intro">
            <p className="eyebrow">Reviews</p>
            <h2>Voices from the Baytak community.</h2>
          </div>
          <div className="reviews-grid">
            {reviews.map((review) => (
              <blockquote key={review.name}>
                <p>“{review.quote}”</p>
                <footer>
                  <strong>{review.name}</strong>
                  <span>{review.role}</span>
                </footer>
              </blockquote>
            ))}
          </div>
        </section>

        <section id="volunteer" className="foundation-section volunteer-section">
          <div className="volunteer-panel">
            <div>
              <p className="eyebrow">Volunteer with Baytak</p>
              <h2>Give your time where it matters.</h2>
              <p>
                Join field distribution, medical accompaniment, workshop support, or community outreach. Tell us how you would like to help.
              </p>
            </div>
            <form
              className="volunteer-form"
              onSubmit={(event: FormEvent<HTMLFormElement>) => {
                event.preventDefault()
                setVolunteerNotice('Volunteer registration is being configured. Please email us to join the next opportunity.')
              }}
            >
              <label>
                Name
                <input required placeholder="Your name" />
              </label>
              <label>
                Phone
                <input type="tel" required placeholder="01xxxxxxxxx" />
              </label>
              <label>
                How can you help?
                <textarea required rows={3} placeholder="Skills, availability, or preferred activity" />
              </label>
              <button className="button button-primary" type="submit">
                Join as a volunteer <UsersRound size={17} />
              </button>
              {volunteerNotice && <p className="contact-notice">{volunteerNotice}</p>}
            </form>
          </div>
        </section>

        <section id="contact" className="foundation-section contact-section">
          <div className="contact-intro">
            <p className="eyebrow">Contact us</p>
            <h2>Let’s create a better future together.</h2>
            <p>Reach out about donations, volunteering, medical services, or partnership with Baytak.</p>
            <div className="contact-list">
              <a href={`mailto:${brand.contactEmail}`}>
                <Mail size={18} /> {brand.contactEmail}
              </a>
              <span>
                <MessageCircle size={18} /> WhatsApp contact to be added
              </span>
              <span>
                <MapPin size={18} /> Address and service locations to be added
              </span>
            </div>
          </div>
          <form
            className="contact-form"
            onSubmit={(event) => {
              event.preventDefault()
              setContactNotice('Form delivery is being configured. Please contact the foundation by email in the meantime.')
            }}
          >
            <label>
              Name
              <input required placeholder="Your name" />
            </label>
            <label>
              Email
              <input type="email" required placeholder="you@example.com" />
            </label>
            <label>
              How can we help?
              <textarea required rows={4} placeholder="Tell us how you would like to support Baytak Foundation" />
            </label>
            <button className="button button-primary" type="submit">
              Send message <ArrowRight size={17} />
            </button>
            {contactNotice && <p className="contact-notice">{contactNotice}</p>}
          </form>
        </section>
      </main>

      <footer className="foundation-footer">
        <div className="brand">
          <img className="brand-logo" src={brand.logoPath} alt="" />
          <span>
            <strong>{brand.appName}</strong>
            <small>مؤسسة بيتك</small>
          </span>
        </div>
        <div className="footer-links">
          <a href="#about">About Baytak</a>
          <a href="#donate">Donate now</a>
          <a href="#volunteer">Volunteer</a>
          <a href="#contact">Contact</a>
        </div>
        <span>
          © {new Date().getFullYear()} {brand.appName}. Built around compassion, dignity, and accountability.
        </span>
        <a href="#top">Back top</a>
      </footer>
    </div>
  )
}
