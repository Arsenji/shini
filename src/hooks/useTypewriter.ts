import { useEffect, useState } from 'react'

export type HeroPhrase = {
  lead: string
  word: string
  /** Показывать строку «по выгодным ценам» */
  showPrices: boolean
}

const phrases: HeroPhrase[] = [
  { lead: 'Качественные', word: 'шины', showPrices: true },
  { lead: 'Качественные', word: 'диски', showPrices: true },
  { lead: 'Качественный', word: 'шиномонтаж', showPrices: true },
  { lead: 'Качественно', word: 'и выгодно', showPrices: false },
]

export function useTypewriter() {
  const [text, setText] = useState('')
  const [phraseIndex, setPhraseIndex] = useState(0)
  const [isDeleting, setIsDeleting] = useState(false)

  const phrase = phrases[phraseIndex]

  useEffect(() => {
    const current = phrase.word
    const timeout = setTimeout(
      () => {
        if (!isDeleting) {
          const next = current.slice(0, text.length + 1)
          setText(next)
          if (next === current) {
            setTimeout(() => setIsDeleting(true), 2000)
          }
        } else {
          const next = current.slice(0, text.length - 1)
          setText(next)
          if (next === '') {
            setIsDeleting(false)
            setPhraseIndex((i) => (i + 1) % phrases.length)
          }
        }
      },
      isDeleting ? 60 : 120,
    )
    return () => clearTimeout(timeout)
  }, [text, phraseIndex, isDeleting, phrase.word])

  return {
    lead: phrase.lead,
    text,
    showPrices: phrase.showPrices,
  }
}
