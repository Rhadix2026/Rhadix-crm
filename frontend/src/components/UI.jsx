import React from 'react'
import { brandInfo, currentBrand } from '../brand'

// Terug-naar-platform: naar het portaal 'kies een applicatie' (env-afhankelijk).
function _platformUrl() {
  if (import.meta.env.VITE_PLATFORM_URL) return import.meta.env.VITE_PLATFORM_URL
  const stag = typeof location !== 'undefined' && location.hostname.includes('staging')
  return stag ? 'https://app-staging.rhadix.nl' : 'https://app.rhadix.nl'
}


// ── Merk-logo (knoop-netwerk in de huisstijl) ───────────────────────────────
export function BrandMark({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden="true">
      <circle cx="20" cy="20" r="19" fill="var(--accent)" opacity="0.18" />
      <line x1="20" y1="20" x2="11" y2="12" stroke="var(--accent)" strokeWidth="1.6" />
      <line x1="20" y1="20" x2="30" y2="13" stroke="var(--accent)" strokeWidth="1.6" />
      <line x1="20" y1="20" x2="13" y2="29" stroke="var(--accent)" strokeWidth="1.6" />
      <line x1="20" y1="20" x2="29" y2="28" stroke="var(--accent)" strokeWidth="1.6" />
      <circle cx="20" cy="20" r="4.4" fill="#fff" />
      <circle cx="11" cy="12" r="2.6" fill="var(--accent)" />
      <circle cx="30" cy="13" r="2.6" fill="var(--accent)" />
      <circle cx="13" cy="29" r="2.6" fill="var(--accent-soft)" />
      <circle cx="29" cy="28" r="2.6" fill="var(--accent-soft)" />
    </svg>
  )
}

export function BrandLogo({ onClick }) {
  const b = brandInfo()
  return (
    <button onClick={onClick} style={{ display:'flex', alignItems:'center', gap:10, background:'none',
      border:'none', cursor:onClick?'pointer':'default', padding:0 }}>
      <img src="/rhadix-logo.jpg" alt="Rhadix" style={{ height:36, width:'auto', objectFit:'contain' }} />
    </button>
  )
}

// ── Navigatie ───────────────────────────────────────────────────────────────
export function Nav({ tabs, active, onTab, onBack, authUser, onLogout }) {
  const brand = currentBrand()
  return (
    <div className="nav">
      <div className="row" style={{ gap:16 }}>
        <BrandLogo onClick={() => onTab(tabs[0].key)} />
        {onBack && <button className="nav-tab" onClick={onBack} title="Terug (1 stap)">← Terug</button>}
        <button className="nav-tab" onClick={() => { window.location.href = _platformUrl() }} title="Terug naar platform — kies een applicatie">▦ Platform</button>
        <div className="nav-tabs">
          {tabs.map(t => (
            <button key={t.key} className={`nav-tab ${active === t.key ? 'active' : ''}`}
              onClick={() => onTab(t.key)}>{t.label}</button>
          ))}
        </div>
      </div>
      <div className="nav-right">
        {authUser && <span className="small" style={{ color:'#cdd7e8' }}>{authUser.email}</span>}
        {onLogout && <button className="nav-tab" onClick={onLogout}>Uitloggen</button>}
      </div>
    </div>
  )
}

export function PageHead({ title, sub, actions }) {
  return (
    <div className="page-head spread">
      <div><h1>{title}</h1>{sub && <p>{sub}</p>}</div>
      {actions && <div className="row">{actions}</div>}
    </div>
  )
}

// ── Badges ────────────────────────────────────────────────────────────────
const NIVEAU_CLS = { hoog:'b-red', middel:'b-amber', laag:'b-green' }
export function NiveauBadge({ value, label }) {
  const cls = NIVEAU_CLS[(value || '').toLowerCase()] || 'b-grey'
  return <span className={`badge ${cls}`}>{label ? `${label}: ` : ''}{value || '—'}</span>
}
const BETROUW_CLS = { hoog:'b-green', midden:'b-amber', middel:'b-amber', laag:'b-red' }
export function BetrouwBadge({ value }) {
  const cls = BETROUW_CLS[(value || '').toLowerCase()] || 'b-grey'
  return <span className={`badge ${cls}`}>{value || 'Onbekend'}</span>
}
const HOUDING = {
  positief:{ c:'b-green', e:'☺' }, neutraal:{ c:'b-grey', e:'•' },
  onbekend:{ c:'b-grey', e:'?' }, negatief:{ c:'b-red', e:'☹' },
}
export function HoudingBadge({ value }) {
  const h = HOUDING[(value || '').toLowerCase()] || HOUDING.onbekend
  return <span className={`badge ${h.c}`}>{h.e} {value || 'Onbekend'}</span>
}

// ── Modal ────────────────────────────────────────────────────────────────
export function Modal({ title, onClose, children, footer, wide }) {
  return (
    <div className="modal-bg" onMouseDown={onClose}>
      <div className="modal" style={wide ? { maxWidth:760 } : undefined} onMouseDown={e => e.stopPropagation()}>
        <div className="modal-head">{title}<button className="btn-ghost" onClick={onClose} style={{ fontSize:20 }}>×</button></div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  )
}

export function Field({ label, children }) {
  return <div className="field"><label>{label}</label>{children}</div>
}

export function Toast({ msg }) { return msg ? <div className="toast">{msg}</div> : null }

// Meerdere Rhadix-collega's koppelen (extra accounthouders). `excludeId` = primair (uitgesloten).
export function TeamMultiSelect({ team = [], value = [], onChange, excludeId }) {
  const selected = new Set((value || []).map(String))
  const options = team.filter(t => String(t.id) !== String(excludeId || ''))
  function toggle(id) {
    const next = new Set(selected)
    next.has(String(id)) ? next.delete(String(id)) : next.add(String(id))
    onChange(Array.from(next))
  }
  if (!options.length) return <span className="muted small">Geen extra teamleden beschikbaar.</span>
  return (
    <div className="row" style={{ flexWrap:'wrap', gap:'6px 14px' }}>
      {options.map(t => (
        <label key={t.id} className="row small" style={{ gap:6, cursor:'pointer', alignItems:'center' }}>
          <input type="checkbox" checked={selected.has(String(t.id))} onChange={() => toggle(t.id)} />
          {t.naam}
        </label>
      ))}
    </div>
  )
}

// regels (newline-gescheiden tekst) → lijst
export function Bullets({ text }) {
  const lines = (text || '').split('\n').map(s => s.trim()).filter(Boolean)
  if (!lines.length) return <span className="muted small">—</span>
  return <ul className="list-clean">{lines.map((l, i) => <li key={i}>{l}</li>)}</ul>
}
