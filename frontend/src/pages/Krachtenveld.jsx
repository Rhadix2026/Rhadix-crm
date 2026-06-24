import React, { useEffect, useState } from 'react'
import { listKv, getKv, createKv, updateKv, deleteKv, addSh, updateSh, deleteSh, listOrgs, genereerKrachtenveld } from '../services/api'
import { PageHead, Modal, Field, Toast, Bullets, HoudingBadge, NiveauBadge } from '../components/UI'

const POS = { hoog:82, middel:50, laag:18 }  // betrokkenheid x%  (laag links, hoog rechts)
const INV = { hoog:18, middel:50, laag:82 }  // invloed y%       (hoog boven, laag onder)
const QCOLOR = { 'Actief betrekken':'#1e7d4f', 'Tevreden houden':'#c0392b', 'Mee nemen':'#b9770f', 'Informeren':'#3b5575' }
const LEEG_KV = { titel:'', regio:'', organisatie_id:'', bestuurlijk_orgaan:'', operationeel_orgaan:'',
  besluitvormingsproces:'', beslissingsfrequentie:'', kernopgave:'', beslissingsdrivers:'', belemmeringen:'',
  kansen:'', waarde:'', volgende_stappen:'', notities:'', eigenaar:'' }
const LEEG_SH = { naam:'', rol:'', invloed:'Middel', betrokkenheid:'Middel', houding:'Onbekend',
  verantwoordelijkheden:'', doelen_belangen:'', argumenten:'', belemmeringen:'', aanpak:'',
  laatste_contact:'', volgende_stap:'' }

