import React, { useEffect, useState } from 'react'
import { listAct, createAct, updateAct, deleteAct, listOrgs } from '../services/api'
import { PageHead, Modal, Field, Toast } from '../components/UI'

const LEEG = { titel:'', soort:'taak', status:'open', datum:'', eigenaar:'', omschrijving:'', organisatie_id:'' }
const SOORT = { taak:'b-blue', afspraak:'b-amber', notitie:'b-grey' }

export default function Opvolging() {
  const [rows, setRows] = useState([])
  const [filter, setFilter] = useState('')
  const [orgs, setOrgs] = useState([])
  const [edit, setEdit] = useState(null)
  const [toast, setToast] = useState('')

  function load() { listAct(filter ? `?status=${filter}` : '').then(setRows) }
  useEffect(() => { load() }, [filter])
  useEffect(() => { listOrgs().then(setOrgs) }, [])
  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2000) }

  async function save(body) {
    const b = { ...body, organisatie_id: body.organisatie_id || null, datum: body.datum || null }
    if (edit.id) await updateAct(edit.id, b); else await createAct(b)
    setEdit(null); load(); flash('Opgeslagen')
  }
  async function toggle(a) { await updateAct(a.id, { ...a, status: a.status === 'open' ? 'afgerond' : 'open', organisatie_id: a.organisatie_id || null }); load() }
  async function remove(id) { await deleteAct(id); load(); flash('Verwijderd') }

  const orgName = id => orgs.find(o => o.id === id)?.naam || ''
  return (
    <div>
      <PageHead title="Opvolging" sub="Taken, afspraken en notities per relatie."
        actions={<button className="btn btn-primary" onClick={() => setEdit({ ...LEEG })}>+ Actie</button>} />
      <div className="card card-pad row" style={{ marginBottom:14, gap:8 }}>
        {['', 'open', 'afgerond'].map(s => (
          <button key={s} className={`btn btn-sm ${filter === s ? 'btn-primary' : ''}`} onClick={() => setFilter(s)}>
            {s === '' ? 'Alles' : s === 'open' ? 'Open' : 'Afgerond'}</button>
        ))}
      </div>
      <div className="card" style={{ overflow:'hidden' }}>
        <table className="tbl">
          <thead><tr><th></th><th>Titel</th><th>Soort</th><th>Relatie</th><th>Datum</th><th>Eigenaar</th><th></th></tr></thead>
          <tbody>
            {rows.map(a => (
              <tr key={a.id}>
                <td><input type="checkbox" checked={a.status === 'afgerond'} onChange={() => toggle(a)} /></td>
                <td style={{ textDecoration: a.status === 'afgerond' ? 'line-through' : 'none' }}>
                  <b>{a.titel}</b>{a.omschrijving && <div className="small muted">{a.omschrijving}</div>}</td>
                <td><span className={`badge ${SOORT[a.soort] || 'b-grey'}`}>{a.soort}</span></td>
                <td className="small muted">{orgName(a.organisatie_id) || '—'}</td>
                <td className="small">{a.datum || '—'}</td>
                <td className="small">{a.eigenaar || '—'}</td>
                <td className="row" style={{ gap:4 }}>
                  <button className="btn-ghost small" onClick={() => setEdit(a)}>bewerk</button>
                  <button className="btn-ghost small" style={{ color:'var(--red)' }} onClick={() => remove(a.id)}>×</button>
                </td>
              </tr>
            ))}
            {!rows.length && <tr><td colSpan={7} className="muted small" style={{ padding:18 }}>Geen acties.</td></tr>}
          </tbody>
        </table>
      </div>
      {edit && <ActForm data={edit} orgs={orgs} onClose={() => setEdit(null)} onSave={save} />}
      <Toast msg={toast} />
    </div>
  )
}

function ActForm({ data, orgs, onClose, onSave }) {
  const [f, setF] = useState(data)
  const set = (k, v) => setF(p => ({ ...p, [k]: v }))
  return (
    <Modal title={data.id ? 'Actie bewerken' : 'Nieuwe actie'} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Annuleren</button>
        <button className="btn btn-primary" disabled={!f.titel} onClick={() => onSave(f)}>Opslaan</button></>}>
      <Field label="Titel"><input className="input" value={f.titel} onChange={e => set('titel', e.target.value)} /></Field>
      <div className="grid" style={{ gridTemplateColumns:'1fr 1fr' }}>
        <Field label="Soort"><select className="select" value={f.soort} onChange={e => set('soort', e.target.value)}>
          <option value="taak">Taak</option><option value="afspraak">Afspraak</option><option value="notitie">Notitie</option></select></Field>
        <Field label="Status"><select className="select" value={f.status} onChange={e => set('status', e.target.value)}>
          <option value="open">Open</option><option value="afgerond">Afgerond</option></select></Field>
        <Field label="Datum"><input className="input" type="date" value={f.datum || ''} onChange={e => set('datum', e.target.value)} /></Field>
        <Field label="Eigenaar"><input className="input" value={f.eigenaar || ''} onChange={e => set('eigenaar', e.target.value)} /></Field>
      </div>
      <Field label="Relatie"><select className="select" value={f.organisatie_id || ''} onChange={e => set('organisatie_id', e.target.value)}>
        <option value="">—</option>{orgs.map(o => <option key={o.id} value={o.id}>{o.naam}</option>)}</select></Field>
      <Field label="Omschrijving"><textarea className="input" value={f.omschrijving || ''} onChange={e => set('omschrijving', e.target.value)} /></Field>
    </Modal>
  )
}
