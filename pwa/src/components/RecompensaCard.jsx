import { useState } from 'react'

export default function RecompensaCard({
  recompensa,
  puntos = 0,
  tasa = 0,
  onCanjear,
  mostrarProgreso = true,
  sobreVerde = false,
}) {
  const { nombre, descripcion, imagen, costo_puntos, stock } = recompensa
  const [urlFallida, setUrlFallida] = useState(null)

  const agotado = stock <= 0
  const alcanza = !agotado && puntos >= costo_puntos
  const avance = Math.min(puntos, costo_puntos)
  const pct = costo_puntos > 0 ? Math.round((avance / costo_puntos) * 100) : 0
  const faltan = Math.max(0, costo_puntos - puntos)
  const litros = tasa > 0 ? Math.round(costo_puntos / tasa) : null
  const mostrarImagen = Boolean(imagen) && urlFallida !== imagen

  const clases = ['premio-card']
  if (sobreVerde) clases.push('premio-card--verde')
  if (agotado) clases.push('premio-card--agotado')

  let estado = null
  if (agotado) estado = 'Agotado'
  else if (alcanza) estado = 'Listo para canjear'
  else estado = `Te faltan ${faltan} pts`

  return (
    <article className={clases.join(' ')}>
      <div className="premio-media">
        {mostrarImagen ? (
          <img
            src={imagen}
            alt={nombre}
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setUrlFallida(imagen)}
          />
        ) : (
          <span className="premio-media-vacia" aria-hidden="true" />
        )}
      </div>

      <div className="premio-cuerpo">
        <header className="premio-cabecera">
          <h3 className="premio-nombre">{nombre}</h3>
          <span className="premio-costo">
            <strong>{costo_puntos}</strong>
            <span className="premio-costo-u">pts</span>
          </span>
        </header>

        {descripcion && <p className="premio-desc">{descripcion}</p>}

        {mostrarProgreso ? (
          <>
            <div
              className="medidor"
              role="progressbar"
              aria-valuemin="0"
              aria-valuemax={costo_puntos}
              aria-valuenow={avance}
              aria-label={`${puntos} de ${costo_puntos} puntos`}
            >
              <span className="nivel" style={{ width: `${pct}%` }} />
            </div>
            <div className="premio-pie">
              <span className={alcanza ? 'premio-estado listo' : 'premio-estado'}>{estado}</span>
              {onCanjear && (
                <button
                  className="premio-canjear"
                  disabled={!alcanza}
                  onClick={() => onCanjear(recompensa)}
                >
                  {agotado ? 'Agotado' : 'Canjear'}
                </button>
              )}
            </div>
          </>
        ) : (
          <p className="premio-litros">
            {litros !== null ? (
              <>
                Equivale a <strong>{litros} L</strong> de GLP
              </>
            ) : (
              <>Por {costo_puntos} puntos</>
            )}
          </p>
        )}
      </div>
    </article>
  )
}
