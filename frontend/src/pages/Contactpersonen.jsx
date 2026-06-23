import React, { useEffect, useState } from 'react'
import { listCps, createCp, updateCp, deleteCp, listOrgs } from '../services/api'
import { PageHead, Modal, Field, Toast } from '../components/UI'

const LEEG = { categorie:'RSO', organisatie_naam:'', organisatie_id:'', rso_regio:'', rolniveau:'',
  naam:'', functie:'', email:'', telefoon:'', zekerheid:'', bron_url:'', bron_type:'', opmerking:'' }
const ZCLS = { hoog:'b-green', middel:'b-amber', laag:'b-red' }

export default function Contactpersonen() {
  const [rows, setRows] = useState([])
  const [q, setQ] = useState('')
  const [orgs, setOrgs] = useState([])
  const [edit, setEdit] = useState(null)
  const [toast, setToast] = useState('')

  function load() { listCps(q ? `?q=${encodeURIComponent(q)}` : '').then(setRows) }
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t) }, [q])
  useEffect(() => { listOrgs().then(setOrgs) }, [])
  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2000) }

  async function save(body) {
    const b = { ...body, organisatie_id: body.organisatie_id || null }
    if (edit.id) await updateCp(edit.id, b); else await createCp(b)
    setEdit(null); load(); flash('Opgeslagen')
  }
  async function remove(id) { if (!confirm('Contactpersoon verwijderen?')) return; await deleteCp(id); load(); flash('Verwijderd') }

  return (
    <div>
      <PageHead title="Contactpersonen" sub="Bestuurlijke en IV/ICT-contacten bij RSO's, aanbieders en leveranciers."
        actions={<button className="btn btn-primary" onClick={() => setEdit({ ...LEEG })}>+ Contactpersoon</button>} />
      <div className="card card-pad row" style={{ marginBottom:14 }}>
        <input className="input" placeholder="Zoek op naam, organisatie of functie…" value={q} onChange={e => setQ(e.target.value)} />
        <span className="muted small" style={{ whiteSpace:'nowrap' }}>{rows.length} contacten</span>
      </div>
      <div className="card" style={{ overflow:'hidden' }}>
        <table className="tbl">
          <thead><tr><th>Naam</th><th>Organisatie</th><th>Rolniveau</th><th>Contact</th><th>Zekerheid</th><th></th></tr></thead>
          <tbody>
            {rows.map(c => (
              <tr key={c.id}>
                <td><b>{c.naam || '—'}</b>{c.functie && <div className="small muted">{c.functie}</div>}</td>
                <td className="small">{c.organisatie_naam}{c.rso_regio && <div className="muted">{c.rso_regio}</div>}</td>
                <td className="small">{c.rolniveau || '—'}</td>
                <td className="small">{c.email || c.telefoon || '—'}</td>
                <td>{c.zekerheid && <span className={`badge ${ZCLS[c.zekerheid.toLowerCase()] || 'b-grey'}`}>{c.zekerheid}</span>}</td>
                <td className="row" style={{ gap:4 }}>
                  <button className="btn-ghost small" onClick={() => setEdit(c)}>bewerk</button>
                  <button className="btn-ghost small" style={{ color:'var(--red)' }} onClick={() => remove(c.id)}>×</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {edit && <CpForm data={edit} orgs={orgs} onClose={() => setEdit(null)} onSave={save} />}
      <Toast msg={toast} />
    </div>
  )
}

function CpForm({ data, orgs, onClose, onSave }) {
  const [f, setF] = useState(data)
  const set = (k, v) => setF(p => ({ ...p, [k]: v }))
  return (
    <Modal wide title={data.id ? 'Contactpersoon bewerken' : 'Nieuwe contactpersoon'} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Annuleren</button>
        <button className="btn btn-primary" onClick={() => onSave(f)}>Opslaan</button></>}>
      <div className="grid" style={{ gridTemplateColumns:'1fr 1fr' }}>
        <Field label="Naam"><input className="input" value={f.naam || ''} onChange={e => set('naam', e.target.value)} /></Field>
        <Field label="Functie / rol"><input className="input" value={f.functie || ''} onChange={e => set('functie', e.target.value)} /></Field>
        <Field label="Categorie"><select className="select" value={f.categorie || ''} onChange={e => set('categorie', e.target.value)}>
          <option>RSO</option><option>VVT</option><option>Leverancier</option></select></Field>
        <Field label="Gekoppelde organisatie"><select className="select" value={f.organisatie_id || ''} onChange={e => set('organisatie_id', e.target.value)}>
          <option value="">— vrije tekst —</option>{orgs.map(o => <option key={o.id} value={o.id}>{o.naam}</option>)}</select></Field>
        <Field label="Organisatie (tekst)"><input className="input" value={f.organisatie_naam || ''} onChange={e => set('organisatie_naam', e.target.value)} /></Field>
        <Field label="RSO / regio"><input className="input" value={f.rso_regio || ''} onChange={e => set('rso_regio', e.target.value)} /></Field>
        <Field label="Rolniveau"><input className="input" value={f.rolniveau || ''} onChange={e => set('rolniveau', e.target.value)} placeholder="Bestuur/directie, IV/ICT…" /></Field>
        <Field label="Zekerheid"><select className="select" value={f.zekerheid || ''} onChange={e => set('zekerheid', e.target.value)}>
          <option value="">—</option><option>Hoog</option><option>Middel</option><option>Laag</option></select></Field>
        <Field label="E-mail"><input className="input" value={f.email || ''} onChange={e => set('email', e.target.value)} /></Field>
        <Field label="Telefoon"><input className="input" value={f.telefoon || ''} onChange={e => set('telefoon', e.target.value)} /></Field>
      </div>
      <Field label="Opmerking / actie"><textarea className="input" value={f.opmerking || ''} onChange={e => set('opmerking', e.target.value)} /></Field>
    </Modal>
  )
}
