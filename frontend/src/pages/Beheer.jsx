import React, { useEffect, useState } from 'react'
import { listOrgUsers, platformStats } from '../services/api'
import { PageHead, platformUrl } from '../components/UI'

const ROL = { PLATFORM_ADMIN:'b-navy', ORG_ADMIN:'b-blue', ORG_USER:'b-grey' }

export default function Beheer({ authUser }) {
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState(null)
  const isPlatform = authUser.role === 'PLATFORM_ADMIN'

  function load() {
    listOrgUsers().then(setUsers).catch(() => {})
    if (isPlatform) platformStats().then(setStats).catch(() => {})
  }
  useEffect(() => { load() }, [])


  return (
    <div>
      <PageHead title="Beheer"
        sub="Overzicht van de gebruikers van uw organisatie in deze applicatie. Accounts, wachtwoorden en applicatietoewijzingen worden centraal beheerd op het Rhadix-platform."
        actions={<button className="btn" onClick={() => { window.location.href = platformUrl() }}>▦ Naar het Platform</button>} />

      {isPlatform && stats && (
        <div className="stats" style={{ marginBottom:16 }}>
          <div className="stat"><div className="n">{stats.tenants}</div><div className="l">Organisaties</div></div>
          <div className="stat"><div className="n">{stats.users}</div><div className="l">Gebruikers</div></div>
          <div className="stat"><div className="n">{stats.active_users}</div><div className="l">Actief</div></div>
        </div>
      )}

      <div className="card" style={{ overflow:'hidden' }}>
        <table className="tbl">
          <thead><tr><th>Naam</th><th>E-mail</th><th>Rol</th><th>Status</th><th>Laatste login</th></tr></thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td><b>{u.full_name || '—'}</b></td>
                <td className="small">{u.email}</td>
                <td><span className={`badge ${ROL[u.role] || 'b-grey'}`}>{u.role}</span></td>
                <td>{u.is_active ? <span className="badge b-green">Actief</span> : <span className="badge b-red">Inactief</span>}</td>
                <td className="small muted">{u.last_login_at ? new Date(u.last_login_at).toLocaleDateString('nl-NL') : '—'}</td>

              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card card-pad" style={{ marginTop:14 }}>
        <div className="section-title" style={{ marginTop:0 }}>Licentiemodule</div>
        <p className="small muted">Het aanmaken van gebruikers, het instellen van wachtwoorden en het koppelen van
          applicaties aan organisaties en gebruikers verloopt centraal via het Rhadix-platform. Een nieuwe gebruiker
          verschijnt hier vanzelf na zijn eerste login.</p>
      </div>

    </div>
  )
}
