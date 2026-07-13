/** Только цифры для числовых полей (размер шины). */
export function digitsOnly(value: string, maxLength = 3): string {
  return value.replace(/\D/g, '').slice(0, maxLength)
}

/** Телефон: цифры и ведущий «+». */
export function sanitizePhoneInput(value: string): string {
  const cleaned = value.replace(/[^\d+]/g, '')
  if (!cleaned) return ''

  // Если пользователь начинает ввод "не с +" и не с "8",
  // считаем, что это российский номер и подставляем +7.
  // Если ввёл просто "7" — подставляем "+" (получится +7...).
  if (cleaned.startsWith('+')) {
    return `+${cleaned.slice(1).replace(/\D/g, '')}`.slice(0, 12)
  }

  const digits = cleaned.replace(/\D/g, '')
  if (!digits) return ''

  // Начали с 8 — оставляем как есть (нормализация будет на backend)
  if (digits.startsWith('8')) {
    return digits.slice(0, 11)
  }

  // Начали с 7 — добавляем плюс
  if (digits.startsWith('7')) {
    return `+${digits}`.slice(0, 12)
  }

  // Любая другая цифра в начале — это обычно номер без кода страны
  return `+7${digits}`.slice(0, 12)
}

export function parseTireNumber(value: string): number | null {
  if (!/^\d{2,3}$/.test(value)) return null
  return Number(value)
}
