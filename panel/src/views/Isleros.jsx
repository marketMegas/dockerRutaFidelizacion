import { useEffect, useState } from 'react'
import { api, fmtFecha } from '../api.js'

export default function Isleros() {
  const [isleros, setIsleros] = useState([])
  const [usuario, setUsuario] = useState('')
  const [nombre, setNombre] = useState('')
  const [password, setPassword] = useState('')
  const [detalle, setDetalle] = useState(null)
  const [error, setError] = useState('')
  const [aviso, setAviso] = useState('')

  function cargar() {
    api('/admin/isleros')
      .then(setIsleros)
      .catch((e) => setError(e.message))
  }

  useEffect(() => {
    cargar()
  }, [])

  async function crear(e) {
    e.preventDefault()
    setError('')
    setAviso('')
    if (usuario.trim().length < 3) {
      setError('El usuario debe tener al menos 3 caracteres')
      return
    }
    if (nombre.trim().length < 2) {
      setError('El nombre debe tener al menos 2 caracteres')
      return
    }
    if (password.length < 10) {
      setError('La contraseña debe tener al menos 10 caracteres')
      return
    }
    try {
      await api('/admin/isleros', { method: 'POST', body: { usuario, nombre, password } })
      setUsuario('')
      setNombre('')
      setPassword('')
      setAviso('Islero creado')
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  async function alternar(islero) {
    setError('')
    setAviso('')
    try {
      await api(`/admin/isleros/${islero.id}`, { method: 'PATCH', body: { activo: !islero.activo } })
      setAviso(islero.activo ? 'Islero desactivado' : 'Islero activado')
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  async function resetear(islero) {
    setError('')
    setAviso('')
    const nueva = window.prompt(`Nueva contraseña para ${islero.usuario} (mínimo 10 caracteres)`)
    if (nueva === null) return
    if (nueva.length < 10) {
      setError('La contraseña debe tener al menos 10 caracteres')
      return
    }
    try {
      await api(`/admin/isleros/${islero.id}`, { method: 'PATCH', body: { password: nueva } })
      setAviso('Contraseña actualizada')
    } catch (err) {
      setError(err.message)
    }
  }

  async function verRegistros(islero) {
    setError('')
    try {
      const registros = await api(`/admin/isleros/${islero.id}/registros?limite=50`)
      setDetalle({ islero, registros })
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <h2>Isleros</h2>
      <p className="muted">
        Cuentas del personal de isla. Solo pueden registrar clientes por placa, cédula y celular; cada cambio queda
        auditado.
      </p>

      {error && <p className="error">{error}</p>}
      {aviso && <p className="ok">{aviso}</p>}

      <form className="fila" onSubmit={crear}>
        <input
          placeholder="Usuario"
          autoComplete="off"
          value={usuario}
          onChange={(e) => setUsuario(e.target.value)}
          required
        />
        <input
          placeholder="Nombre completo"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="Contraseña (mín. 10)"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit">Crear islero</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Nombre</th>
            <th>Estado</th>
            <th>Último acceso</th>
            <th>Registros</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {isleros.map((i) => (
            <tr key={i.id}>
              <td data-label="Usuario">{i.usuario}</td>
              <td data-label="Nombre">{i.nombre || '-'}</td>
              <td data-label="Estado">{i.activo ? 'Activo' : 'Inactivo'}</td>
              <td data-label="Último acceso">{i.ultimo_acceso ? fmtFecha(i.ultimo_acceso) : 'Nunca'}</td>
              <td data-label="Registros">{i.registros}</td>
              <td className="celda-acciones">
                <button onClick={() => alternar(i)}>{i.activo ? 'Desactivar' : 'Activar'}</button>
                <button onClick={() => resetear(i)}>Clave</button>
                <button onClick={() => verRegistros(i)}>Registros</button>
              </td>
            </tr>
          ))}
          {isleros.length === 0 && (
            <tr>
              <td colSpan="6" className="muted">
                Aún no hay isleros creados.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {detalle && (
        <div className="panel-detalle">
          <div className="fila">
            <h3>Registros de {detalle.islero.nombre || detalle.islero.usuario}</h3>
            <button onClick={() => setDetalle(null)}>Cerrar</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Placa</th>
                <th>Acción</th>
                <th>Cédula</th>
                <th>Celular</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {detalle.registros.map((r) => (
                <tr key={r.id}>
                  <td data-label="Fecha">{fmtFecha(r.created_at)}</td>
                  <td data-label="Placa">{r.placa}</td>
                  <td data-label="Acción">{r.accion === 'crear' ? 'Registro' : 'Actualización'}</td>
                  <td data-label="Cédula">{r.detalle?.despues?.cedula || '-'}</td>
                  <td data-label="Celular">{r.detalle?.despues?.telefono || '-'}</td>
                  <td data-label="IP">{r.ip || '-'}</td>
                </tr>
              ))}
              {detalle.registros.length === 0 && (
                <tr>
                  <td colSpan="6" className="muted">
                    Sin registros.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
