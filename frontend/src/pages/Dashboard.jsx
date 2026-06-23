import React, { useEffect, useState } from 'react'
import { getDashboard } from '../services/api'
import { PageHead } from '../components/UI'

const QCOL = { 'Actief betrekken':'b-green', 'Tevreden houden':'b-red', 'Mee nemen':'b-amber', 'Informeren':'b-blue' }

export default function Dashboard({ onGo }) {
  const [d, setD] = useState(null)
  const [err, setErr] = useState('')
  useEffect(() => { getDashboard().then(setD).catch(e => setErr(e.message)) }, [])
  if (err) return <div className="badge b-red">{err}</div>
  if (!d) return <p className="muted">Laden…</p>

  const maxRso = Math.max(1, ...d.aanbieders_per_rso.map(x => x.aantal))
  return (
    <div>
      <PageHead title="Rapportage" sub="Overzicht van relaties, krachtenveld en opvolging — in dienst van de Rhadix Index." />
      <div className="stats" style={{ marginBottom:18 }}>
        <Tile n={d.rso_count} l="RSO's" onClick={() => onGo('relaties')} />
        <Tile n={d.aanbieder_count} l="Zorgaanbieders" onClick={() => onGo('relaties')} />
        <Tile n={d.contactpersoon_count} l="Contactpersonen" onClick={() => onGo('contacten')} />
        <Tile n={d.krachtenveld_count} l="Krachtenvelden" onClick={() => onGo('krachtenveld')} />
        <Tile n={d.stakeholder_count} l="Stakeholders" onClick={() => onGo('krachtenveld')} />
        <Tile n={d.open_activiteiten} l="Open acties" onClick={() => onGo('opvolging')} />
      </div>

      <div className="grid" style={{ gridTemplateColumns:'1.4fr 1fr' }}>
        <div className="card card-pad">
          <div className="section-title" style={{ marginTop:0 }}>Aanbieders per RSO</div>
          {d.aanbieders_per_rso.map(x => (
            <div key={x.rso} className="row" style={{ margin:'6px 0' }}>
              <div style={{ width:200, fontSize:12.5 }} className="muted">{x.rso}</div>
              <div style={{ flex:1, background:'var(--bg)', borderRadius:6, height:16 }}>
                <div style={{ width:`${x.aantal/maxRso*100}%`, background:'var(--accent)', height:'100%', borderRadius:6 }} />
              </div>
              <div style={{ width:28, textAlign:'right', fontWeight:700 }}>{x.aantal}</div>
            </div>
          ))}
        </div>
        <div className="grid">
          <div className="card card-pad">
            <div className="section-title" style={{ marginTop:0 }}>Stakeholders per kwadrant</div>
            {Object.entries(d.kwadranten).map(([k, v]) => (
              <div key={k} className="spread" style={{ margin:'7px 0' }}>
                <span className={`badge ${QCOL[k] || 'b-grey'}`}>{k}</span>
                <b>{v}</b>
              </div>
            ))}
          </div>
          <div className="card card-pad">
            <div className="section-title" style={{ marginTop:0 }}>Betrouwbaarheid mapping</div>
            {Object.entries(d.betrouwbaarheid).map(([k, v]) => (
              <div key={k} className="spread" style={{ margin:'6px 0' }}>
                <span className="muted">{k}</span><b>{v}</b>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function Tile({ n, l, onClick }) {
  return <div className="stat" style={{ cursor:'pointer' }} onClick={onClick}>
    <div className="n">{n}</div><div className="l">{l}</div></div>
}
