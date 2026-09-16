import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'
import { getInitialBrand } from './brand'

// Omgeving (navy=prod, groen=staging) en merk (rhadix/suresync) op <html>
const env = (import.meta.env.VITE_RHADIX_ENV || 'development').toLowerCase()
if (env === 'staging') document.documentElement.dataset.env = 'staging'
document.documentElement.dataset.brand = getInitialBrand()

// Browser-terug na uitloggen mag geen ingelogd scherm meer tonen. Een pagina die
// de browser uit zijn back/forward-cache haalt wordt niet opnieuw opgebouwd: de
// SSO-bootstrap wordt dan overgeslagen en het oude scherm komt terug zoals het
// was. Opnieuw laden dwingt die sessiecontrole af.
window.addEventListener('pageshow', (e) => { if (e.persisted) window.location.reload() })

createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
)
