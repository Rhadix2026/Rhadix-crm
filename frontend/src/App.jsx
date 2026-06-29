import React, { useEffect, useState } from 'react'
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

export default function App() {
  const [authUser, setAuthUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('dashboard')
  const [brandV, setBrandV] = useState(currentBrand())

  useEffect(() => {
    const onUnauth = () => setAuthUser(null)
    window.addEventListener('rhadix:unauthorized', onUnauth)
    return () => window.removeEventListener('rhadix:unauthorized', onUnauth)
  }, [])

  useEffect(() => {
    if (getAuthToken()) {
      getMe().then(setAuthUser).catch(() => clearAuthToken()).finally(() => setLoading(false))
    } else setLoading(false)
  }, [])

  function toggleBrand() {
    const next = currentBrand() === 'suresync' ? 'rhadix' : 'suresync'
    document.documentElement.dataset.brand = next
    sessionStorage.setItem('rhadix_brand', next)
    setBrandV(next)
  }
  function logout() { clearAuthToken(); setAuthUser(null) }

  if (loading) return null
  if (!authUser) return <LoginScreen onLogin={setAuthUser} onBrandToggle={IS_STAGING ? toggleBrand : null} brandV={brandV} />

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
      <Nav tabs={tabs} active={tab} onTab={setTab}
           onBrandToggle={IS_STAGING ? toggleBrand : null}
           authUser={authUser} onLogout={logout} />
      <div className="page">
        {tab === 'dashboard'    && <Dashboard onGo={setTab} />}
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
