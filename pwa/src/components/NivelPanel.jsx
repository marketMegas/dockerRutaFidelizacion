import { fmtLitros } from '../api.js'

function fmtMult(valor) {
  return (Number(valor) || 1).toLocaleString('es-CO', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export default function NivelPanel({ cliente }) {
  const niveles = cliente?.niveles ?? []
  const actual = cliente?.nivel
  const siguiente = cliente?.siguiente_nivel
  if (!actual || niveles.length === 0) return null

  const consumo = Number(cliente?.consumo_mes) || 0
  const faltanSubir = Number(cliente?.faltan_para_subir) || 0
  const faltanMantener = Number(cliente?.faltan_para_mantener) || 0
  const multiplicador = Number(cliente?.multiplicador) || 1
  const meta = Number(siguiente?.minimo) || 0
  const pct = siguiente && meta > 0 ? Math.min(100, Math.round((consumo / meta) * 100)) : 100

  return (
    <section className="nivel-panel" aria-label="Tu nivel del mes">
      <header className="nivel-cabecera">
        <span className="nivel-chip">Nivel {actual.nombre}</span>
        <span className="nivel-mult">
          <strong>×{fmtMult(multiplicador)}</strong> puntos por litro
        </span>
      </header>

      <ul className="escalera">
        {niveles.map((n) => {
          const estado =
            Number(n.minimo) === Number(actual.minimo)
              ? 'actual'
              : Number(n.minimo) < Number(actual.minimo)
                ? 'pasado'
                : 'futuro'
          return (
            <li key={n.clave} className={`peldano ${estado}`}>
              <span className="peldano-nombre">{n.nombre}</span>
              <span className="peldano-litros">{fmtLitros(n.minimo)} L</span>
              <span className="peldano-mult">×{fmtMult(n.multiplicador)}</span>
            </li>
          )
        })}
      </ul>

      <div className="nivel-avance">
        {siguiente ? (
          <div
            className="medidor"
            role="progressbar"
            aria-valuemin="0"
            aria-valuemax={meta}
            aria-valuenow={Math.min(consumo, meta)}
            aria-label={`${fmtLitros(consumo)} de ${fmtLitros(meta)} litros para ${siguiente.nombre}`}
          >
            <span className="nivel" style={{ width: `${pct}%` }} />
          </div>
        ) : (
          <div className="medidor" aria-hidden="true">
            <span className="nivel" style={{ width: '100%' }} />
          </div>
        )}

        <div className="nivel-pie">
          <span>
            <strong>{fmtLitros(consumo)} L</strong> este mes
          </span>
          {siguiente ? (
            <span>
              {faltanSubir > 0 ? (
                <>
                  <strong>{fmtLitros(faltanSubir)} L</strong> para {siguiente.nombre}
                </>
              ) : (
                <>Ya alcanzaste {siguiente.nombre}</>
              )}
            </span>
          ) : (
            <span>Nivel máximo</span>
          )}
        </div>
      </div>

      {faltanMantener > 0 && (
        <p className="nivel-nota">
          Para mantener {actual.nombre} el próximo mes te faltan{' '}
          <strong>{fmtLitros(faltanMantener)} L</strong> este mes.
        </p>
      )}
    </section>
  )
}
