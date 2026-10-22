import { api } from './api.js'

export const ALFABETO_CODIGOS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

export function cargarCatalogo() {
  return api('/admin/catalogo')
}

export function guardarCatalogo(datos) {
  return api('/admin/catalogo', {
    method: 'PUT',
    body: {
      version: datos.version,
      niveles: datos.niveles.map((n) => ({
        clave: n.clave,
        nombre: n.nombre,
        minimo: Number(n.minimo),
        multiplicador: Number(n.multiplicador),
        descripcion: n.descripcion || '',
      })),
      premios: datos.premios.map((p) => ({
        clave: p.clave,
        nombre: p.nombre,
        descripcion: p.descripcion || '',
        imagen: p.imagen || '',
        costo_puntos: Number(p.costo_puntos),
        activo: Boolean(p.activo),
        codigos: p.codigos || [],
      })),
    },
  })
}

export function generarCodigos(clave, cantidad) {
  return api(`/admin/catalogo/${encodeURIComponent(clave)}/codigos`, {
    method: 'POST',
    body: { cantidad: Number(cantidad) },
  })
}

export function claveDesdeNombre(nombre, usadas = new Set()) {
  const limpio = nombre
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  const base = limpio || 'premio'
  let clave = base
  let n = 2
  while (usadas.has(clave)) {
    clave = `${base}-${n}`
    n += 1
  }
  return clave
}

export function normalizarCodigo(valor) {
  const limpio = String(valor || '')
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, '')
  if (limpio.length !== 8) return null
  if ([...limpio].some((ch) => !ALFABETO_CODIGOS.includes(ch))) return null
  return `${limpio.slice(0, 4)}-${limpio.slice(4)}`
}

export function codigosDesdeTexto(texto) {
  return String(texto || '')
    .split(/[\s,;]+/)
    .filter(Boolean)
}

export function textoDesdeCodigos(codigos) {
  return (codigos || []).join('\n')
}