export default function Krachtenveld() {
  const [list, setList] = useState([])
  const [sel, setSel] = useState(null)
  const [editKv, setEditKv] = useState(null)
  const [editSh, setEditSh] = useState(null)
  const [orgs, setOrgs] = useState([])
  const [toast, setToast] = useState('')
  const [genOpen, setGenOpen] = useState(false)
  const [genBusy, setGenBusy] = useState(false)

  function flash(m) { setToast(m); setTimeout(() => setToast(''), 2200) }
  function reloadList() { listKv().then(setList) }
  async function genereer(orgId) {
    setGenBusy(true)
    try {
      const kv = await genereerKrachtenveld(orgId)
      setGenOpen(false); reloadList(); setSel(await getKv(kv.id)); flash('Krachtenveld gegenereerd')
    } catch (e) { alert(e.message) }
    finally { setGenBusy(false) }
  }
  useEffect(() => { reloadList(); listOrgs('?soort=RSO').then(setOrgs) }, [])
  async function open(id) { setSel(await getKv(id)) }
  async function refresh() { if (sel) setSel(await getKv(sel.id)) }

  async function saveKv(body) {
    const saved = editKv.id ? await updateKv(editKv.id, body) : await createKv(body)
    setEditKv(null); reloadList(); setSel(await getKv(saved.id)); flash('Opgeslagen')
  }
  async function removeKv(id) {
    if (!confirm('Krachtenveld verwijderen?')) return
    await deleteKv(id); setSel(null); reloadList(); flash('Verwijderd')
  }
  async function saveSh(body) {
    if (editSh.id) await updateSh(editSh.id, body); else await addSh(sel.id, body)
    setEditSh(null); refresh(); flash('Stakeholder opgeslagen')
  }
  async function removeSh(id) { await deleteSh(id); refresh() }

  // ── lijst ──
  if (!sel) return (
    <div>
      <PageHead title="Krachtenveld" sub="Stakeholders, rollen, invloed en impact op besluitvorming."
        actions={<>
          <button className="btn" onClick={() => setGenOpen(true)}>✨ Genereer krachtenveld</button>
          <button className="btn btn-primary" onClick={() => setEditKv({ ...LEEG_KV })}>+ Krachtenveld</button>
        </>} />
      <div className="grid" style={{ gridTemplateColumns:'repeat(auto-fill,minmax(280px,1fr))' }}>
        {list.map(k => (
          <div key={k.id} className="card card-pad clickable" style={{ cursor:'pointer' }} onClick={() => open(k.id)}>
            <div style={{ fontWeight:700, color:'var(--brand)' }}>{k.titel}</div>
            <div className="muted small" style={{ margin:'4px 0 10px' }}>{k.regio || '—'}</div>
            <span className="badge b-navy">{k.aantal_stakeholders} stakeholders</span>
          </div>
        ))}
        {!list.length && <p className="muted">Nog geen krachtenvelden. Maak er één aan.</p>}
      </div>
      {genOpen && <GenModal orgs={orgs} busy={genBusy} onClose={() => setGenOpen(false)} onGen={genereer} />}
      {editKv && <KvForm data={editKv} orgs={orgs} onClose={() => setEditKv(null)} onSave={saveKv} />}
      <Toast msg={toast} />
    </div>
  )

  // ── detail ──
  return (
    <div>
      <PageHead title={sel.titel} sub={sel.regio}
        actions={<>
          <button className="btn" onClick={() => setSel(null)}>← Overzicht</button>
          <button className="btn" onClick={() => setEditKv(sel)}>Bewerken</button>
          <button className="btn btn-danger" onClick={() => removeKv(sel.id)}>Verwijderen</button>
        </>} />

      <div className="grid" style={{ gridTemplateColumns:'1.2fr 1fr', alignItems:'start' }}>
        {/* Matrix */}
        <div className="card card-pad">
          <div className="spread" style={{ marginBottom:8 }}>
            <div className="section-title" style={{ margin:0 }}>Krachtenveld & invloedsmatrix</div>
            <button className="btn btn-sm btn-accent" onClick={() => setEditSh({ ...LEEG_SH })}>+ Stakeholder</button>
          </div>
          <div className="matrix-wrap">
            <div className="axis-y">Invloed op besluitvorming →</div>
            <div style={{ flex:1 }}>
              <div className="matrix">
                <div className="q q-th"><span className="q-label">Tevreden houden</span></div>
                <div className="q q-ab"><span className="q-label">Actief betrekken</span></div>
                <div className="q q-in"><span className="q-label">Informeren</span></div>
                <div className="q q-mn"><span className="q-label">Mee nemen</span></div>
                {sel.stakeholders.map((s, i) => {
                  const x = POS[(s.betrokkenheid || 'middel').toLowerCase()] ?? 50
                  const y = INV[(s.invloed || 'middel').toLowerCase()] ?? 50
                  return (
                    <div key={s.id} className="sh-dot" style={{ left:`${x}%`, top:`${y}%` }} onClick={() => setEditSh(s)}>
                      <div className="pt" style={{ background:QCOLOR[s.kwadrant] || '#64748b' }}>{i + 1}</div>
                      <div className="nm">{s.naam}</div>
                    </div>
                  )
                })}
              </div>
              <div className="axis-x">Betrokkenheid bij Rhadix →</div>
            </div>
          </div>
        </div>

        {/* Stakeholderlijst */}
        <div className="card card-pad">
          <div className="section-title" style={{ marginTop:0 }}>Stakeholders ({sel.stakeholders.length})</div>
          {sel.stakeholders.map((s, i) => (
            <div key={s.id} style={{ borderBottom:'1px dashed var(--border)', padding:'8px 0' }}>
              <div className="spread">
                <div className="row" style={{ gap:8 }}>
                  <span className="pt" style={{ width:22, height:22, borderRadius:'50%', background:QCOLOR[s.kwadrant] || '#64748b',
                    color:'#fff', display:'inline-flex', alignItems:'center', justifyContent:'center', fontSize:11, fontWeight:700 }}>{i + 1}</span>
                  <div><b>{s.naam}</b>{s.rol && <div className="small muted">{s.rol}</div>}</div>
                </div>
                <button className="btn-ghost small" onClick={() => setEditSh(s)}>bewerk</button>
              </div>
              <div className="row" style={{ gap:6, marginTop:5, flexWrap:'wrap' }}>
                <NiveauBadge label="Invloed" value={s.invloed} />
                <span className="badge b-grey">Betrokken: {s.betrokkenheid}</span>
                <HoudingBadge value={s.houding} />
              </div>
            </div>
          ))}
          {!sel.stakeholders.length && <span className="muted small">Nog geen stakeholders.</span>}
        </div>
      </div>

      {/* Canvas-blokken */}
      <div className="grid" style={{ gridTemplateColumns:'repeat(auto-fit,minmax(260px,1fr))', marginTop:14 }}>
        <Block t="Kernopgave"            v={sel.kernopgave} />
        <Block t="Beslissingsdrivers"    v={sel.beslissingsdrivers} />
        <Block t="Mogelijke belemmeringen" v={sel.belemmeringen} />
        <Block t="Kansen voor Rhadix"    v={sel.kansen} />
        <Block t="Waarde"                v={sel.waarde} />
        <Block t="Volgende stappen"      v={sel.volgende_stappen} />
      </div>
      <div className="card card-pad" style={{ marginTop:14 }}>
        <div className="section-title" style={{ marginTop:0 }}>Besluitvormingsstructuur</div>
        <div className="grid" style={{ gridTemplateColumns:'1fr 1fr' }}>
          <KV label="Bestuurlijk orgaan" v={sel.bestuurlijk_orgaan} />
          <KV label="Operationeel orgaan" v={sel.operationeel_orgaan} />
          <KV label="Besluitvormingsproces" v={sel.besluitvormingsproces} />
          <KV label="Beslissingsfrequentie" v={sel.beslissingsfrequentie} />
        </div>
        {sel.notities && <><div className="section-title">Notities</div><p className="small">{sel.notities}</p></>}
      </div>

      {editSh && <ShForm data={editSh} onClose={() => setEditSh(null)} onSave={saveSh}
        onDelete={editSh.id ? () => { removeSh(editSh.id); setEditSh(null) } : null} />}
      {editKv && <KvForm data={editKv} orgs={orgs} onClose={() => setEditKv(null)} onSave={saveKv} />}
      <Toast msg={toast} />
    </div>
  )
}

