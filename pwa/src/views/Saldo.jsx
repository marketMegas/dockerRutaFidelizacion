export default function Saldo({ cliente, refrescar }) {
  return (
    <div className="inicio">
      <div className="saldo">
        <span className="saldo-v">{cliente?.puntos ?? 0}</span>
        <span className="saldo-t">puntos disponibles</span>
      </div>

      <p className="muted">
        Acumula puntos por cada litro que cargas y canjealos por recompensas. Identificate con
        tu placa para sumar.
      </p>

      <button className="primario" onClick={refrescar}>
        Actualizar saldo
      </button>
    </div>
  )
}
