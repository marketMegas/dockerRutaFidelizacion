import { useEffect, useState } from 'react'
import { api } from '../api.js'
import RecompensaCard from '../components/RecompensaCard.jsx'

export default function Recompensas({ onSesion }) {
  const [premios, setPremios] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/catalogo')
      .then((data) => setPremios(data.premios || []))
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false))
  }, [])

  return (
    <div>
      <h2>Recompensas</h2>
      <p className="muted">Inicia sesión para canjear premios con tus puntos.</p>
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
      ) : premios.length === 0 ? (
        <p className="vacio">Aún no hay premios disponibles</p>
      ) : (
        <div className="premios">
          {premios.map((p) => (
            <RecompensaCard key={p.clave} recompensa={p} mostrarProgreso={false} />
          ))}
        </div>
      )}

      <button type="button" className="primario" onClick={onSesion}>
        Iniciar sesión para canjear
      </button>
    </div>
  )
}
