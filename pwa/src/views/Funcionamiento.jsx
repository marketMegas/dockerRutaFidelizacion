import { useEffect, useState } from 'react'
import { api } from '../api.js'

const PASOS = [
  {
    n: 1,
    t: 'Registra tu placa y cedula',
    d: 'Entra con la placa de tu vehiculo (3 letras y 3 numeros, ej. ABC123) y tu cedula. Si es tu primera vez, te enviamos un codigo al celular y tu cuenta queda creada.',
  },
  {
    n: 2,
    t: 'Carga glp',
    d: 'Al cargar en la estacion, la venta se asocia a tu cuenta con el telefono o la placa que registraste.',
  },
  {
    n: 3,
    t: 'Suma puntos',
    d: 'Cada litro cargado abona puntos segun la regla vigente de la estacion. Revisa tu saldo en Inicio.',
  },
  {
    n: 4,
    t: 'Canjea recompensas',
    d: 'Cuando tengas puntos suficientes, canjea en Recompensas y presenta tu cedula para reclamarla.',
  },
]

export default function Funcionamiento() {
  const [tasa, setTasa] = useState(0)

  useEffect(() => {
    api('/config')
      .then((c) => setTasa(c.puntos_por_litro))
      .catch(() => {})
  }, [])

  return (
    <div>
      <h2>Funcionamiento</h2>
      <p className="muted">
        {tasa > 0
          ? `Ganas ${tasa} punto${tasa === 1 ? '' : 's'} por cada litro de glp.`
          : 'Ganas puntos por cada litro de glp que cargas.'}
      </p>

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
            <strong>Tu celular acumula, tu cedula te identifica</strong>
            <span className="muted">
              La cuenta y los puntos son del celular; la cedula se presenta al reclamar recompensas.
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
            <span className="muted">Acumulalos y canjealos cuando quieras.</span>
          </div>
        </li>
        <li>
          <div className="lista-info">
            <strong>Cambios de telefono</strong>
            <span className="muted">Entra con tu placa y registra el nuevo celular.</span>
          </div>
        </li>
      </ul>
    </div>
  )
}
