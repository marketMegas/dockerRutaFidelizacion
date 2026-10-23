import { fmtPuntos } from '../api.js'
import NivelPanel from '../components/NivelPanel.jsx'

export default function Saldo({ cliente, refrescar }) {
  return (
    <div className="inicio">
      <div className="saldo">
        <span className="saldo-v">{fmtPuntos(cliente?.puntos)}</span>
        <span className="saldo-t">puntos disponibles</span>
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
