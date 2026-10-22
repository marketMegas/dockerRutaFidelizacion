const PASOS = [
  {
    n: 1,
    t: 'Registra tu placa',
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
    d: 'Cada litro cargado suma puntos y tu nivel del mes los multiplica. Mientras más litros acumules, más puntos recibes por litro. Revisa tu saldo en Inicio.',
  },
  {
    n: 4,
    t: 'Canjea y recibe tu código',
    d: 'Cuando tengas puntos suficientes, canjea en Recompensas y recibirás un código de 8 caracteres. Guárdalo o envíalo por WhatsApp: con ese código reclamas tu premio en la estación.',
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
            <strong>Tu placa acumula, tu celular te identifica</strong>
            <span className="muted">
              Cada vez que cargas con tu placa se acumulan puntos en tu cuenta (tu celular).
            </span>
          </div>
        </li>
        <li>
          <div className="lista-info">
            <strong>Tu nivel depende de los litros del mes</strong>
            <span className="muted">
              Se calcula con los litros del mes anterior y del mes en curso: cuenta el mayor.
              Al cruzar un umbral, tus siguientes litros suman con el multiplicador nuevo.
            </span>
          </div>
        </li>
        <li>
          <div className="lista-info">
            <strong>El nivel se mantiene mientras cargues</strong>
            <span className="muted">
              Para conservar tu nivel el mes siguiente necesitas volver a alcanzar sus litros
              este mes.
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
            <strong>Cada código se usa una vez</strong>
            <span className="muted">El código que recibes es único y queda asociado a tu cuenta.</span>
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
