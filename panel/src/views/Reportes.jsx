import { useEffect, useState } from 'react'
import { api, fmtFecha } from '../api.js'

export default function Reportes() {
  const [ventas, setVentas] = useState([])
  const [canjes, setCanjes] = useState([])
  const [cedula, setCedula] = useState('')
  const [error, setError] = useState('')

  function cargarCanjes(q = '') {
    const filtro = q ? `?q=${encodeURIComponent(q)}` : ''
    api(`/admin/canjes${filtro}`).then(setCanjes).catch((e) => setError(e.message))
  }

  function cargar() {
    api('/admin/ventas?dias=14').then(setVentas).catch((e) => setError(e.message))
    cargarCanjes(cedula)
  }

  useEffect(() => {
    cargar()
  }, [])

  function buscar(e) {
    e.preventDefault()
    setError('')
    cargarCanjes(cedula)
  }

  async function entregar(id) {
    try {
      await api(`/admin/canjes/${id}/entregado`, { method: 'POST' })
      cargar()
    } catch (e) {
      setError(e.message)
    }
  }

  const maxLitros = Math.max(1, ...ventas.map((v) => v.litros))

  return (
    <div>
      <h2>Reportes</h2>
      {error && <p className="error">{error}</p>}

      <h3>Ventas por dia (14 dias)</h3>
      <table>
        <thead>
          <tr>
            <th>Dia</th>
            <th>Ventas</th>
            <th>Litros</th>
            <th>Monto</th>
            <th>Puntos</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {ventas.map((v) => (
            <tr key={v.dia}>
              <td>{v.dia}</td>
              <td>{v.cantidad}</td>
              <td>{v.litros.toFixed(1)}</td>
              <td>{v.monto.toLocaleString('es-CO')}</td>
              <td>{v.puntos}</td>
              <td>
                <div className="barra">
                  <div className="barra-fill" style={{ width: `${(v.litros / maxLitros) * 100}%` }} />
                </div>
              </td>
            </tr>
          ))}
          {ventas.length === 0 && (
            <tr>
              <td colSpan="6" className="muted">
                Sin ventas registradas
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <h3>Canjes recientes</h3>
      <form className="fila" onSubmit={buscar}>
        <input
          inputMode="numeric"
          placeholder="Buscar por cedula del cliente"
          value={cedula}
          onChange={(e) => setCedula(e.target.value.replace(/[^0-9]/g, ''))}
        />
        <button type="submit">Buscar</button>
        {cedula && (
          <button
            type="button"
            onClick={() => {
              setCedula('')
              cargarCanjes('')
            }}
          >
            Limpiar
          </button>
        )}
      </form>
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Cliente</th>
            <th>Cedula</th>
            <th>Recompensa</th>
            <th>Puntos</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {canjes.map((c) => (
            <tr key={c.id}>
              <td>{fmtFecha(c.created_at)}</td>
              <td>{c.cliente || '-'}</td>
              <td>{c.cedula || '-'}</td>
              <td>{c.recompensa || '-'}</td>
              <td>{c.puntos_costo}</td>
              <td>{c.estado}</td>
              <td>
                {c.estado !== 'entregado' && <button onClick={() => entregar(c.id)}>Marcar entregado</button>}
              </td>
            </tr>
          ))}
          {canjes.length === 0 && (
            <tr>
              <td colSpan="7" className="muted">
                Sin canjes registrados
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
