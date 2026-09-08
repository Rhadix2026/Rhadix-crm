import React, { useEffect, useState, useRef } from 'react'
import { getMe, getAuthToken, clearAuthToken } from './services/api'
import { currentBrand } from './brand'
import { Nav } from './components/UI'
import LoginScreen from './pages/LoginScreen'
import Dashboard from './pages/Dashboard'
import Relaties from './pages/Relaties'
import Krachtenveld from './pages/Krachtenveld'
import Contactpersonen from './pages/Contactpersonen'
import Opvolging from './pages/Opvolging'
import Beheer from './pages/Beheer'
import Taken from './pages/Taken'

const IS_STAGING = (import.meta.env.VITE_RHADIX_ENV || '').toLowerCase() === 'staging'

function GeenAppToegang({ melding, onLogout }) {
  return (
    <div style={{ padding: 48, display: 'flex', justifyContent: 'center' }}>
      <div style={{
        maxWidth: 560, borderLeft: '4px solid #c0392b', background: 'var(--card, #fff)',
        borderRadius: 8, padding: '20px 24px', boxShadow: '0 1px 3px rgba(0,0,0,.12)',
      }}>
        <h2 style={{ margin: '0 0 8px', fontSize: 18 }}>Geen toegang tot Rhadix CRM</h2>
        <p style={{ margin: '0 0 16px', lineHeight: 1.5 }}>{melding}</p>
        <button onClick={onLogout}>Uitloggen</button>
      </div>
    </div>
  )
}

export default function App() {
  const [authUser, setAuthUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [geenToegang, setGeenToegang] = useState(null)
  const [tab, setTab] = useState('dashboard')
  const histRef = useRef([])
  function goTab(t) { if (t !== tab) { histRef.current.push(tab); setTab(t) } }
  function back()   { const h = histRef.current; if (h.length) { setTab(h.pop()) } else if (typeof window !== 'undefined') { window.history.back() } }
  const [brandV, setBrandV] = useState(currentBrand())

  useEffect(() => {
    const onUnauth = () => setAuthUser(null)
    window.addEventListener('rhadix:unauthorized', onUnauth)
    return () => window.removeEventListener('rhadix:unauthorized', onUnauth)
  }, [])

  useEffect(() => {
    const onGeenToegang = (e) => setGeenToegang(e.detail)
    window.addEventListener('rhadix:geen-app-toegang', onGeenToegang)
    return () => window.removeEventListener('rhadix:geen-app-toegang', onGeenToegang)
  }, [])

  useEffect(() => {
    // SSO-bootstrap: altijd /auth/me proberen. Met het centrale rhadix_sso-cookie
    // (same-origin) logt de gebruiker automatisch in, ook zonder opgeslagen token.
    getMe().then(setAuthUser).catch(() => clearAuthToken()).finally(() => setLoading(false))
  }, [])

  function toggleBrand() {
    const next = currentBrand() === 'suresync' ? 'rhadix' : 'suresync'
    document.documentElement.dataset.brand = next
    sessionStorage.setItem('rhadix_brand', next)
    setBrandV(next)
  }
  function logout() { clearAuthToken(); setAuthUser(null); setGeenToegang(null) }

  if (loading) return null
  if (!authUser) return <LoginScreen onLogin={setAuthUser} onBrandToggle={IS_STAGING ? toggleBrand : null} brandV={brandV} />
  if (geenToegang) return <GeenAppToegang melding={geenToegang} onLogout={logout} />

  const isAdmin = authUser.role === 'PLATFORM_ADMIN' || authUser.role === 'ORG_ADMIN'
  const tabs = [
    { key:'dashboard', label:'Dashboard' },
    { key:'relaties', label:'Relaties' },
    { key:'krachtenveld', label:'Krachtenveld' },
    { key:'contacten', label:'Contactpersonen' },
    { key:'opvolging', label:'Opvolging' },
    { key:'taken', label:'Taken' },
    ...(isAdmin ? [{ key:'beheer', label:'Beheer' }] : []),
  ]

  return (
    <div>
      <Nav tabs={tabs} active={tab} onTab={goTab} onBack={back}
           authUser={authUser} onLogout={logout} />
      <div className="page">
        {tab === 'dashboard'    && <Dashboard onGo={goTab} />}
        {tab === 'relaties'     && <Relaties />}
        {tab === 'krachtenveld' && <Krachtenveld />}
        {tab === 'contacten'    && <Contactpersonen />}
        {tab === 'opvolging'    && <Opvolging />}
        {tab === 'taken'        && <Taken authUser={authUser} />}
        {tab === 'beheer'       && <Beheer authUser={authUser} />}
      </div>
    </div>
  )
}
