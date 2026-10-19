import { useEffect, useState } from 'react'
import { api, fmtFecha } from '../api.js'

export default function Clientes() {
  const [q, setQ] = useState('')
  const [data, setData] = useState({ total: 0, clientes: [] })
  const [detalle, setDetalle] = useState(null)
  const [nuevaPlaca, setNuevaPlaca] = useState('')
  const [error, setError] = useState('')

  function cargar() {
    api(`/admin/clientes?q=${encodeURIComponent(q)}`)
      .then(setData)
      .catch((e) => setError(e.message))
  }

  useEffect(() => {
    cargar()
  }, [])

  async function ver(id) {
    try {
      setDetalle(await api(`/admin/clientes/${id}`))
    } catch (e) {
      setError(e.message)
    }
  }

  async function agregarPlaca(e) {
    e.preventDefault()
    setError('')
    try {
      await api(`/admin/clientes/${detalle.cliente.id}/vehiculos`, { method: 'POST', body: { placa: nuevaPlaca } })
      setNuevaPlaca('')
      await ver(detalle.cliente.id)
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  async function quitarPlaca(vehiculoId) {
    if (!confirm('Quitar esta placa del cliente?')) return
    setError('')
    try {
      await api(`/admin/clientes/${detalle.cliente.id}/vehiculos/${vehiculoId}`, { method: 'DELETE' })
      await ver(detalle.cliente.id)
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  async function reversar(movId) {
    if (!confirm('Reversar este movimiento?')) return
    try {
      await api(`/admin/movimientos/${movId}/reverso`, { method: 'POST', body: { motivo: 'reverso desde panel' } })
      if (detalle) await ver(detalle.cliente.id)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div>
      <h2>Clientes</h2>
      <div className="fila">
        <input
          placeholder="Buscar por placa, cedula, telefono o nombre"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && cargar()}
        />
        <button onClick={cargar}>Buscar</button>
        <span className="muted">{data.total} clientes</span>
      </div>
      {error && <p className="error">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Placas</th>
            <th>Cedula</th>
            <th>Telefono</th>
            <th>Nombre</th>
            <th>Puntos</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.clientes.map((c) => (
            <tr key={c.id}>
              <td>{(c.placas || []).join(', ') || c.placa || '-'}</td>
              <td>{c.cedula || '-'}</td>
              <td>{c.telefono}</td>
              <td>{c.nombre || '-'}</td>
              <td>{c.puntos}</td>
              <td>
                <button onClick={() => ver(c.id)}>Detalle</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {detalle && (
        <div className="panel-detalle">
          <div className="fila">
            <h3>
              {detalle.cliente.nombre || detalle.cliente.telefono}
              {detalle.cliente.cedula ? ` - C.C. ${detalle.cliente.cedula}` : ''}
              {detalle.cliente.placa ? ` - ${detalle.cliente.placa}` : ''} - {detalle.cliente.puntos} pts
            </h3>
            <button onClick={() => setDetalle(null)}>Cerrar</button>
          </div>

          <h4>Placas</h4>
          <ul className="placas-cliente">
            {(detalle.cliente.placas || []).map((v) => (
              <li key={v.id}>
                <span>{v.placa}</span>
                <button onClick={() => quitarPlaca(v.id)}>Quitar</button>
              </li>
            ))}
            {(detalle.cliente.placas || []).length === 0 && <li className="muted">Sin placas</li>}
          </ul>
          <form className="fila" onSubmit={agregarPlaca}>
            <input
              placeholder="ABC123"
              value={nuevaPlaca}
              onChange={(e) => setNuevaPlaca(e.target.value.toUpperCase())}
            />
            <button type="submit">Agregar placa</button>
          </form>

          <h4>Movimientos</h4>
          <table>
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Tipo</th>
                <th>Cantidad</th>
                <th>Saldo</th>
                <th>Motivo</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {detalle.movimientos.map((m) => (
                <tr key={m.id}>
                  <td>{fmtFecha(m.created_at)}</td>
                  <td>{m.tipo}</td>
                  <td className={m.cantidad < 0 ? 'neg' : 'pos'}>{m.cantidad}</td>
                  <td>{m.saldo_resultante}</td>
                  <td>{m.motivo}</td>
                  <td>
                    {(m.tipo === 'acumulacion' || m.tipo === 'canje') && (
                      <button onClick={() => reversar(m.id)}>Reversar</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <h4>Ventas</h4>
          <table>
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Factura</th>
                <th>Litros</th>
                <th>Puntos</th>
                <th>Placa</th>
                <th>Origen</th>
              </tr>
            </thead>
            <tbody>
              {detalle.ventas.map((v) => (
                <tr key={v.id}>
                  <td>{fmtFecha(v.created_at)}</td>
                  <td>{v.id_externo}</td>
                  <td>{v.volumen_litros}</td>
                  <td>{v.puntos_otorgados}</td>
                  <td>{v.placa || '-'}</td>
                  <td>{v.origen}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
