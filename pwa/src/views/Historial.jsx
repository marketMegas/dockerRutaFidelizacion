import { useEffect, useState } from 'react'
import { api, fmtFecha } from '../api.js'

const ETIQUETA = {
  acumulacion: 'Puntos ganados',
  canje: 'Canje',
  reverso: 'Ajuste',
  ajuste: 'Ajuste',
}

export default function Historial() {
  const [movs, setMovs] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    api('/clientes/me/movimientos')
      .then(setMovs)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <h2>Historial</h2>
      {error && <p className="error">{error}</p>}
      <ul className="lista">
        {movs.map((m) => (
          <li key={m.id}>
            <div className="lista-info">
              <strong>{ETIQUETA[m.tipo] || m.tipo}</strong>
              <span className="muted">{m.motivo || m.referencia || ''}</span>
              <span className="muted fecha">{fmtFecha(m.created_at)}</span>
            </div>
            <span className={`delta ${m.cantidad < 0 ? 'neg' : 'pos'}`}>
              {m.cantidad > 0 ? '+' : ''}
              {m.cantidad}
            </span>
          </li>
        ))}
        {movs.length === 0 && <li className="muted">Todavía no tienes movimientos</li>}
      </ul>
    </div>
  )
}