function Block({ t, v }) {
  return <div className="card card-pad"><div className="section-title" style={{ marginTop:0 }}>{t}</div><Bullets text={v} /></div>
}
function KV({ label, v }) {
  return <div style={{ margin:'4px 0' }}><span className="muted small">{label}: </span><span>{v || '—'}</span></div>
}

function KvForm({ data, orgs, onClose, onSave }) {
  const [f, setF] = useState(data)
  const set = (k, v) => setF(p => ({ ...p, [k]: v }))
  const T = (k, label) => <Field label={label}><textarea className="input" value={f[k] || ''} onChange={e => set(k, e.target.value)} placeholder="Eén punt per regel" /></Field>
  return (
    <Modal wide title={data.id ? 'Krachtenveld bewerken' : 'Nieuw krachtenveld'} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Annuleren</button>
        <button className="btn btn-primary" disabled={!f.titel} onClick={() => onSave({ ...f, organisatie_id: f.organisatie_id || null })}>Opslaan</button></>}>
      <div className="grid" style={{ gridTemplateColumns:'1fr 1fr' }}>
        <Field label="Titel"><input className="input" value={f.titel} onChange={e => set('titel', e.target.value)} /></Field>
        <Field label="Regio"><input className="input" value={f.regio || ''} onChange={e => set('regio', e.target.value)} /></Field>
        <Field label="Gekoppelde RSO"><select className="select" value={f.organisatie_id || ''} onChange={e => set('organisatie_id', e.target.value)}>
          <option value="">—</option>{orgs.map(o => <option key={o.id} value={o.id}>{o.naam}</option>)}</select></Field>
        <Field label="Eigenaar"><input className="input" value={f.eigenaar || ''} onChange={e => set('eigenaar', e.target.value)} /></Field>
        <Field label="Bestuurlijk orgaan"><input className="input" value={f.bestuurlijk_orgaan || ''} onChange={e => set('bestuurlijk_orgaan', e.target.value)} /></Field>
        <Field label="Operationeel orgaan"><input className="input" value={f.operationeel_orgaan || ''} onChange={e => set('operationeel_orgaan', e.target.value)} /></Field>
        <Field label="Besluitvormingsproces"><input className="input" value={f.besluitvormingsproces || ''} onChange={e => set('besluitvormingsproces', e.target.value)} /></Field>
        <Field label="Beslissingsfrequentie"><input className="input" value={f.beslissingsfrequentie || ''} onChange={e => set('beslissingsfrequentie', e.target.value)} /></Field>
      </div>
      {T('kernopgave', 'Kernopgave')}{T('beslissingsdrivers', 'Beslissingsdrivers')}{T('belemmeringen', 'Belemmeringen')}
      {T('kansen', 'Kansen voor Rhadix')}{T('waarde', 'Waarde')}{T('volgende_stappen', 'Volgende stappen')}
      <Field label="Notities"><textarea className="input" value={f.notities || ''} onChange={e => set('notities', e.target.value)} /></Field>
    </Modal>
  )
}

