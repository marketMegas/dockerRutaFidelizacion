import { useEffect, useState } from 'react'
import { api, fmtFecha } from '../api.js'

export default function Clientes() {
  const [q, setQ] = useState('')
  const [data, setData] = useState({ total: 0, clientes: [] })
  const [detalle, setDetalle] = useState(null)
  const [nuevaPlaca, setNuevaPlaca] = useState('')
  const [nuevaCedula, setNuevaCedula] = useState('')
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
      const info = await api(`/admin/clientes/${id}`)
      setDetalle(info)
      setNuevaCedula(info.cliente.cedula || '')
    } catch (e) {
      setError(e.message)
    }
  }

  async function guardarCedula(e) {
    e.preventDefault()
    setError('')
    try {
      await api(`/admin/clientes/${detalle.cliente.id}`, { method: 'PATCH', body: { cedula: nuevaCedula } })
      await ver(detalle.cliente.id)
      cargar()
    } catch (err) {
      setError(err.message)
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
          placeholder="Buscar por placa, cédula, teléfono o nombre"
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
            <th>Cédula</th>
            <th>Teléfono</th>
            <th>Nombre</th>
            <th>Puntos</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {data.clientes.map((c) => (
            <tr key={c.id}>
              <td data-label="Placas">{(c.placas || []).join(', ') || c.placa || '-'}</td>
              <td data-label="Cédula">{c.cedula || '-'}</td>
              <td data-label="Teléfono">{c.telefono}</td>
              <td data-label="Nombre">{c.nombre || '-'}</td>
              <td data-label="Puntos">{c.puntos}</td>
              <td className="celda-acciones">
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

          <h4>Cédula</h4>
          <form className="fila" onSubmit={guardarCedula}>
            <input
              inputMode="numeric"
              placeholder="1098765432"
              value={nuevaCedula}
              onChange={(e) => setNuevaCedula(e.target.value.replace(/[^0-9]/g, '').slice(0, 10))}
            />
            <button type="submit">{detalle.cliente.cedula ? 'Actualizar cédula' : 'Agregar cédula'}</button>
          </form>

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
                  <td data-label="Fecha">{fmtFecha(m.created_at)}</td>
                  <td data-label="Tipo">{m.tipo}</td>
                  <td data-label="Cantidad" className={m.cantidad < 0 ? 'neg' : 'pos'}>{m.cantidad}</td>
                  <td data-label="Saldo">{m.saldo_resultante}</td>
                  <td data-label="Motivo">{m.motivo}</td>
                  <td className="celda-acciones">
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
                  <td data-label="Fecha">{fmtFecha(v.created_at)}</td>
                  <td data-label="Factura">{v.id_externo}</td>
                  <td data-label="Litros">{v.volumen_litros}</td>
                  <td data-label="Puntos">{v.puntos_otorgados}</td>
                  <td data-label="Placa">{v.placa || '-'}</td>
                  <td data-label="Origen">{v.origen}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
