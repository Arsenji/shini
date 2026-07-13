const API_BASE = import.meta.env.VITE_API_URL ?? ''

export type OrderPayload = {
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
    throw new Error('Order request failed')
  }

  return response.json() as Promise<OrderResponse>
}
