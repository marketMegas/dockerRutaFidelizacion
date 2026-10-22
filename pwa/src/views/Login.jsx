import { useEffect, useState } from 'react'
import { api, setToken } from '../api.js'
import RecompensaCard from '../components/RecompensaCard.jsx'

const PLACA_RE = /^[A-Z]{3}[0-9]{3}$/
const PLACA_MSG = 'La placa debe tener 3 letras y 3 números (ej. ABC123)'
const CEDULA_RE = /^[0-9]{6,10}$/
const CEDULA_MSG = 'La cédula debe tener solo números (6 a 10)'

const TITULOS = {
  placa: 'Registra tu placa',
  registro: 'Crea tu cuenta',
  codigo: 'Verifica tu código',
}

const HEROES = [
  'https://images.pexels.com/photos/40431732/pexels-photo-40431732.jpeg',
  'https://images.pexels.com/photos/40431768/pexels-photo-40431768.jpeg',
]
const HERO_MS = 5000

function formatearPlaca(valor) {
  const limpio = valor.toUpperCase().replace(/[^A-Z0-9]/g, '')
  const letras = limpio.replace(/[0-9]/g, '').slice(0, 3)
  const numeros = limpio.replace(/[A-Z]/g, '').slice(0, 3)
  return letras + numeros
}

export default function Login({ onLogin }) {
  const [premios, setPremios] = useState([])
  const [paso, setPaso] = useState('placa')
  const [placa, setPlaca] = useState('')
  const [telefono, setTelefono] = useState('')
  const [cedula, setCedula] = useState('')
  const [nombre, setNombre] = useState('')
  const [codigo, setCodigo] = useState('')
  const [telefonoParcial, setTelefonoParcial] = useState('')
  const [aviso, setAviso] = useState('')
  const [debug, setDebug] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)
  const [heroe, setHeroe] = useState(0)

  useEffect(() => {
    api('/catalogo')
      .then((data) => setPremios(data.premios || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const id = setInterval(() => setHeroe((i) => (i + 1) % HEROES.length), HERO_MS)
    return () => clearInterval(id)
  }, [])

  async function pedirCodigo(telefonoRegistro) {
    setError('')
    setCargando(true)
    try {
      const body = { placa }
      if (telefonoRegistro) {
        body.telefono = telefonoRegistro
        body.cedula = cedula
        body.nombre = nombre
      }
      const data = await api('/auth/otp/request', { method: 'POST', body })
      setTelefonoParcial(data.telefono_parcial || '')
      setDebug(data.debug_codigo || '')
      setAviso(data.placa_nueva && !data.cliente_nuevo ? 'Agregaremos esta placa a tu cuenta.' : '')
      setPaso('codigo')
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  async function consultarPlaca(e) {
    e.preventDefault()
    if (!PLACA_RE.test(placa)) {
      setError(PLACA_MSG)
      return
    }
    setError('')
    setCargando(true)
    try {
      const data = await api('/auth/identificar', { method: 'POST', body: { placa } })
      if (data.existe) {
        await pedirCodigo()
      } else {
        setPaso('registro')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  async function registrar(e) {
    e.preventDefault()
    if (!PLACA_RE.test(placa)) {
      setPaso('placa')
      setError(PLACA_MSG)
      return
    }
    if (!CEDULA_RE.test(cedula)) {
      setError(CEDULA_MSG)
      return
    }
    await pedirCodigo(telefono)
  }

  async function verificar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const data = await api('/auth/otp/verify', { method: 'POST', body: { placa, codigo } })
      setToken(data.access_token)
      onLogin()
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="login">
      <div className="login-hero">
        <div className="login-hero-texto">
          <h1>
            <span className="login-hero-label">Programa:</span>
            Fidelización puntos g-max
          </h1>
          <p>Suma puntos por cada litro que cargas. Mientras más cargues, más puntos por litro.</p>
        </div>

        <div className="login-hero-carrusel">
          {HEROES.map((url, i) => (
            <img
              key={url}
              className={`login-hero-banner${i === heroe ? ' activa' : ''}`}
              src={url}
              alt=""
              decoding="async"
              loading={i === 0 ? 'eager' : 'lazy'}
              referrerPolicy="no-referrer"
            />
          ))}

          <div className="login-hero-puntos">
            {HEROES.map((url, i) => (
              <button
                key={url}
                type="button"
                className={i === heroe ? 'activo' : ''}
                onClick={() => setHeroe(i)}
                aria-label={`Ver la foto ${i + 1} de ${HEROES.length}`}
                aria-current={i === heroe}
              />
            ))}
          </div>
        </div>
      </div>

      {paso === 'placa' && (
        <form onSubmit={consultarPlaca}>
          <h2 className="login-panel-titulo">{TITULOS.placa}</h2>
          <label>
            Número de placa
            <input
              className="entrada-placa"
              placeholder="ABC123"
              autoComplete="off"
              autoCapitalize="characters"
              spellCheck={false}
              maxLength={6}
              pattern="[A-Za-z]{3}[0-9]{3}"
              title="3 letras y 3 números (ej. ABC123)"
              aria-invalid={placa.length > 0 && !PLACA_RE.test(placa)}
              value={placa}
              onChange={(e) => setPlaca(formatearPlaca(e.target.value))}
              required
            />
          </label>
          <p className="muted">3 letras y 3 números (ABC123)</p>
          {error && <p className="error">{error}</p>}
          <button disabled={cargando}>{cargando ? 'Consultando...' : 'Continuar'}</button>
        </form>
      )}

      {paso === 'registro' && (
        <form onSubmit={registrar}>
          <h2 className="login-panel-titulo">{TITULOS.registro}</h2>
          <p className="muted">No encontramos tu placa. Regístrate para empezar.</p>
          <label>
            Número de celular
            <input
              inputMode="tel"
              placeholder="300 000 0000"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
              required
            />
          </label>
          <label>
            Número de cédula
            <input
              inputMode="numeric"
              placeholder="1098765432"
              value={cedula}
              onChange={(e) => setCedula(e.target.value.replace(/[^0-9]/g, '').slice(0, 10))}
              required
            />
          </label>
          <p className="muted">La cédula identifica tu cuenta en la estación.</p>
          <label>
            Tu nombre
            <input placeholder="Opcional" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </label>
          {error && <p className="error">{error}</p>}
          <button disabled={cargando}>{cargando ? 'Enviando...' : 'Recibir código'}</button>
          <button type="button" className="link" onClick={() => setPaso('placa')}>
            Cambiar placa
          </button>
        </form>
      )}

      {paso === 'codigo' && (
        <form onSubmit={verificar}>
          <h2 className="login-panel-titulo">{TITULOS.codigo}</h2>
          <p className="muted">Enviamos un código al celular {telefonoParcial}.</p>
          {aviso && <p className="ok">{aviso}</p>}
          <label>
            Código de verificación
            <input
              className="otp"
              inputMode="numeric"
              maxLength="6"
              placeholder="000000"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              required
            />
          </label>
          {debug && <p className="demo">Código de prueba: {debug}</p>}
          {error && <p className="error">{error}</p>}
          <button disabled={cargando}>{cargando ? 'Verificando...' : 'Entrar'}</button>
          <button type="button" className="link" onClick={() => setPaso('placa')}>
            Cambiar placa
          </button>
        </form>
      )}

      {premios.length > 0 && (
        <section className="login-premios">
          <h2>Recompensas</h2>
          <div className="premios">
            {premios.map((r) => (
              <RecompensaCard key={r.clave} recompensa={r} mostrarProgreso={false} sobreMenta />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
