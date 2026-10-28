import { useEffect, useMemo, useRef, useState } from 'react'
import { api, fmtFecha, fmtPuntos } from '../api.js'
import './ChatbotWidget.css'

const SUGERENCIAS = [
  '¿Cuántos puntos tengo?',
  '¿Cuánto he redimido?',
  '¿Qué he canjeado?',
  '¿Cuál es mi nivel?',
  '¿Puedo canjear?',
]

function normalizar(texto) {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .trim()
}

function detectarIntent(pregunta) {
  const t = normalizar(pregunta)

  if (t.includes('ayuda') || t.includes('hola') || t.includes('como usar') || t === '') {
    return 'ayuda'
  }
  if (t.includes('nivel')) {
    return 'nivel'
  }
  if (t.includes('puedo canjear') || t.includes('cuando puedo canjear')) {
    return 'puedo_canjear'
  }
  if ((t.includes('que') && (t.includes('canje') || t.includes('he canjeado'))) || t.includes('mis canjes') || t.includes('premios que')) {
    return 'lista_canjes'
  }
  if (t.includes('redimid') || t.includes('gastad') || (t.includes('cuanto') && t.includes('he')) || (t.includes('puntos') && (t.includes('redim') || t.includes('usad')))) {
    return 'redimidos_total'
  }
  if ((t.includes('cuanto') || t.includes('cuantos')) && t.includes('punto')) {
    return 'saldo'
  }
  if (t.includes('punto') && !t.includes('redim') && !t.includes('gast')) {
    return 'saldo'
  }
  return 'desconocido'
}

export default function ChatbotWidget({ cliente }) {
  const [abierto, setAbierto] = useState(false)
  const [mensajes, setMensajes] = useState([])
  const [entrada, setEntrada] = useState('')
  const [cargando, setCargando] = useState(false)
  const [misCanjes, setMisCanjes] = useState([])
  const [cargadosCanjes, setCargadosCanjes] = useState(false)
  const listaRef = useRef(null)

  const puntos = cliente?.puntos ?? 0
  const nivel = cliente?.nivel

  useEffect(() => {
    if (listaRef.current) {
      listaRef.current.scrollTop = listaRef.current.scrollHeight
    }
  }, [mensajes])

  useEffect(() => {
    if (abierto && !cargadosCanjes && cliente) {
      setCargando(true)
      api('/canjes/mis')
        .then((data) => {
          setMisCanjes(Array.isArray(data) ? data : [])
          setCargadosCanjes(true)
        })
        .catch(() => {
          setMisCanjes([])
          setCargadosCanjes(true)
        })
        .finally(() => setCargando(false))
    }
  }, [abierto, cargadosCanjes, cliente])

  const totalRedimido = useMemo(() => {
    return misCanjes.reduce((acc, c) => acc + (Number(c.puntos_costo) || 0), 0)
  }, [misCanjes])

  function agregarMensaje(autor, texto) {
    setMensajes((prev) => [...prev, { id: Date.now() + Math.random(), autor, texto, ts: new Date() }])
  }

  function responder(pregunta) {
    const intent = detectarIntent(pregunta)
    if (intent === 'ayuda') {
      return 'Puedo ayudarte con: puntos disponibles, puntos redimidos, mis canjes, nivel y si puedes canjear. Elige una sugerencia o escribe tu pregunta.'
    }
    if (intent === 'nivel') {
      if (nivel) {
        if (typeof nivel === 'object') {
          return `Tu nivel actual es **${nivel.nombre || 'Sin nivel'}**${nivel.multiplicador ? ` (multiplicador x${nivel.multiplicador})` : ''}.`
        }
        return `Tu nivel actual es **${nivel}**.`
      }
      return 'No tengo información de tu nivel en este momento.'
    }
    if (intent === 'saldo') {
      return `Tienes **${fmtPuntos(puntos)}** puntos disponibles.`
    }
    if (intent === 'redimidos_total') {
      if (misCanjes.length === 0) {
        return 'Aún no has redimido ningún premio. Tienes **' + fmtPuntos(puntos) + '** puntos disponibles.'
      }
      return `Has redimido **${fmtPuntos(totalRedimido)}** puntos en **${misCanjes.length}** canje${misCanjes.length === 1 ? '' : 's'}.`
    }
    if (intent === 'lista_canjes') {
      if (misCanjes.length === 0) {
        return 'Aún no has canjeado premios. Puedes ver las recompensas disponibles en la sección Recompensas.'
      }
      const ultimos = misCanjes.slice(0, 5)
      const lineas = ultimos.map((c) => `- ${c.premio || c.premio_nombre} · ${fmtPuntos(c.puntos_costo)} pts · ${fmtFecha(c.created_at)}`)
      return `Tus últimos canjes:\n${lineas.join('\n')}${misCanjes.length > 5 ? `\n... y ${misCanjes.length - 5} más` : ''}`
    }
    if (intent === 'puedo_canjear') {
      if (puntos <= 0) {
        return 'No tienes puntos suficientes para canjear en este momento.'
      }
      return `Sí puedes canjear. Tienes **${fmtPuntos(puntos)}** puntos. Revisa las recompensas disponibles para ver qué premios se ajustan a tu saldo.`
    }
    return 'No entendí tu pregunta. Prueba con alguna de estas: "¿Cuántos puntos tengo?", "¿Cuánto he redimido?", "¿Qué he canjeado?", "¿Cuál es mi nivel?".'
  }

  function enviar(e) {
    e.preventDefault()
    const texto = entrada.trim()
    if (!texto || cargando) return
    agregarMensaje('usuario', texto)
    setEntrada('')
    setCargando(true)
    setTimeout(() => {
      const resp = responder(texto)
      agregarMensaje('bot', resp)
      setCargando(false)
    }, 300)
  }

  function usarSugerencia(s) {
    if (cargando) return
    agregarMensaje('usuario', s)
    setCargando(true)
    setTimeout(() => {
      const resp = responder(s)
      agregarMensaje('bot', resp)
      setCargando(false)
    }, 250)
  }

  function toggle() {
    setAbierto((v) => {
      const nuevo = !v
      if (nuevo && mensajes.length === 0) {
        setTimeout(() => {
          agregarMensaje('bot', 'Hola! Soy tu asistente de puntos. Pregúntame sobre tus puntos, redenciones o nivel.')
        }, 200)
      }
      return nuevo
    })
  }

  function limpiarChat() {
    setMensajes([])
    setTimeout(() => {
      agregarMensaje('bot', 'Chat limpio. ¿En qué te puedo ayudar?')
    }, 150)
  }

  if (!cliente) return null

  return (
    <>
      {!abierto && (
        <button className="chatbot-fab" onClick={toggle} aria-label="Abrir asistente de puntos">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </button>
      )}

      {abierto && (
        <div className="chatbot-widget">
          <div className="chatbot-header">
            <div className="chatbot-header-info">
              <div className="chatbot-avatar">🤖</div>
              <div>
                <div className="chatbot-title">Asistente de Puntos</div>
                <div className="chatbot-subtitle">Solo para consultas</div>
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

          <div className="chatbot-mensajes" ref={listaRef}>
            {mensajes.map((m) => (
              <div key={m.id} className={`chatbot-mensaje chatbot-mensaje--${m.autor}`}>
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
          </div>

          {mensajes.length === 0 && (
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
              className="chatbot-input"
              type="text"
              value={entrada}
              onChange={(e) => setEntrada(e.target.value)}
              placeholder="Escribe tu pregunta..."
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
