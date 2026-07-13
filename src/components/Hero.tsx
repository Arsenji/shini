import { FormEvent, useState } from 'react'
import { useTypewriter } from '../hooks/useTypewriter'
import { createOrder } from '../api/orders'
import { TireTracks } from './TireTracks'

type FormStatus = 'idle' | 'loading' | 'success' | 'error'

export function Hero() {
  const typed = useTypewriter()
  const [width, setWidth] = useState('')
  const [profile, setProfile] = useState('')
  const [radius, setRadius] = useState('')
  const [phone, setPhone] = useState('')
  const [status, setStatus] = useState<FormStatus>('idle')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setStatus('loading')

    try {
      await createOrder({
        width: Number(width),
        profile: Number(profile),
        radius: Number(radius),
        phone,
      })
      setStatus('success')
      setWidth('')
      setProfile('')
      setRadius('')
      setPhone('')
    } catch {
      setStatus('error')
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
              <div className="hero__form-row">
                <input
                  type="text"
                  placeholder="Ширина (205)"
                  className="input"
                  value={width}
                  onChange={(e) => setWidth(e.target.value)}
                  required
                />
                <span className="hero__form-sep">/</span>
                <input
                  type="text"
                  placeholder="Профиль (55)"
                  className="input"
                  value={profile}
                  onChange={(e) => setProfile(e.target.value)}
                  required
                />
                <span className="hero__form-sep">R</span>
                <input
                  type="text"
                  placeholder="16"
                  className="input input--sm"
                  value={radius}
                  onChange={(e) => setRadius(e.target.value)}
                  required
                />
              </div>
              <input
                type="tel"
                placeholder="+7 (___) ___-__-__"
                className="input"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                required
              />
              {status === 'error' && (
                <p className="hero__form-feedback hero__form-feedback--error">
                  Произошла ошибка. Попробуйте позже.
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
