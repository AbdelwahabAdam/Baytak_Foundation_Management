import { Check, Minus, Plus, ShoppingCart, Trash2, X } from 'lucide-react'
import { type FormEvent, useMemo, useState } from 'react'

import { donationOptions, type DonationOption } from './content'

export type CartItem = {
  id: string
  optionId: string
  title: string
  amount: number
  quantity: number
}

function formatEgp(value: number) {
  return new Intl.NumberFormat('en-EG', {
    style: 'currency',
    currency: 'EGP',
    maximumFractionDigits: 0,
  }).format(value)
}

function OptionCard({
  option,
  amount,
  onAmountChange,
  onAdd,
}: {
  option: DonationOption
  amount: number
  onAmountChange: (value: number) => void
  onAdd: () => void
}) {
  return (
    <article className="donate-option-card">
      <div>
        <h3>{option.title}</h3>
        <p>{option.description}</p>
      </div>
      <div className="donate-option-actions">
        <label>
          Amount (EGP)
          <input
            type="number"
            min={option.fixed ? option.defaultAmount : 1}
            step={1}
            value={amount}
            disabled={option.fixed}
            onChange={(event) => onAmountChange(Number(event.target.value) || 0)}
          />
        </label>
        <button className="button button-primary" type="button" onClick={onAdd}>
          Add <Plus size={16} />
        </button>
      </div>
    </article>
  )
}

