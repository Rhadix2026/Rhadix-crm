import React, { useEffect, useState } from 'react'
import { listOrgs, getOrg, createOrg, updateOrg, deleteOrg } from '../services/api'
import { PageHead, BetrouwBadge, Modal, Field, Toast, Bullets } from '../components/UI'

const LEEG = { soort:'VVT', naam:'', type:'', werkgebied:'', cluster:'', provincies:'', website:'',
  bron_url:'', bron_opmerking:'', aantal_aangesloten:null, focus_themas:'', rso_naam:'',
  betrouwbaarheid:'', onderbouwing:'', actie_validatie:'' }

export default function Relaties() {
  const [soort, setSoort] = useState('')
  const [q, setQ] = useState('')
  const [rows, setRows] = useState([])
  const [detail, setDetail] = useState(null)
  const [edit, setEdit] = useState(null)
  const [toast, setToast] = useState('')

  function load() {
    const p = new URLSearchParams()
    if (soort) p.set('soort', soort)
    if (q) p.set('q', q)
    const qs = p.toString()
    listOrgs(qs ? `?${qs}` : '').then(setRows)
  }
  useEffect(() => { load() }, [soort])
  useEffect(() => { const t = setTimeout(load, 250); return () => clearTimeout(t) }, [q])

  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2200) }
  async function open(id) { setDetail(await getOrg(id)) }
  async function save(body) {
    if (edit.id) await updateOrg(edit.id, body); else await createOrg(body)
    setEdit(null); load(); flash('Opgeslagen')
  }
  async function remove(id) {
    if (!confirm('Relatie verwijderen?')) return
    await deleteOrg(id); setDetail(null); load(); flash('Verwijderd')
  }

  return (
    <div>
      <PageHead title="Relaties" sub="RSO's en zorgaanbieders (VVT). Indicatieve mapping — valideren vóór formeel gebruik."
        actions={<button className="btn btn-primary" onClick={() => setEdit({ ...LEEG })}>+ Relatie</button>} />

      <div className="card card-pad row" style={{ marginBottom:14, gap:10 }}>
        <select className="select" style={{ width:160 }} value={soort} onChange={e => setSoort(e.target.value)}>
          <option value="">Alle soorten</option><option value="RSO">RSO</option><option value="VVT">Zorgaanbieder</option>
        </select>
        <input className="input" placeholder="Zoek op naam, regio of provincie…" value={q} onChange={e => setQ(e.target.value)} />
        <span className="muted small" style={{ whiteSpace:'nowrap' }}>{rows.length} resultaten</span>
      </div>

      <div className="card" style={{ overflow:'hidden' }}>
        <table className="tbl">
          <thead><tr><th>Soort</th><th>Naam</th><th>Werkgebied</th><th>RSO</th><th>Betrouwbaarheid</th><th>Contacten</th></tr></thead>
          <tbody>
            {rows.map(o => (
              <tr key={o.id} className="clickable" onClick={() => open(o.id)}>
                <td><span className={`badge ${o.soort === 'RSO' ? 'b-navy' : 'b-grey'}`}>{o.soort}</span></td>
                <td><b>{o.naam}</b>{o.type && <div className="small muted">{o.type}</div>}</td>
                <td className="small muted">{o.werkgebied || '—'}</td>
                <td className="small">{o.rso_naam || (o.soort === 'RSO' ? `${o.aantal_aangesloten ?? 0} aanbieders` : '—')}</td>
                <td>{o.soort === 'VVT' ? <BetrouwBadge value={o.betrouwbaarheid} /> : '—'}</td>
                <td>{o.aantal_contacten || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {detail && (
        <Modal wide title={detail.naam} onClose={() => setDetail(null)}
          footer={<>
            <button className="btn btn-danger" onClick={() => remove(detail.id)}>Verwijderen</button>
            <button className="btn" onClick={() => { setEdit(detail); setDetail(null) }}>Bewerken</button>
            <button className="btn btn-primary" onClick={() => setDetail(null)}>Sluiten</button>
          </>}>
          <div className="row" style={{ gap:8, marginBottom:6 }}>
            <span className={`badge ${detail.soort === 'RSO' ? 'b-navy' : 'b-grey'}`}>{detail.soort}</span>
            {detail.soort === 'VVT' && <BetrouwBadge value={detail.betrouwbaarheid} />}
            {detail.rso_naam && <span className="badge b-blue">RSO: {detail.rso_naam}</span>}
          </div>
          <KV label="Type" v={detail.type} /><KV label="Werkgebied" v={detail.werkgebied} />
          <KV label="Provincie(s)" v={detail.provincies} /><KV label="Cluster" v={detail.cluster} />
          {detail.soort === 'RSO' && <KV label="Aangesloten aanbieders" v={detail.aantal_aangesloten} />}
          {detail.onderbouwing && <KV label="Onderbouwing" v={detail.onderbouwing} />}
          {detail.actie_validatie && <KV label="Actie / validatie" v={detail.actie_validatie} />}
          {detail.bron_url && <KV label="Bron" v={detail.bron_url} />}

          <div className="section-title">Contactpersonen ({detail.contactpersonen?.length || 0})</div>
          {detail.contactpersonen?.length
            ? detail.contactpersonen.map(c => (
                <div key={c.id} className="spread" style={{ borderBottom:'1px dashed var(--border)', padding:'5px 0' }}>
                  <div><b>{c.naam || '—'}</b> <span className="muted small">{c.functie}</span></div>
                  <div className="small muted">{c.email || c.rolniveau || ''}</div>
                </div>))
            : <span className="muted small">Nog geen contactpersonen.</span>}

          <div className="section-title">Krachtenvelden ({detail.krachtenvelden?.length || 0})</div>
          {detail.krachtenvelden?.length
            ? detail.krachtenvelden.map(k => <div key={k.id} className="small">• {k.titel} — {k.aantal_stakeholders} stakeholders</div>)
            : <span className="muted small">Nog geen krachtenveld-analyse.</span>}
        </Modal>
      )}

      {edit && <OrgForm data={edit} onClose={() => setEdit(null)} onSave={save} />}
      <Toast msg={toast} />
    </div>
  )
}

function KV({ label, v }) {
  if (v === null || v === undefined || v === '') return null
  return <div style={{ margin:'4px 0' }}><span className="muted small">{label}: </span><span>{v}</span></div>
}

function OrgForm({ data, onClose, onSave }) {
  const [f, setF] = useState(data)
  const set = (k, v) => setF(p => ({ ...p, [k]: v }))
  const isRso = f.soort === 'RSO'
  function submit() {
    const body = { ...f }
    body.aantal_aangesloten = body.aantal_aangesloten ? Number(body.aantal_aangesloten) : null
    onSave(body)
  }
  return (
    <Modal wide title={data.id ? 'Relatie bewerken' : 'Nieuwe relatie'} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Annuleren</button>
        <button className="btn btn-primary" onClick={submit} disabled={!f.naam}>Opslaan</button></>}>
      <div className="grid" style={{ gridTemplateColumns:'1fr 1fr' }}>
        <Field label="Soort"><select className="select" value={f.soort} onChange={e => set('soort', e.target.value)}>
          <option value="VVT">Zorgaanbieder</option><option value="RSO">RSO</option></select></Field>
        <Field label="Naam"><input className="input" value={f.naam} onChange={e => set('naam', e.target.value)} /></Field>
        <Field label="Type"><input className="input" value={f.type || ''} onChange={e => set('type', e.target.value)} /></Field>
        <Field label="Werkgebied"><input className="input" value={f.werkgebied || ''} onChange={e => set('werkgebied', e.target.value)} /></Field>
        <Field label="Provincie(s)"><input className="input" value={f.provincies || ''} onChange={e => set('provincies', e.target.value)} /></Field>
        <Field label="Cluster"><input className="input" value={f.cluster || ''} onChange={e => set('cluster', e.target.value)} /></Field>
        {isRso
          ? <>
              <Field label="Aangesloten aanbieders"><input className="input" type="number" value={f.aantal_aangesloten ?? ''} onChange={e => set('aantal_aangesloten', e.target.value)} /></Field>
              <Field label="Focus-thema's"><input className="input" value={f.focus_themas || ''} onChange={e => set('focus_themas', e.target.value)} /></Field>
            </>
          : <>
              <Field label="Indicatieve RSO"><input className="input" value={f.rso_naam || ''} onChange={e => set('rso_naam', e.target.value)} /></Field>
              <Field label="Betrouwbaarheid"><select className="select" value={f.betrouwbaarheid || ''} onChange={e => set('betrouwbaarheid', e.target.value)}>
                <option value="">—</option><option>Hoog</option><option>Midden</option><option>Laag</option></select></Field>
            </>}
      </div>
      <Field label="Bron-URL"><input className="input" value={f.bron_url || ''} onChange={e => set('bron_url', e.target.value)} /></Field>
      {!isRso && <Field label="Onderbouwing"><textarea className="input" value={f.onderbouwing || ''} onChange={e => set('onderbouwing', e.target.value)} /></Field>}
    </Modal>
  )
}
