const PASOS = [
  {
    n: 1,
    t: 'Registra tu placa y cédula',
    d: 'Entra con la placa de tu vehículo (3 letras y 3 números, ej. ABC123). Si es tu primera vez, pediremos tu número de celular y te enviamos un código así tu cuenta queda creada.',
  },
  {
    n: 2,
    t: 'Carga g-max',
    d: 'Al cargar en la estación, la venta se asocia a tu cuenta con el teléfono o la placa que registraste.',
  },
  {
    n: 3,
    t: 'Suma puntos',
    d: 'Cada litro cargado abona puntos según la regla vigente de la estación. Revisa tu saldo en Inicio.',
  },
  {
    n: 4,
    t: 'Canjea recompensas',
    d: 'Cuando tengas puntos suficientes, canjea en Recompensas y presenta tu cédula para reclamarla.',
  },
]

export default function Funcionamiento() {
  return (
    <div>
      <h2>Funcionamiento</h2>

      <ol className="pasos">
        {PASOS.map((p) => (
          <li key={p.n}>
            <span className="paso-num" aria-hidden="true">
              {p.n}
            </span>
            <div className="lista-info">
              <strong>{p.t}</strong>
              <span className="muted">{p.d}</span>
            </div>
          </li>
        ))}
      </ol>

      <h2>Reglas</h2>
      <ul className="lista">
        <li>
          <div className="lista-info">
            <strong>Tu placa acumula, tu cédula te identifica</strong>
            <span className="muted">
              Cada vez que cargas con tu placa se acumulan puntos en tu cuenta (tu celular).
              La cédula se presenta al reclamar recompensas.
            </span>
          </div>
        </li>
        <li>
          <div className="lista-info">
            <strong>Varias placas, una cuenta</strong>
            <span className="muted">Puedes registrar varias placas con el mismo celular y sumar en una sola cuenta.</span>
          </div>
        </li>
        <li>
          <div className="lista-info">
            <strong>Los puntos no vencen</strong>
            <span className="muted">Acumúlalos y canjéalos cuando quieras.</span>
          </div>
        </li>
        <li>
          <div className="lista-info">
            <strong>Cambios de teléfono</strong>
            <span className="muted">Entra con tu placa y registra el nuevo celular.</span>
          </div>
        </li>
      </ul>
    </div>
  )
}