function ShForm({ data, onClose, onSave, onDelete }) {
  const [f, setF] = useState(data)
  const set = (k, v) => setF(p => ({ ...p, [k]: v }))
  const niveau = ['Hoog', 'Middel', 'Laag']
  return (
    <Modal title={data.id ? 'Stakeholder bewerken' : 'Nieuwe stakeholder'} onClose={onClose}
      footer={<>{onDelete && <button className="btn btn-danger" onClick={onDelete}>Verwijderen</button>}
        <button className="btn" onClick={onClose}>Annuleren</button>
        <button className="btn btn-primary" disabled={!f.naam} onClick={() => onSave(f)}>Opslaan</button></>}>
      <Field label="Naam"><input className="input" value={f.naam} onChange={e => set('naam', e.target.value)} /></Field>
      <Field label="Rol / functie"><input className="input" value={f.rol || ''} onChange={e => set('rol', e.target.value)} /></Field>
      <div className="grid" style={{ gridTemplateColumns:'1fr 1fr 1fr' }}>
        <Field label="Invloed"><select className="select" value={f.invloed} onChange={e => set('invloed', e.target.value)}>{niveau.map(n => <option key={n}>{n}</option>)}</select></Field>
        <Field label="Betrokkenheid"><select className="select" value={f.betrokkenheid} onChange={e => set('betrokkenheid', e.target.value)}>{niveau.map(n => <option key={n}>{n}</option>)}</select></Field>
        <Field label="Houding"><select className="select" value={f.houding} onChange={e => set('houding', e.target.value)}>
          {['Positief', 'Neutraal', 'Onbekend', 'Negatief'].map(n => <option key={n}>{n}</option>)}</select></Field>
      </div>
      <Field label="Doelen / belangen"><textarea className="input" value={f.doelen_belangen || ''} onChange={e => set('doelen_belangen', e.target.value)} /></Field>
      <Field label="Belangrijkste argumenten"><textarea className="input" value={f.argumenten || ''} onChange={e => set('argumenten', e.target.value)} /></Field>
      <Field label="Belemmeringen / zorgen"><textarea className="input" value={f.belemmeringen || ''} onChange={e => set('belemmeringen', e.target.value)} /></Field>
      <Field label="Aanpak / strategie"><textarea className="input" value={f.aanpak || ''} onChange={e => set('aanpak', e.target.value)} /></Field>
      <div className="grid" style={{ gridTemplateColumns:'1fr 1fr' }}>
        <Field label="Laatste contact"><input className="input" value={f.laatste_contact || ''} onChange={e => set('laatste_contact', e.target.value)} /></Field>
        <Field label="Volgende stap"><input className="input" value={f.volgende_stap || ''} onChange={e => set('volgende_stap', e.target.value)} /></Field>
      </div>
    </Modal>
  )
}

function GenModal({ orgs, busy, onClose, onGen }) {
  const [orgId, setOrgId] = useState('')
  return (
    <Modal title="Genereer krachtenveld" onClose={onClose}
      footer={<>
        <button className="btn" onClick={onClose}>Annuleren</button>
        <button className="btn btn-primary" disabled={!orgId || busy} onClick={() => onGen(orgId)}>
          {busy ? 'Bezig…' : '✨ Genereren'}
        </button>
      </>}>
      <p className="small muted" style={{ marginBottom:12 }}>
        Kies een RSO. We bouwen een krachtenveld op met de standaard RSO-rollen op de matrix
        en zetten de gekoppelde contactpersonen automatisch om naar stakeholders. Kernopgave,
        beslissingsdrivers en kansen worden voorgevuld — daarna zelf bij te schaven.
      </p>
      <Field label="RSO / organisatie">
        <select className="select" value={orgId} onChange={e => setOrgId(e.target.value)}>
          <option value="">— Kies een RSO —</option>
          {orgs.map(o => <option key={o.id} value={o.id}>{o.naam}{o.aantal_contacten ? ` · ${o.aantal_contacten} contacten` : ''}</option>)}
        </select>
      </Field>
    </Modal>
  )
}
