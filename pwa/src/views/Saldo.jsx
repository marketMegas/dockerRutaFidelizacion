export default function Saldo({ cliente, refrescar }) {
  return (
    <div className="inicio">
      <div className="saldo">
        <span className="saldo-v">{cliente?.puntos ?? 0}</span>
        <span className="saldo-t">puntos disponibles</span>
      </div>

      <p className="muted">
        Acumula puntos por cada litro que cargas y canjéalos por recompensas. Identifícate con tu
        placa para sumar y presenta tu cédula al reclamar.
      </p>

      <button className="primario" onClick={refrescar}>
        Actualizar saldo
      </button>
    </div>
  )
}
