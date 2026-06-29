import React, { useEffect, useState } from 'react'
import { listTasks, createTask, updateTask, deleteTask, assignableUsers } from '../services/api'
import { PageHead, Modal, Field, Toast } from '../components/UI'

const LEEG = { title:'', description:'', priority:'NORMAAL', due_date:'', assignee_id:'' }
const PRIO_BADGE = { HOOG:'b-amber', NORMAAL:'b-blue', LAAG:'b-grey' }
const STATUS_LABEL = { OPEN:'Open', IN_BEHANDELING:'In behandeling', KLAAR:'Klaar', GEANNULEERD:'Geannuleerd' }

export default function Taken({ authUser }) {
  const [rows, setRows]   = useState([])
  const [scope, setScope] = useState('mine')
  const [users, setUsers] = useState([])
  const [edit, setEdit]   = useState(null)
  const [toast, setToast] = useState('')

  function load() { listTasks(`?scope=${scope}`).then(setRows).catch(e => flash(e.message)) }
  useEffect(() => { load() }, [scope])
  useEffect(() => { assignableUsers().then(setUsers).catch(() => {}) }, [])
  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2200) }

  const userName = id => { const u = users.find(u => u.id === id); return u ? (u.name || u.email) : '' }

  async function save(body) {
    const b = { ...body, due_date: body.due_date || null, assignee_id: body.assignee_id || null }
    try {
      if (edit.id) await updateTask(edit.id, b); else await createTask(b)
      setEdit(null); load(); flash('Opgeslagen')
    } catch (e) { flash(e.message) }
  }
  async function setStatus(t, status) { try { await updateTask(t.id, { status }); load() } catch (e) { flash(e.message) } }
  async function remove(id) { try { await deleteTask(id); load(); flash('Verwijderd') } catch (e) { flash(e.message) } }

  const isAdmin = authUser?.role === 'PLATFORM_ADMIN' || authUser?.role === 'ORG_ADMIN'
  const scopes = [
    { key:'mine', label:'Mijn taken' },
    { key:'created', label:'Door mij aangemaakt' },
    { key:'all', label: isAdmin ? 'Hele organisatie' : 'Alles van mij' },
  ]

  return (
    <div>
      <PageHead title="Taken" sub="Werk je toegewezen taken af en wijs acties toe aan collega's."
        actions={<button className="btn btn-primary" onClick={() => setEdit({ ...LEEG })}>+ Taak</button>} />

      <div className="card card-pad row" style={{ marginBottom:14, gap:8 }}>
        {scopes.map(s => (
          <button key={s.key} className={`btn btn-sm ${scope === s.key ? 'btn-primary' : ''}`}
            onClick={() => setScope(s.key)}>{s.label}</button>
        ))}
      </div>

      <div className="card" style={{ overflow:'hidden' }}>
        <table className="tbl">
          <thead><tr>
            <th></th><th>Taak</th><th>Prioriteit</th><th>Toegewezen aan</th><th>Deadline</th><th>Bron</th><th></th>
          </tr></thead>
          <tbody>
            {rows.map(t => {
              const klaar = t.status === 'KLAAR'
              return (
                <tr key={t.id}>
                  <td><input type="checkbox" checked={klaar}
                    onChange={() => setStatus(t, klaar ? 'OPEN' : 'KLAAR')} title="Markeer als klaar" /></td>
                  <td style={{ textDecoration: klaar ? 'line-through' : 'none' }}>
                    <b>{t.title}</b>
                    {t.description && <div className="small muted">{t.description}</div>}
                    {!klaar && t.status !== 'OPEN' && <span className="small muted"> · {STATUS_LABEL[t.status]}</span>}
                  </td>
                  <td><span className={`badge ${PRIO_BADGE[t.priority] || 'b-grey'}`}>{t.priority}</span></td>
                  <td className="small">{userName(t.assignee_id) || '—'}</td>
                  <td className="small">{t.due_date ? t.due_date.slice(0,10) : '—'}</td>
                  <td className="small muted">{t.source_label || (t.source_type || '—')}</td>
                  <td className="row" style={{ gap:4 }}>
                    {t.status !== 'IN_BEHANDELING' && !klaar &&
                      <button className="btn-ghost small" onClick={() => setStatus(t, 'IN_BEHANDELING')}>oppakken</button>}
                    <button className="btn-ghost small" onClick={() => setEdit(t)}>bewerk</button>
                    <button className="btn-ghost small" style={{ color:'var(--red)' }} onClick={() => remove(t.id)}>×</button>
                  </td>
                </tr>
              )
            })}
            {!rows.length && <tr><td colSpan={7} className="muted small" style={{ padding:18 }}>Geen taken.</td></tr>}
          </tbody>
        </table>
      </div>

      {edit && (
        <TaakModal edit={edit} users={users} onClose={() => setEdit(null)} onSave={save} />
      )}
      <Toast msg={toast} />
    </div>
  )
}

function TaakModal({ edit, users, onClose, onSave }) {
  const [f, setF] = useState({
    title: edit.title || '', description: edit.description || '',
    priority: edit.priority || 'NORMAAL',
    due_date: edit.due_date ? edit.due_date.slice(0,10) : '',
    assignee_id: edit.assignee_id || '',
  })
  const set = (k, v) => setF(s => ({ ...s, [k]: v }))
  return (
    <Modal title={edit.id ? 'Taak bewerken' : 'Nieuwe taak'} onClose={onClose}
      footer={<>
        <button className="btn" onClick={onClose}>Annuleren</button>
        <button className="btn btn-primary" disabled={!f.title.trim()} onClick={() => onSave(f)}>Opslaan</button>
      </>}>
      <Field label="Titel"><input className="inp" value={f.title} onChange={e => set('title', e.target.value)} autoFocus /></Field>
      <Field label="Omschrijving"><textarea className="inp" rows={3} value={f.description} onChange={e => set('description', e.target.value)} /></Field>
      <div className="row" style={{ gap:10 }}>
        <Field label="Prioriteit">
          <select className="inp" value={f.priority} onChange={e => set('priority', e.target.value)}>
            <option value="LAAG">Laag</option><option value="NORMAAL">Normaal</option><option value="HOOG">Hoog</option>
          </select>
        </Field>
        <Field label="Deadline"><input className="inp" type="date" value={f.due_date} onChange={e => set('due_date', e.target.value)} /></Field>
      </div>
      <Field label="Toewijzen aan">
        <select className="inp" value={f.assignee_id} onChange={e => set('assignee_id', e.target.value)}>
          <option value="">— Niemand —</option>
          {users.map(u => <option key={u.id} value={u.id}>{u.name || u.email}</option>)}
        </select>
      </Field>
    </Modal>
  )
}
