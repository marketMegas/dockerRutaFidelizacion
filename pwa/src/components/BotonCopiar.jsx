import { useEffect, useRef, useState } from 'react'
import { copiarTexto } from '../api.js'

export default function BotonCopiar({ texto, etiqueta = 'Copiar', className = '' }) {
  const [estado, setEstado] = useState('')
  const timer = useRef(null)

  useEffect(() => () => clearTimeout(timer.current), [])

  async function copiar() {
    const ok = await copiarTexto(texto)
    setEstado(ok ? 'Copiado' : 'No se pudo')
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setEstado(''), 1800)
  }

  return (
    <button
      type="button"
      className={`boton-copiar${className ? ` ${className}` : ''}`}
      onClick={copiar}
      aria-label={`Copiar ${texto}`}
    >
      {estado || etiqueta}
    </button>
  )
}
