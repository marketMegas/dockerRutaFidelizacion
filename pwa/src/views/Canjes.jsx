import { useEffect, useState } from 'react'
import { api, fmtFecha } from '../api.js'
import RecompensaCard from '../components/RecompensaCard.jsx'

export default function Canjes({ cliente, refrescar }) {
  const [recompensas, setRecompensas] = useState([])
  const [tasa, setTasa] = useState(0)
  const [misCanjes, setMisCanjes] = useState([])
  const [cargando, setCargando] = useState(true)
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')

  function cargar() {
    setCargando(true)
    api('/recompensas')
      .then(setRecompensas)
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false))
    api('/canjes/mis').then(setMisCanjes).catch(() => {})
  }

  useEffect(() => {
    cargar()
    api('/config').then((c) => setTasa(c.puntos_por_litro)).catch(() => {})
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
      {cliente && !cliente.cedula && (
        <p className="error">Agrega tu cedula en Mis datos para poder reclamar recompensas.</p>
      )}
      {mensaje && <p className="ok">{mensaje}</p>}
      {error && <p className="error">{error}</p>}

      {cargando ? (
        <div className="premios">
          {[0, 1].map((i) => (
            <div key={i} className="premio-card esqueleto" aria-hidden="true">
              <span className="premio-media esq-media" />
              <div className="premio-cuerpo">
                <span className="esq-linea esq-titulo" />
                <span className="esq-linea" />
                <span className="esq-barra" />
              </div>
            </div>
          ))}
        </div>
      ) : recompensas.length === 0 ? (
        <p className="vacio">Aun no hay recompensas disponibles</p>
      ) : (
        <div className="premios">
          {recompensas.map((r) => (
            <RecompensaCard
              key={r.id}
              recompensa={r}
              puntos={puntos}
              tasa={tasa}
              onCanjear={canjear}
            />
          ))}
        </div>
      )}

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
