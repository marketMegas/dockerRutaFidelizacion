import { useEffect, useState } from 'react'
import { api } from '../api.js'
import RecompensaCard from '../components/RecompensaCard.jsx'

export default function Recompensas({ onSesion }) {
  const [recompensas, setRecompensas] = useState([])
  const [tasa, setTasa] = useState(0)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/recompensas')
      .then(setRecompensas)
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false))
    api('/config')
      .then((c) => setTasa(c.puntos_por_litro))
      .catch(() => {})
  }, [])

  return (
    <div>
      <h2>Recompensas</h2>
      <p className="muted">Inicia sesion para canjear premios con tus puntos.</p>
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
            <RecompensaCard key={r.id} recompensa={r} tasa={tasa} mostrarProgreso={false} />
          ))}
        </div>
      )}

      <button type="button" className="primario" onClick={onSesion}>
        Iniciar sesion para canjear
      </button>
    </div>
  )
}
