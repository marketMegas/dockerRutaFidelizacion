import { useState } from 'react'
import { api, fmtFecha } from '../api.js'

export default function Datos({ cliente, refrescar }) {
  const [cedula, setCedula] = useState('')
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)

  if (!cliente) return <p className="muted">Cargando...</p>

  const placas = cliente.placas?.length ? cliente.placas : cliente.placa ? [cliente.placa] : []

  const filas = [
    { k: 'Cedula', v: cliente.cedula || '-' },
    { k: 'Celular', v: cliente.telefono },
    { k: 'Nombre', v: cliente.nombre || '-' },
  ]
  if (cliente.email) filas.push({ k: 'Email', v: cliente.email })
  filas.push({ k: 'Miembro desde', v: fmtFecha(cliente.created_at) })

  async function guardarCedula(e) {
    e.preventDefault()
    setError('')
    setGuardando(true)
    try {
      await api('/clientes/me', { method: 'PATCH', body: { cedula } })
      setCedula('')
      await refrescar()
    } catch (err) {
      setError(err.message)
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="datos">
      <h2>Mis datos</h2>

      <div className="saldo">
        <span className="saldo-v">{cliente.puntos}</span>
        <span className="saldo-t">puntos disponibles</span>
      </div>

      {!cliente.cedula && (
        <form className="cedula-pendiente" onSubmit={guardarCedula}>
          <p className="muted">
            Necesitamos tu cedula para reclamar recompensas. Agregala para poder canjear.
          </p>
          <div className="fila">
            <input
              inputMode="numeric"
              placeholder="1098765432"
              value={cedula}
              onChange={(e) => setCedula(e.target.value.replace(/[^0-9]/g, '').slice(0, 10))}
              required
            />
            <button disabled={guardando}>{guardando ? 'Guardando...' : 'Guardar cedula'}</button>
          </div>
          {error && <p className="error">{error}</p>}
        </form>
      )}

      <h3>Mis placas</h3>
      <ul className="lista">
        {placas.map((p) => (
          <li key={p}>
            <div className="lista-info">
              <strong>{p}</strong>
            </div>
          </li>
        ))}
        {placas.length === 0 && <li className="muted">Aun no tienes placas registradas</li>}
      </ul>

      <ul className="lista">
        {filas.map((f) => (
          <li key={f.k}>
            <div className="lista-info">
              <strong>{f.k}</strong>
            </div>
            <span className="valor">{f.v}</span>
          </li>
        ))}
      </ul>

      <button className="primario" onClick={refrescar}>
        Actualizar mis datos
      </button>
    </div>
  )
}
