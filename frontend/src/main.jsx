import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'
import { getInitialBrand } from './brand'

// Omgeving (navy=prod, groen=staging) en merk (rhadix/suresync) op <html>
const env = (import.meta.env.VITE_RHADIX_ENV || 'development').toLowerCase()
if (env === 'staging') document.documentElement.dataset.env = 'staging'
document.documentElement.dataset.brand = getInitialBrand()

createRoot(document.getElementById('root')).render(
  <React.StrictMode><App /></React.StrictMode>
)
