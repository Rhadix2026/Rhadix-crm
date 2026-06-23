import React, { useEffect, useState } from 'react'
import { listOrgUsers, createOrgUser, toggleUser, resetUserPwd, platformStats } from '../services/api'
import { PageHead, Modal, Field, Toast } from '../components/UI'

const ROL = { PLATFORM_ADMIN:'b-navy', ORG_ADMIN:'b-blue', ORG_USER:'b-grey' }
const LEEG = { email:'', full_name:'', password:'', role:'ORG_USER' }

export default function Beheer({ authUser }) {
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState(null)
  const [add, setAdd] = useState(null)
  const [toast, setToast] = useState('')
  const isPlatform = authUser.role === 'PLATFORM_ADMIN'

  function load() {
    listOrgUsers().then(setUsers).catch(() => {})
    if (isPlatform) platformStats().then(setStats).catch(() => {})
  }
  useEffect(() => { load() }, [])
  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2200) }

  async function save(body) {
    try { await createOrgUser(body); setAdd(null); load(); flash('Gebruiker toegevoegd') }
    catch (e) { alert(e.message) }
  }
  async function toggle(u) { await toggleUser(u.id); load() }
  async function reset(u) {
    const pw = prompt(`Nieuw wachtwoord voor ${u.email} (min. 12 tekens):`)
    if (!pw) return
    try { await resetUserPwd(u.id, pw); flash('Wachtwoord gereset') } catch (e) { alert(e.message) }
  }

  return (
    <div>
      <PageHead title="Beheer" sub="Gebruikers binnen je organisatie. Toegang tot applicaties verloopt via de centrale licentiemodule."
        actions={<button className="btn btn-primary" onClick={() => setAdd({ ...LEEG })}>+ Gebruiker</button>} />

      {isPlatform && stats && (
        <div className="stats" style={{ marginBottom:16 }}>
          <div className="stat"><div className="n">{stats.tenants}</div><div className="l">Organisaties</div></div>
          <div className="stat"><div className="n">{stats.users}</div><div className="l">Gebruikers</div></div>
          <div className="stat"><div className="n">{stats.active_users}</div><div className="l">Actief</div></div>
        </div>
      )}

      <div className="card" style={{ overflow:'hidden' }}>
        <table className="tbl">
          <thead><tr><th>Naam</th><th>E-mail</th><th>Rol</th><th>Status</th><th>Laatste login</th><th></th></tr></thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td><b>{u.full_name || '—'}</b></td>
                <td className="small">{u.email}</td>
                <td><span className={`badge ${ROL[u.role] || 'b-grey'}`}>{u.role}</span></td>
                <td>{u.is_active ? <span className="badge b-green">Actief</span> : <span className="badge b-red">Inactief</span>}</td>
                <td className="small muted">{u.last_login_at ? new Date(u.last_login_at).toLocaleDateString('nl-NL') : '—'}</td>
                <td className="row" style={{ gap:6 }}>
                  <button className="btn-ghost small" onClick={() => reset(u)}>wachtwoord</button>
                  <button className="btn-ghost small" onClick={() => toggle(u)}>{u.is_active ? 'deactiveer' : 'activeer'}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card card-pad" style={{ marginTop:14 }}>
        <div className="section-title" style={{ marginTop:0 }}>Licentiemodule</div>
        <p className="small muted">Het koppelen van applicaties aan organisaties en gebruikers verloopt centraal
          via de licentiemodule van het Rhadix-platform. Deze functionaliteit wordt centraal beheerd; binnenkort
          ook hier zichtbaar.</p>
      </div>

      {add && <UserForm data={add} canPlatform={isPlatform} onClose={() => setAdd(null)} onSave={save} />}
      <Toast msg={toast} />
    </div>
  )
}

function UserForm({ data, canPlatform, onClose, onSave }) {
  const [f, setF] = useState(data)
  const set = (k, v) => setF(p => ({ ...p, [k]: v }))
  return (
    <Modal title="Nieuwe gebruiker" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Annuleren</button>
        <button className="btn btn-primary" disabled={!f.email || !f.password} onClick={() => onSave(f)}>Toevoegen</button></>}>
      <Field label="Naam"><input className="input" value={f.full_name} onChange={e => set('full_name', e.target.value)} /></Field>
      <Field label="E-mail"><input className="input" type="email" value={f.email} onChange={e => set('email', e.target.value)} /></Field>
      <Field label="Wachtwoord (min. 12 tekens)"><input className="input" type="text" value={f.password} onChange={e => set('password', e.target.value)} /></Field>
      <Field label="Rol"><select className="select" value={f.role} onChange={e => set('role', e.target.value)}>
        <option value="ORG_USER">Gebruiker</option><option value="ORG_ADMIN">Organisatiebeheerder</option>
        {canPlatform && <option value="PLATFORM_ADMIN">Platformbeheerder</option>}</select></Field>
    </Modal>
  )
}
