// brand.js — merk-laag (Rhadix / SureSync), gelijk aan de andere Rhadix-apps.
// Het actieve merk staat op <html data-brand="..."> en wordt in main.jsx gezet.

export const BRANDS = {
  rhadix: {
    key: 'rhadix',
    naam: 'Rhadix',
    product: 'Rhadix CRM',
    tagline: 'DATA DRIVEN HEALTHCARE',
  },
  suresync: {
    key: 'suresync',
    naam: 'SureSync',
    product: 'SureSync CRM',
    tagline: 'CONNECTED CARE DATA',
  },
}

export function getInitialBrand() {
  // Rhadix (navy) is standaard; alternatief merk alleen via expliciete VITE_BRAND.
  const env = (import.meta.env.VITE_BRAND || '').toLowerCase()
  return BRANDS[env] ? env : 'rhadix'
}

export function currentBrand() {
  if (typeof document === 'undefined') return 'rhadix'
  return document.documentElement.dataset.brand || 'rhadix'
}

export function brandInfo() {
  return BRANDS[currentBrand()] || BRANDS.rhadix
}
