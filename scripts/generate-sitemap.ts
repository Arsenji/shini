import { writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { SITE_ORIGIN } from '../src/lib/seo.ts'
import {
  getCanonicalTireOffers,
  getCanonicalWheelOffers,
  getProductRedirects,
} from '../src/lib/productUrls.ts'

function urlEntry(loc: string, priority: string, changefreq = 'weekly'): string {
  return `  <url>
    <loc>${loc}</loc>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
  </url>`
}

const tireOffers = getCanonicalTireOffers()
const wheelOffers = getCanonicalWheelOffers()
const redirects = getProductRedirects()

const urls = [
  urlEntry(`${SITE_ORIGIN}/`, '1.0'),
  urlEntry(`${SITE_ORIGIN}/tires`, '0.9'),
  urlEntry(`${SITE_ORIGIN}/wheels`, '0.9'),
  urlEntry(`${SITE_ORIGIN}/privacy-policy`, '0.5', 'yearly'),
  urlEntry(`${SITE_ORIGIN}/personal-data-consent`, '0.5', 'yearly'),
  ...tireOffers.map((offer) => urlEntry(`${SITE_ORIGIN}${offer.path}`, '0.7')),
  ...wheelOffers.map((offer) => urlEntry(`${SITE_ORIGIN}${offer.path}`, '0.7')),
]

const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.join('\n')}
</urlset>
`

const sitemapOut = resolve(process.cwd(), 'public/sitemap.xml')
writeFileSync(sitemapOut, xml, 'utf8')

const redirectMap: Record<string, string> = {}
for (const { from, to } of redirects) {
  redirectMap[from] = to
}
const redirectsOut = resolve(process.cwd(), 'public/product-redirects.json')
writeFileSync(redirectsOut, `${JSON.stringify(redirectMap, null, 2)}\n`, 'utf8')

console.log(`sitemap.xml: ${urls.length} URLs → ${sitemapOut}`)
console.log(`product-redirects.json: ${redirects.length} redirects → ${redirectsOut}`)
