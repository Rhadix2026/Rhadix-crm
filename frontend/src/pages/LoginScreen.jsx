import React, { useState } from 'react'
import { login, getMe } from '../services/api'
import { brandInfo } from '../brand'
import { BrandMark } from '../components/UI'

export default function LoginScreen({ onLogin, onBrandToggle }) {
  const b = brandInfo()
  const [email, setEmail] = useState('')
  const [pwd, setPwd] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault(); setErr(''); setBusy(true)
    try { await login(email.trim(), pwd); onLogin(await getMe()) }
    catch (ex) { setErr(ex.message || 'Inloggen mislukt') }
    finally { setBusy(false) }
  }

  return (
    <div style={{ minHeight:'100vh', display:'grid', gridTemplateColumns:'1fr', placeItems:'center',
      background:'linear-gradient(135deg,var(--brand-hero),var(--brand-dark))', padding:20 }}>
      <div className="card" style={{ width:'100%', maxWidth:400, padding:'34px 32px' }}>
        <div className="row" style={{ gap:12, marginBottom:6 }}>
          <BrandMark size={40} />
          <div>
            <div style={{ fontWeight:800, fontSize:20, color:'var(--brand)' }}>{b.naam} <span style={{ color:'var(--accent)' }}>CRM</span></div>
            <div className="small muted" style={{ letterSpacing:'1.5px' }}>{b.tagline}</div>
          </div>
        </div>
        <p className="muted small" style={{ margin:'8px 0 20px' }}>
          Stakeholder- en krachtenveldbeheer rond RSO's en zorgaanbieders.
        </p>
        <form onSubmit={submit}>
          <div className="field"><label>E-mailadres</label>
            <input className="input" type="email" value={email} autoFocus
              onChange={e => setEmail(e.target.value)} placeholder="admin@rhadix.nl" /></div>
          <div className="field"><label>Wachtwoord</label>
            <input className="input" type="password" value={pwd}
              onChange={e => setPwd(e.target.value)} placeholder="••••••••" /></div>
          {err && <div className="badge b-red" style={{ marginBottom:12 }}>{err}</div>}
          <button className="btn btn-primary" style={{ width:'100%', padding:'10px' }} disabled={busy}>
            {busy ? 'Bezig…' : 'Inloggen'}
          </button>
        </form>
        {onBrandToggle && (
          <button className="btn-ghost small" style={{ marginTop:14, width:'100%' }} onClick={onBrandToggle}>
            Wissel huisstijl (staging)
          </button>
        )}
      </div>
    </div>
  )
}
