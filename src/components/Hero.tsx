import { FormEvent, useState } from 'react'
import { useTypewriter } from '../hooks/useTypewriter'
import { createOrder } from '../api/orders'
import { digitsOnly, parseTireNumber, sanitizeNameInput, sanitizePhoneInput, validateName } from '../lib/sanitize'
import { TireTracks } from './TireTracks'

type FormStatus = 'idle' | 'loading' | 'success' | 'error'

export function Hero() {
  const typed = useTypewriter()
  const [name, setName] = useState('')
  const [width, setWidth] = useState('')
  const [profile, setProfile] = useState('')
  const [radius, setRadius] = useState('')
  const [phone, setPhone] = useState('')
  const [status, setStatus] = useState<FormStatus>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setStatus('loading')
    setErrorMessage('')

    const safeName = validateName(name)
    const safeWidth = parseTireNumber(width)
    const safeProfile = parseTireNumber(profile)
    const safeRadius = parseTireNumber(radius)
    const safePhone = sanitizePhoneInput(phone)

    if (!safeName) {
      setStatus('error')
      setErrorMessage('Укажите имя (только буквы), например «Иван»')
      return
    }

    if (safeWidth === null || safeProfile === null || safeRadius === null) {
      setStatus('error')
      setErrorMessage('Укажите размер шины цифрами, например 205 / 55 R16')
      return
    }

    try {
      await createOrder({
        name: safeName,
        width: safeWidth,
        profile: safeProfile,
        radius: safeRadius,
        phone: safePhone,
      })
      setStatus('success')
      setName('')
      setWidth('')
      setProfile('')
      setRadius('')
      setPhone('')
    } catch (error) {
      setStatus('error')
      setErrorMessage(error instanceof Error ? error.message : 'Произошла ошибка. Попробуйте позже.')
    }
  }

  return (
    <section className="hero">
      <div className="hero__bg">
        <TireTracks />
        <div className="hero__glow hero__glow--1" />
        <div className="hero__glow hero__glow--2" />
      </div>

      <div className="container">
        <div className="hero__inner">
          <div className="hero__content">
          <p className="hero__tag">Шины, диски, шиномонтаж</p>
          <h1 className="hero__title">
            <span className="hero__title-line">Качественные</span>
            <span className="hero__title-line hero__title-line--typed">
              {typed}
              <span className="hero__cursor">|</span>
            </span>
            <span className="hero__title-line">
              по <strong>выгодным ценам</strong>
            </span>
          </h1>
          <p className="hero__desc">
            <span className="hero__desc-highlight">
              Подбор, продажа и монтаж шин и дисков всех классов — от бюджетных до премиальных.{' '}
              <strong>Бесплатная консультация и расчёт за 10 минут.</strong>
            </span>
          </p>
          <div className="hero__actions">
            <a href="#contact" className="btn btn--primary">
              Узнать стоимость
            </a>
            <a href="#catalog" className="btn btn--outline">
              Смотреть каталог
            </a>
          </div>
          </div>

          <div className="hero__card">
          <p className="section__tag section__tag--highlight">Онлайн подбор</p>
          <h2 className="hero__card-title">Подбор шин по размеру</h2>
          {status === 'success' ? (
            <div className="hero__form-feedback hero__form-feedback--success">
              <p className="hero__form-feedback-title">Спасибо!</p>
              <p>Мы свяжемся с вами в течение 10 минут.</p>
            </div>
          ) : (
            <form className="hero__form" onSubmit={handleSubmit}>
              <input
                type="text"
                placeholder="Имя"
                className="input"
                value={name}
                onChange={(e) => setName(sanitizeNameInput(e.target.value))}
                required
              />
              <div className="hero__form-row">
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  autoComplete="off"
                  maxLength={3}
                  placeholder="Ширина (205)"
                  className="input"
                  value={width}
                  onChange={(e) => setWidth(digitsOnly(e.target.value, 3))}
                  required
                />
                <span className="hero__form-sep">/</span>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  autoComplete="off"
                  maxLength={2}
                  placeholder="Профиль (55)"
                  className="input"
                  value={profile}
                  onChange={(e) => setProfile(digitsOnly(e.target.value, 2))}
                  required
                />
                <span className="hero__form-sep">R</span>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  autoComplete="off"
                  maxLength={2}
                  placeholder="16"
                  className="input input--sm"
                  value={radius}
                  onChange={(e) => setRadius(digitsOnly(e.target.value, 2))}
                  required
                />
              </div>
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
                {status === 'loading' ? 'Отправка...' : 'Получить расчёт'}
              </button>
            </form>
          )}
          <p className="hero__card-note">
            Перезвоним в течение 10 минут и назовём точную цену
          </p>
          </div>
        </div>
      </div>

      <div className="hero__tire">
        <div className="tire-visual">
          <div className="tire-visual__outer" />
          <div className="tire-visual__inner" />
          <div className="tire-visual__hub" />
        </div>
      </div>
    </section>
  )
}
