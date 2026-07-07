import { useEffect, useState } from 'react'

const phrases = ['шины', 'диски', 'шиномонтаж', 'выгодно']

export function useTypewriter() {
  const [text, setText] = useState('')
  const [phraseIndex, setPhraseIndex] = useState(0)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    const current = phrases[phraseIndex]
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
  }, [text, phraseIndex, isDeleting])

  return text
}
