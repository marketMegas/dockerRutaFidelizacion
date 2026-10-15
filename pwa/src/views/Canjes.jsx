import { useEffect, useState } from 'react'
import { api, fmtFecha } from '../api.js'

export default function Canjes({ cliente, refrescar }) {
  const [recompensas, setRecompensas] = useState([])
  const [misCanjes, setMisCanjes] = useState([])
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')

  function cargar() {
    api('/recompensas').then(setRecompensas).catch((e) => setError(e.message))
    api('/canjes/mis').then(setMisCanjes).catch(() => {})
  }

  useEffect(() => {
    cargar()
  }, [])

  async function canjear(r) {
    setError('')
    setMensaje('')
    try {
      const res = await api('/canjes', { method: 'POST', body: { recompensa_id: r.id } })
      setMensaje(`Canjeaste ${res.recompensa}. Presenta tu cedula para reclamarla.`)
      await refrescar()
      cargar()
    } catch (e) {
      setError(e.message)
    }
  }

  const puntos = cliente?.puntos ?? 0

  return (
    <div>
      <h2>Recompensas</h2>
      <p className="muted">Tienes {puntos} puntos</p>
      {mensaje && <p className="ok">{mensaje}</p>}
      {error && <p className="error">{error}</p>}

      <ul className="lista">
        {recompensas.map((r) => {
          const alcanza = puntos >= r.costo_puntos && r.stock > 0
          return (
            <li key={r.id}>
              <div className="lista-info">
                <strong>{r.nombre}</strong>
                <span className="muted">{r.descripcion || ''}</span>
                <span className="muted">{r.stock} disponibles</span>
              </div>
              <div className="premio">
                <span className="costo">{r.costo_puntos} pts</span>
                <button disabled={!alcanza} onClick={() => canjear(r)}>
                  {r.stock > 0 ? 'Canjear' : 'Agotado'}
                </button>
              </div>
            </li>
          )
        })}
      </ul>

      <h2>Mis canjes</h2>
      <ul className="lista">
        {misCanjes.map((c) => (
          <li key={c.id}>
            <div className="lista-info">
              <strong>{c.recompensa}</strong>
              <span className="muted">{fmtFecha(c.created_at)}</span>
            </div>
            <span className={`badge ${c.estado}`}>{c.estado}</span>
          </li>
        ))}
        {misCanjes.length === 0 && <li className="muted">Aun no has canjeado recompensas</li>}
      </ul>
    </div>
  )
}
