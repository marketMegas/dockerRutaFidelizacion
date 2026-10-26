import { useState } from 'react'
import { fmtPuntos } from '../api.js'
import NivelPanel from '../components/NivelPanel.jsx'

const IMG_SALDO = 'https://images.pexels.com/photos/40539387/pexels-photo-40539387.jpeg'

export default function Saldo({ cliente, refrescar }) {
  const [imgFallida, setImgFallida] = useState(false)

  return (
    <div className="inicio">
      <div className="saldo-heroe">
        <div className="saldo">
          <span className="saldo-v">{fmtPuntos(cliente?.puntos)}</span>
          <span className="saldo-t">puntos disponibles</span>
        </div>
        {!imgFallida && (
          <div className="saldo-img-wrap">
            <img
              className="saldo-img"
              src={IMG_SALDO}
              alt=""
              loading="lazy"
              decoding="async"
              referrerPolicy="no-referrer"
              onError={() => setImgFallida(true)}
            />
          </div>
        )}
      </div>

      <NivelPanel cliente={cliente} />

      <p className="muted">
        Cada litro que cargas suma puntos y tu nivel del mes los multiplica. Canjea en
        Recompensas y recibe un código para reclamar tu premio en los comercios aliados.
      </p>

      <button className="primario" onClick={refrescar}>
        Actualizar saldo
      </button>
    </div>
  )
}
