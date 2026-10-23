import { useEffect, useRef, useState } from 'react'
import { compartir } from '../api.js'
import BotonCopiar from './BotonCopiar.jsx'

export default function CodigoCaja({ codigo, premio, nuevo = false }) {
  const [aviso, setAviso] = useState('')
  const timer = useRef(null)

  useEffect(() => () => clearTimeout(timer.current), [])

  async function enviar() {
    const estado = await compartir({
      titulo: `Código ${premio}`,
      texto: `Este es mi código para ${premio}: ${codigo}`,
    })
    if (estado === 'copiado') setAviso('Copiado. Pégalo donde lo necesites.')
    else if (estado === 'fallo') setAviso('No se pudo copiar. Escribe el código a mano.')
    else setAviso('')
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setAviso(''), 2600)
  }

  return (
    <section
      className={`codigo-caja${nuevo ? ' codigo-caja--nuevo' : ''}`}
      aria-label={`Código de ${premio}`}
    >
      {nuevo && <span className="codigo-etiqueta">Recién canjeado</span>}
      <p className="codigo-premio">{premio}</p>
      <strong className="codigo-valor">{codigo}</strong>
      <div className="codigo-acciones">
        <BotonCopiar texto={codigo} className="codigo-accion" />
        <button type="button" className="codigo-accion codigo-accion--fuerte" onClick={enviar}>
          Compartir
        </button>
      </div>
      <p className="codigo-hint">Muéstralo en los comercios aliados o envíalo por WhatsApp.</p>
      <p className="codigo-aviso" role="status">
        {aviso}
      </p>
    </section>
  )
}
