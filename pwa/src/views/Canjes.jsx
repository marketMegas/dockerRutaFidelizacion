import { useEffect, useState } from 'react'
import { api, fmtFecha, fmtPuntos } from '../api.js'
import BotonCopiar from '../components/BotonCopiar.jsx'
import CodigoCaja from '../components/CodigoCaja.jsx'
import RecompensaCard from '../components/RecompensaCard.jsx'

export default function Canjes({ cliente, refrescar }) {
  const [premios, setPremios] = useState([])
  const [misCanjes, setMisCanjes] = useState([])
  const [cargando, setCargando] = useState(true)
  const [canjeando, setCanjeando] = useState('')
  const [entregado, setEntregado] = useState(null)
  const [error, setError] = useState('')

  function cargar() {
    setCargando(true)
    api('/catalogo')
      .then((data) => setPremios(data.premios || []))
      .catch((e) => setError(e.message))
      .finally(() => setCargando(false))
    api('/canjes/mis').then(setMisCanjes).catch(() => {})
  }

  useEffect(() => {
    cargar()
  }, [])

  async function canjear(premio) {
    setError('')
    setCanjeando(premio.clave)
    try {
      const res = await api('/canjes', { method: 'POST', body: { premio_clave: premio.clave } })
      setEntregado(res)
      await refrescar()
      cargar()
    } catch (e) {
      setError(e.message)
    } finally {
      setCanjeando('')
    }
  }

  const puntos = cliente?.puntos ?? 0

  return (
    <div>
      <h2>Recompensas</h2>
      <p className="muted">
        Tienes {fmtPuntos(puntos)} puntos. Elige un premio y recibe tu código al instante.
      </p>
      {error && <p className="error">{error}</p>}

      {entregado && <CodigoCaja codigo={entregado.codigo} premio={entregado.premio} nuevo />}

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
            <RecompensaCard
              key={p.clave}
              recompensa={p}
              puntos={puntos}
              canjeando={canjeando === p.clave}
              onCanjear={canjear}
            />
          ))}
        </div>
      )}

      <h2>Mis códigos</h2>
      <ul className="lista">
        {misCanjes.map((c) => (
          <li key={c.id}>
            <div className="lista-info">
              <strong>{c.premio}</strong>
              <span className="muted">
                {fmtFecha(c.created_at)} · {fmtPuntos(c.puntos_costo)} pts
              </span>
            </div>
            <div className="codigo-fila">
              <span className="codigo-mini">{c.codigo}</span>
              <BotonCopiar texto={c.codigo} />
            </div>
          </li>
        ))}
        {misCanjes.length === 0 && <li className="muted">Aún no has canjeado premios</li>}
      </ul>
    </div>
  )
}
