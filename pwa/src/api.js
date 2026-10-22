const BASE = import.meta.env.VITE_API_URL || '/fid-api'

let token = localStorage.getItem('fid_cliente_token') || ''

export function setToken(t) {
  token = t || ''
  if (t) localStorage.setItem('fid_cliente_token', t)
  else localStorage.removeItem('fid_cliente_token')
}

export function getToken() {
  return token
}

export async function api(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })

  const data = await res.json().catch(() => ({}))

  if (res.status === 401 && !path.includes('/auth/')) {
    setToken('')
    window.location.reload()
    throw new Error('Sesión expirada')
  }
  if (!res.ok) {
    const detalle = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join(', ') : data.detail
    throw new Error(detalle || `Error ${res.status}`)
  }
  return data
}

export function fmtFecha(iso) {
  if (!iso) return '-'
  const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`)
  return d.toLocaleString('es-CO', { dateStyle: 'short', timeStyle: 'short' })
}

export function fmtLitros(valor) {
  const n = Number(valor) || 0
  return n.toLocaleString('es-CO', { maximumFractionDigits: 1 })
}

export function fmtPuntos(valor) {
  return (Number(valor) || 0).toLocaleString('es-CO')
}

export async function copiarTexto(texto) {
  try {
    await navigator.clipboard.writeText(texto)
    return true
  } catch {
    // En http fuera de localhost no hay Clipboard API: se copia con un textarea.
    try {
      const area = document.createElement('textarea')
      area.value = texto
      area.setAttribute('readonly', '')
      area.style.position = 'fixed'
      area.style.opacity = '0'
      document.body.appendChild(area)
      area.select()
      const ok = document.execCommand('copy')
      document.body.removeChild(area)
      return ok
    } catch {
      return false
    }
  }
}

export async function compartir({ titulo, texto }) {
  if (navigator.share) {
    try {
      await navigator.share({ title: titulo, text: texto })
      return 'compartido'
    } catch (e) {
      if (e.name === 'AbortError') return 'cancelado'
    }
  }
  return (await copiarTexto(texto)) ? 'copiado' : 'fallo'
}
