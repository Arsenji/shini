const API_BASE = import.meta.env.VITE_API_URL ?? ''

export type OrderPayload = {
  name: string
  width: number
  profile: number
  radius: number
  phone: string
}

export type OrderResponse = {
  success: boolean
  order_id: number
}

export async function createOrder(payload: OrderPayload): Promise<OrderResponse> {
  const response = await fetch(`${API_BASE}/api/orders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    let detail = 'Не удалось отправить заявку'
    try {
      const data = (await response.json()) as { detail?: string }
      if (data.detail) detail = data.detail
    } catch {
      // ignore invalid JSON
    }
    throw new Error(detail)
  }

  return response.json() as Promise<OrderResponse>
}
