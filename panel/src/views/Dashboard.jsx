import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function Dashboard() {
  const [resumen, setResumen] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/admin/resumen').then(setResumen).catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!resumen) return <p className="muted">Cargando...</p>

  const tarjetas = [
    { t: 'Clientes', v: resumen.total_clientes, s: `${resumen.clientes_nuevos_mes} nuevos este mes` },
    { t: 'Puntos activos', v: resumen.puntos_activos, s: 'saldo en circulación' },
    { t: 'Puntos del mes', v: resumen.puntos_acumulados_mes, s: `${resumen.puntos_canjeados_mes} canjeados` },
    {
      t: 'Códigos entregados',
      v: resumen.codigos_entregados,
      s: `${resumen.codigos_disponibles} disponibles`,
    },
    { t: 'Ventas hoy', v: resumen.ventas_hoy.cantidad, s: `${resumen.ventas_hoy.litros.toFixed(1)} L` },
    { t: 'Ventas del mes', v: resumen.ventas_mes.cantidad, s: `${resumen.ventas_mes.litros.toFixed(1)} L` },
  ]

  return (
    <div>
      <h2>Resumen</h2>
      <div className="grid">
        {tarjetas.map((c) => (
          <div className="card" key={c.t}>
            <span className="card-t">{c.t}</span>
            <span className="card-v">{c.v}</span>
            <span className="card-s">{c.s}</span>
          </div>
        ))}
      </div>

      <h3>Clientes por nivel</h3>
      <div className="grid">
        {(resumen.niveles || []).map((n) => (
          <div className="card" key={n.clave}>
            <span className="card-t">{n.nombre}</span>
            <span className="card-v">{n.clientes}</span>
            <span className="card-s">clientes este mes</span>
          </div>
        ))}
      </div>
    </div>
  )
}
