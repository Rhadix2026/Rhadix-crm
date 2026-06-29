const BASE = '/api'

let _token = sessionStorage.getItem('rhadix_crm_token') || null
export function setAuthToken(t) { _token = t; if (t) sessionStorage.setItem('rhadix_crm_token', t) }
export function getAuthToken()  { return _token }
export function clearAuthToken(){ _token = null; sessionStorage.removeItem('rhadix_crm_token') }

function authHeaders(extra = {}) {
  return _token ? { Authorization: `Bearer ${_token}`, ...extra } : { ...extra }
}

async function req(method, path, body) {
  const opts = { method, headers: authHeaders(body !== undefined ? { 'Content-Type': 'application/json' } : {}) }
  if (body !== undefined) opts.body = JSON.stringify(body)
  const res = await fetch(`${BASE}${path}`, opts)
  if (res.status === 401) { clearAuthToken(); window.dispatchEvent(new CustomEvent('rhadix:unauthorized')) }
  if (!res.ok) {
    let detail = `Fout ${res.status}`
    try { const j = await res.json(); detail = j.detail || detail } catch {}
    throw new Error(detail)
  }
  return res.status === 204 ? null : res.json()
}

// Meta / auth
export const getMeta = () => req('GET', '/meta')
export async function login(email, password) {
  const d = await req('POST', '/auth/login', { email, password }); setAuthToken(d.access_token); return d
}
export const getMe = () => req('GET', '/auth/me')

// Organisaties
export const listOrgs  = (params = '') => req('GET', `/crm/organisaties${params}`)
export const getOrg    = (id) => req('GET', `/crm/organisaties/${id}`)
export const createOrg = (b) => req('POST', '/crm/organisaties', b)
export const updateOrg = (id, b) => req('PATCH', `/crm/organisaties/${id}`, b)
export const deleteOrg = (id) => req('DELETE', `/crm/organisaties/${id}`)

// Contactpersonen
export const listCps  = (params = '') => req('GET', `/crm/contactpersonen${params}`)
export const createCp = (b) => req('POST', '/crm/contactpersonen', b)
export const updateCp = (id, b) => req('PATCH', `/crm/contactpersonen/${id}`, b)
export const deleteCp = (id) => req('DELETE', `/crm/contactpersonen/${id}`)

// Krachtenveld + stakeholders
export const listKv   = () => req('GET', '/crm/krachtenvelden')
export const getKv    = (id) => req('GET', `/crm/krachtenvelden/${id}`)
export const createKv = (b) => req('POST', '/crm/krachtenvelden', b)
export const updateKv = (id, b) => req('PATCH', `/crm/krachtenvelden/${id}`, b)
export const deleteKv = (id) => req('DELETE', `/crm/krachtenvelden/${id}`)
export const genereerKrachtenveld = (orgId) => req('POST', `/crm/organisaties/${orgId}/genereer-krachtenveld`)
export const addSh    = (kvId, b) => req('POST', `/crm/krachtenvelden/${kvId}/stakeholders`, b)
export const updateSh = (id, b) => req('PATCH', `/crm/stakeholders/${id}`, b)
export const deleteSh = (id) => req('DELETE', `/crm/stakeholders/${id}`)

// Activiteiten
export const listAct   = (params = '') => req('GET', `/crm/activiteiten${params}`)
export const createAct = (b) => req('POST', '/crm/activiteiten', b)
export const updateAct = (id, b) => req('PATCH', `/crm/activiteiten/${id}`, b)
export const deleteAct = (id) => req('DELETE', `/crm/activiteiten/${id}`)

// Dashboard
export const getDashboard = () => req('GET', '/crm/dashboard')
export const getTeamleden = () => req('GET', '/crm/teamleden')

// Beheer (ORG_ADMIN / PLATFORM_ADMIN)
export const listOrgUsers  = () => req('GET', '/org/users')
export const createOrgUser = (b) => req('POST', '/org/users', b)
export const toggleUser    = (id) => req('PATCH', `/org/users/${id}/deactivate`)
export const resetUserPwd  = (id, new_password) => req('POST', `/org/users/${id}/reset-password`, { new_password })
export const platformStats = () => req('GET', '/admin/stats')

// ── Taken / workflow ─────────────────────────────────────────────────────────
export const listTasks        = (params = '') => req('GET', `/tasks${params}`)
export const taskSummary      = () => req('GET', '/tasks/summary')
export const assignableUsers  = () => req('GET', '/tasks/assignable-users')
export const createTask       = (b) => req('POST', '/tasks', b)
export const createTasksBulk  = (b) => req('POST', '/tasks/bulk', b)
export const updateTask       = (id, b) => req('PATCH', `/tasks/${id}`, b)
export const deleteTask       = (id) => req('DELETE', `/tasks/${id}`)
