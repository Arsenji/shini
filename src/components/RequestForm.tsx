import { FormEvent, useEffect, useState } from 'react'
import { createOrder } from '../api/orders'
import { shopCategoryLabels, shopSeasonLabels, type ShopCategory, type ShopSeason } from '../data/shop'
import {
  clearOrderInterest,
  getOrderInterest,
  ORDER_INTEREST_EVENT,
  type OrderInterest,
} from '../lib/orderInterest'
import { parseTireSizeLabel, sanitizeNameInput, sanitizePhoneInput, validateName } from '../lib/sanitize'

export function RequestForm() {
  const [name, setName] = useState('')
  const [size, setSize] = useState(() => getOrderInterest()?.preferredSize ?? '')
  const [phone, setPhone] = useState('')
  const [interest, setInterest] = useState<OrderInterest | null>(() => getOrderInterest())
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    function onInterest(event: Event) {
      const detail = (event as CustomEvent<OrderInterest | null>).detail
      setInterest(detail)
      if (detail?.preferredSize) {
        setSize(detail.preferredSize)
        setStatus('idle')
        setErrorMessage('')
      } else if (detail === null) {
        setSize('')
      }
    }

    window.addEventListener(ORDER_INTEREST_EVENT, onInterest)
    return () => window.removeEventListener(ORDER_INTEREST_EVENT, onInterest)
  }, [])

  function clearInterest() {
    clearOrderInterest()
    setInterest(null)
    setSize('')
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setStatus('loading')
    setErrorMessage('')

    const safeName = validateName(name)
    if (!safeName) {
      setStatus('error')
      setErrorMessage('Укажите имя (только буквы), например «Иван»')
      return
    }

    const parsed = parseTireSizeLabel(size)
    if (!parsed) {
      setStatus('error')
      setErrorMessage('Укажите размер, например 205/55 R16')
      return
    }

    const safePhone = sanitizePhoneInput(phone)
    const currentInterest = interest ?? getOrderInterest()

    try {
      await createOrder({
        name: safeName,
        width: parsed.width,
        profile: parsed.profile,
        radius: parsed.radius,
        phone: safePhone,
        size_label: size.trim(),
        brand: currentInterest?.brand,
        model: currentInterest?.model,
        category: currentInterest?.category,
        season: currentInterest?.season,
        sizes: currentInterest?.sizes.join(', '),
        product_id: currentInterest?.productId,
      })
      setStatus('success')
      setName('')
      setSize('')
      setPhone('')
      clearOrderInterest()
      setInterest(null)
    } catch (error) {
      setStatus('error')
      setErrorMessage(error instanceof Error ? error.message : 'Произошла ошибка. Попробуйте позже.')
    }
  }

  const categoryLabel = interest
    ? shopCategoryLabels[interest.category as ShopCategory] ?? interest.category
    : null
  const seasonLabel =
    interest?.season && interest.season in shopSeasonLabels
      ? shopSeasonLabels[interest.season as ShopSeason]
      : null

  return (
    <section id="request" className="section request">
      <div className="container request__inner">
        <div className="section__header request__header">
          <p className="section__tag section__tag--highlight">Заявка</p>
          <h2 className="section__title">Оставьте заявку</h2>
          <p className="request__sub">Свяжемся в течении 10 минут</p>
        </div>

        {status === 'success' ? (
          <div className="hero__form-feedback hero__form-feedback--success">
            <p className="hero__form-feedback-title">Спасибо!</p>
            <p>Мы свяжемся с вами в течение 10 минут.</p>
          </div>
        ) : (
          <form className="request__form" onSubmit={handleSubmit}>
            {interest && (
              <div className="request__interest">
                <div className="request__interest-body">
                  <p className="request__interest-label">Вы выбрали</p>
                  <p className="request__interest-title">
                    {interest.brand} {interest.model}
                  </p>
                  <p className="request__interest-meta">
                    {[categoryLabel, seasonLabel, interest.color].filter(Boolean).join(' · ')}
                  </p>
                  <p className="request__interest-sizes">
                    {interest.preferredSize
                      ? interest.preferredSize
                      : interest.sizeGroup
                        ? interest.sizeGroup
                        : interest.sizes.length <= 4
                          ? interest.sizes.join(' · ')
                          : `${interest.sizes.slice(0, 4).join(' · ')} +${interest.sizes.length - 4}`}
                    {typeof interest.price === 'number' && interest.price > 0
                      ? ` · ${interest.price.toLocaleString('ru-RU')} ₽`
                      : ''}
                  </p>
                </div>
                <button type="button" className="request__interest-clear" onClick={clearInterest}>
                  Сбросить
                </button>
              </div>
            )}

            <input
              type="text"
              placeholder="Имя"
              className="input"
              value={name}
              onChange={(e) => setName(sanitizeNameInput(e.target.value))}
              required
            />
            <input
              type="text"
              placeholder="Размер (205/55 R16)"
              className="input"
              value={size}
              onChange={(e) => setSize(e.target.value)}
              required
            />
            <input
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              maxLength={12}
              placeholder="+7 (___) ___-__-__"
              className="input"
              value={phone}
              onChange={(e) => setPhone(sanitizePhoneInput(e.target.value))}
              required
            />
            {status === 'error' && (
              <p className="hero__form-feedback hero__form-feedback--error">
                {errorMessage || 'Произошла ошибка. Попробуйте позже.'}
              </p>
            )}
            <button type="submit" className="btn btn--gold btn--full" disabled={status === 'loading'}>
              {status === 'loading' ? 'Отправка...' : 'Отправить заявку'}
            </button>
          </form>
        )}
      </div>
    </section>
  )
}