export function DonationPanel() {
  const [amounts, setAmounts] = useState<Record<string, number>>(() =>
    Object.fromEntries(donationOptions.map((option) => [option.id, option.defaultAmount])),
  )
  const [cart, setCart] = useState<CartItem[]>([])
  const [cartOpen, setCartOpen] = useState(false)
  const [checkoutOpen, setCheckoutOpen] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [cash, setCash] = useState(0)
  const [gold, setGold] = useState(0)
  const [debts, setDebts] = useState(0)

  const total = useMemo(
    () => cart.reduce((sum, item) => sum + item.amount * item.quantity, 0),
    [cart],
  )

  const zakatBase = Math.max(0, cash + gold - debts)
  const zakatDue = Math.round(zakatBase * 0.025)

  function addOption(option: DonationOption, amountOverride?: number) {
    const amount = amountOverride ?? amounts[option.id] ?? option.defaultAmount
    if (amount <= 0) return
    setCart((current) => {
      const existing = current.find((item) => item.optionId === option.id && item.amount === amount)
      if (existing) {
        return current.map((item) =>
          item.id === existing.id ? { ...item, quantity: item.quantity + 1 } : item,
        )
      }
      return [
        ...current,
        {
          id: `${option.id}-${amount}-${Date.now()}`,
          optionId: option.id,
          title: option.title,
          amount,
          quantity: 1,
        },
      ]
    })
    setCartOpen(true)
    setNotice(null)
  }

  function updateQuantity(id: string, delta: number) {
    setCart((current) =>
      current
        .map((item) => (item.id === id ? { ...item, quantity: item.quantity + delta } : item))
        .filter((item) => item.quantity > 0),
    )
  }

  function removeItem(id: string) {
    setCart((current) => current.filter((item) => item.id !== id))
  }

  function submitCheckout(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const name = String(form.get('name') || '').trim()
    if (!cart.length || !name) return
    setNotice(
      'Your donation request was received. Our team will contact you shortly to complete checkout and payment.',
    )
    setCart([])
    setCheckoutOpen(false)
    setCartOpen(false)
    event.currentTarget.reset()
  }

  const quick = donationOptions.filter((option) => option.category === 'quick')
  const monthly = donationOptions.filter((option) => option.category === 'monthly')
  const other = donationOptions.filter((option) => option.category === 'flexible' || option.category === 'ops')

  return (
    <>
      <div className="donate-layout">
        <div className="donate-catalog">
          <div className="donate-group">
            <p className="eyebrow">Quick giving</p>
            <h3>Start with a simple gift</h3>
            <div className="donate-option-grid">
              {quick.map((option) => (
                <OptionCard
                  key={option.id}
                  option={option}
                  amount={amounts[option.id]}
                  onAmountChange={(value) => setAmounts((current) => ({ ...current, [option.id]: value }))}
                  onAdd={() => addOption(option)}
                />
              ))}
            </div>
          </div>

          <div className="donate-group">
            <p className="eyebrow">Monthly shares</p>
            <h3>Sustain families every month</h3>
            <div className="donate-option-grid">
              {monthly.map((option) => (
                <OptionCard
                  key={option.id}
                  option={option}
                  amount={amounts[option.id]}
                  onAmountChange={(value) => setAmounts((current) => ({ ...current, [option.id]: value }))}
                  onAdd={() => addOption(option)}
                />
              ))}
            </div>
          </div>

          <div className="donate-group">
            <p className="eyebrow">Flexible support</p>
            <h3>Where the need is greatest</h3>
            <div className="donate-option-grid">
              {other.map((option) => (
                <OptionCard
                  key={option.id}
                  option={option}
                  amount={amounts[option.id]}
                  onAmountChange={(value) => setAmounts((current) => ({ ...current, [option.id]: value }))}
                  onAdd={() => addOption(option)}
                />
              ))}
            </div>
          </div>

          <div id="zakat" className="zakat-card">
            <div>
              <p className="eyebrow">Calculate your zakat</p>
              <h3>Estimate what you owe, then add it to your donation</h3>
              <p>Enter approximate assets in EGP. Zakat is calculated at 2.5% of eligible wealth.</p>
            </div>
            <div className="zakat-grid">
              <label>
                Cash & savings
                <input type="number" min={0} value={cash || ''} onChange={(event) => setCash(Number(event.target.value) || 0)} placeholder="0" />
              </label>
              <label>
                Gold & silver value
                <input type="number" min={0} value={gold || ''} onChange={(event) => setGold(Number(event.target.value) || 0)} placeholder="0" />
              </label>
              <label>
                Debts
                <input type="number" min={0} value={debts || ''} onChange={(event) => setDebts(Number(event.target.value) || 0)} placeholder="0" />
              </label>
            </div>
            <div className="zakat-result">
              <div>
                <small>Estimated zakat due</small>
                <strong>{formatEgp(zakatDue)}</strong>
              </div>
              <button
                className="button button-primary"
                type="button"
                disabled={zakatDue <= 0}
                onClick={() =>
                  addOption(
                    {
                      id: 'zakat',
                      title: 'Zakat',
                      description: 'Calculated zakat contribution.',
                      defaultAmount: zakatDue,
                      category: 'flexible',
                    },
                    zakatDue,
                  )
                }
              >
                Add zakat to cart <Plus size={16} />
              </button>
            </div>
          </div>
        </div>

        <aside className={`donate-cart-panel ${cartOpen ? 'is-open' : ''}`}>
          <div className="donate-cart-header">
            <div>
              <p className="eyebrow">Your donation</p>
              <h3>Checkout cart</h3>
            </div>
            <button className="icon-button cart-close" type="button" onClick={() => setCartOpen(false)} aria-label="Close cart">
              <X size={18} />
            </button>
          </div>

          {cart.length === 0 ? (
            <div className="donate-cart-empty">
              <ShoppingCart size={28} />
              <p>Select a donation type to begin.</p>
            </div>
          ) : (
            <ul className="donate-cart-list">
              {cart.map((item) => (
                <li key={item.id}>
                  <div>
                    <strong>{item.title}</strong>
                    <small>{formatEgp(item.amount)} each</small>
                  </div>
                  <div className="donate-cart-qty">
                    <button type="button" aria-label="Decrease quantity" onClick={() => updateQuantity(item.id, -1)}>
                      <Minus size={14} />
                    </button>
                    <span>{item.quantity}</span>
                    <button type="button" aria-label="Increase quantity" onClick={() => updateQuantity(item.id, 1)}>
                      <Plus size={14} />
                    </button>
                    <button className="icon-button" type="button" aria-label="Remove item" onClick={() => removeItem(item.id)}>
                      <Trash2 size={15} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <div className="donate-cart-footer">
            <div className="donate-cart-total">
              <span>Total</span>
              <strong>{formatEgp(total)}</strong>
            </div>
            <button
              className="button button-primary button-full"
              type="button"
              disabled={!cart.length}
              onClick={() => setCheckoutOpen(true)}
            >
              Proceed to checkout
            </button>
            {notice && (
              <p className="donate-notice">
                <Check size={16} /> {notice}
              </p>
            )}
          </div>
        </aside>
      </div>

      <button
        className={`donate-cart-fab ${cart.length ? 'has-items' : ''}`}
        type="button"
        onClick={() => setCartOpen(true)}
        aria-label="Open donation cart"
      >
        <ShoppingCart size={20} />
        {cart.length > 0 && <span>{cart.reduce((sum, item) => sum + item.quantity, 0)}</span>}
      </button>

      {checkoutOpen && (
        <div className="modal-backdrop" role="presentation">
          <section className="modal donate-checkout-modal" role="dialog" aria-modal="true" aria-label="Donation checkout">
            <div className="modal-header">
              <h2>Complete your donation</h2>
              <button className="icon-button" type="button" onClick={() => setCheckoutOpen(false)} aria-label="Close">
                <X />
              </button>
            </div>
            <p className="donate-checkout-summary">
              Donation total: <strong>{formatEgp(total)}</strong>
            </p>
            <form className="donate-checkout-form" onSubmit={submitCheckout}>
              <label>
                Full name
                <input name="name" required placeholder="Your full name" />
              </label>
              <label>
                Phone
                <input name="phone" type="tel" required placeholder="01xxxxxxxxx" />
              </label>
              <label>
                Email
                <input name="email" type="email" placeholder="you@example.com" />
              </label>
              <label>
                Preferred payment
                <select name="payment" defaultValue="transfer">
                  <option value="transfer">Bank transfer</option>
                  <option value="cash">Cash handover</option>
                  <option value="wallet">Mobile wallet</option>
                </select>
              </label>
              <label className="form-span-2">
                Notes
                <textarea name="notes" rows={3} placeholder="Any preference for how this donation should be used" />
              </label>
              <div className="form-actions form-span-2">
                <button className="button button-quiet" type="button" onClick={() => setCheckoutOpen(false)}>
                  Back
                </button>
                <button className="button button-primary" type="submit">
                  Confirm donation request
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </>
  )
}
