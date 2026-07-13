import { FormEvent, useState } from 'react'
import { createOrder } from '../api/orders'
import { parseTireSizeLabel, sanitizeNameInput, sanitizePhoneInput, validateName } from '../lib/sanitize'

export function RequestForm() {
  const [name, setName] = useState('')
  const [size, setSize] = useState('')
  const [phone, setPhone] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

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

    try {
      await createOrder({
        name: safeName,
        width: parsed.width,
        profile: parsed.profile,
        radius: parsed.radius,
        phone: safePhone,
      })
      setStatus('success')
      setName('')
      setSize('')
      setPhone('')
    } catch (error) {
      setStatus('error')
      setErrorMessage(error instanceof Error ? error.message : 'Произошла ошибка. Попробуйте позже.')
    }
  }

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
