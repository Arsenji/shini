/** Production site origin for canonical, OG, sitemap */
export const SITE_ORIGIN = 'https://xn----7sbhhcda8aj3ai3a9g.shop'

export function absoluteUrl(path = '/'): string {
  if (!path || path === '/') return `${SITE_ORIGIN}/`
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${SITE_ORIGIN}${normalized}`
}

export type SeoProps = {
  title: string
  description: string
  path?: string
  image?: string
  type?: 'website' | 'product'
  jsonLd?: Record<string, unknown> | Record<string, unknown>[]
}
