import { useEffect, useRef, useState } from 'react'
import { api, fmtPuntos } from '../api.js'
import './ChatbotWidget.css'

const SUGERENCIAS = [
  '¿Cuántos puntos tengo?',
  '¿Qué premios puedo canjear?',
  '¿Cuánto me falta para subir de nivel?',
  '¿Qué he canjeado?',
  '¿Dónde veo mi código?',
]

function normalizar(texto) {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .trim()
}

function respuestaLocal(texto, cliente) {
  const t = normalizar(texto)
  const puntos = fmtPuntos(cliente?.puntos ?? 0)
  const nivel = cliente?.nivel?.nombre

  if (t.includes('nivel')) {
    return nivel
      ? `Estás en nivel **${nivel}**. No pude conectar con el asistente; intenta de nuevo para ver tu avance.`
      : 'No pude conectar con el asistente. Intenta de nuevo en un momento.'
  }
  if (t.includes('punto') || t.includes('saldo')) {
    return `Tienes **${puntos} puntos** disponibles. No pude conectar con el asistente para más detalles.`
  }
  return `No pude conectar con el asistente. Revisa tu conexión e intenta de nuevo. Tu saldo actual es **${puntos} puntos**.`
}

export default function ChatbotWidget({ cliente, onNavegar }) {
  const [abierto, setAbierto] = useState(false)
  const [mensajes, setMensajes] = useState([])
  const [entrada, setEntrada] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')
  const listaRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    if (listaRef.current) {
      listaRef.current.scrollTop = listaRef.current.scrollHeight
    }
  }, [mensajes, cargando, error])

  useEffect(() => {
    if (!abierto) return
    const cerrarConEscape = (e) => {
      if (e.key === 'Escape') setAbierto(false)
    }
    document.addEventListener('keydown', cerrarConEscape)
    const foco = setTimeout(() => inputRef.current?.focus(), 150)
    return () => {
      document.removeEventListener('keydown', cerrarConEscape)
      clearTimeout(foco)
    }
  }, [abierto])

  function agregarMensaje(autor, texto, acciones = []) {
    setMensajes((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), autor, texto, acciones, ts: new Date() },
    ])
  }

  function saludo() {
    const nombre = cliente?.nombre?.trim().split(' ')[0]
    const nivel = cliente?.nivel?.nombre
    const inicio = nombre ? `Hola, ${nombre}.` : 'Hola.'
    const nivelTexto = nivel ? ` y estás en nivel **${nivel}**` : ''
    return `${inicio} Tienes **${fmtPuntos(cliente?.puntos ?? 0)} puntos**${nivelTexto}. ¿En qué te puedo ayudar?`
  }

  function toggle() {
    const nuevo = !abierto
    setAbierto(nuevo)
    if (nuevo && mensajes.length === 0) {
      setTimeout(() => agregarMensaje('bot', saludo()), 200)
    }
  }

  async function enviarTexto(texto) {
    const limpio = texto.trim()
    if (!limpio || cargando) return

    const historial = mensajes.slice(-8).map((m) => ({
      rol: m.autor === 'usuario' ? 'usuario' : 'asistente',
      texto: m.texto,
    }))

    agregarMensaje('usuario', limpio)
    setEntrada('')
    setError('')
    setCargando(true)

    try {
      const data = await api('/asistente/consulta', {
        method: 'POST',
        body: { mensaje: limpio, historial },
      })
      agregarMensaje('bot', data.respuesta, data.acciones || [])
    } catch (e) {
      agregarMensaje('bot', respuestaLocal(limpio, cliente))
      setError(e.message)
    } finally {
      setCargando(false)
    }
  }

  function enviar(e) {
    e.preventDefault()
    enviarTexto(entrada)
  }

  function usarSugerencia(s) {
    enviarTexto(s)
  }

  function navegar(accion) {
    if (!accion?.vista) return
    setAbierto(false)
    onNavegar?.(accion.vista)
  }

  function limpiarChat() {
    setMensajes([])
    setError('')
    setTimeout(() => agregarMensaje('bot', saludo()), 150)
  }

  if (!cliente) return null

  return (
    <>
      {!abierto && (
        <button className="chatbot-fab" onClick={toggle} aria-label="Abrir Chatbot de Ayuda">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </button>
      )}

      {abierto && (
        <div className="chatbot-widget">
          <div className="chatbot-header">
            <div className="chatbot-header-info">
              <div className="chatbot-avatar" aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.9 8.9 0 0 1-3.9-.9L3 21l1.9-5.1A8.4 8.4 0 0 1 12 3.1a8.4 8.4 0 0 1 9 8.4z"></path>
                  <path d="M12 8.2l1 2.1 2.3.3-1.7 1.6.4 2.3-2-1.1-2 1.1.4-2.3-1.7-1.6 2.3-.3z"></path>
                </svg>
              </div>
              <div>
                <div className="chatbot-title">Chatbot de Ayuda</div>
                <div className="chatbot-subtitle">Consultas de tu cuenta</div>
              </div>
            </div>
            <div className="chatbot-header-actions">
              <button className="chatbot-icon-btn" onClick={limpiarChat} title="Limpiar chat" aria-label="Limpiar chat">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"></polyline>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
              <button className="chatbot-icon-btn" onClick={toggle} title="Cerrar" aria-label="Cerrar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>

          <div className="chatbot-mensajes" ref={listaRef} role="log" aria-live="polite">
            {mensajes.map((m) => (
              <div key={m.id} className={`chatbot-mensaje chatbot-mensaje--${m.autor}`}>
                <div className="chatbot-mensaje-bloque">
                  <div className="chatbot-mensaje-burbuja">
                    {m.texto.split('\n').map((linea, idx) => (
                      <div key={idx}>
                        {linea.split(/(\*\*.*?\*\*)/).map((parte, i) => {
                          if (parte.startsWith('**') && parte.endsWith('**')) {
                            return <strong key={i}>{parte.slice(2, -2)}</strong>
                          }
                          return parte
                        })}
                      </div>
                    ))}
                  </div>
                  {m.acciones?.length > 0 && (
                    <div className="chatbot-acciones">
                      {m.acciones.map((a) => (
                        <button
                          key={`${a.vista}-${a.label}`}
                          type="button"
                          className="chatbot-accion"
                          onClick={() => navegar(a)}
                        >
                          {a.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {cargando && (
              <div className="chatbot-mensaje chatbot-mensaje--bot">
                <div className="chatbot-mensaje-burbuja chatbot-mensaje-burbuja--typing">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            {error && <p className="chatbot-error">{error}</p>}
          </div>

          {!mensajes.some((m) => m.autor === 'usuario') && (
            <div className="chatbot-sugerencias">
              {SUGERENCIAS.map((s) => (
                <button key={s} className="chatbot-sugerencia" onClick={() => usarSugerencia(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}

          <form className="chatbot-form" onSubmit={enviar}>
            <input
              ref={inputRef}
              className="chatbot-input"
              type="text"
              value={entrada}
              onChange={(e) => setEntrada(e.target.value)}
              placeholder="Escribe tu pregunta..."
              aria-label="Escribe tu pregunta"
              maxLength={500}
              disabled={cargando}
            />
            <button className="chatbot-enviar" type="submit" disabled={cargando || !entrada.trim()} aria-label="Enviar">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </form>
        </div>
      )}
    </>
  )
}
