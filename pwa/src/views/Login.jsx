import { useEffect, useState } from 'react'
import { api, setToken } from '../api.js'
import RecompensaCard from '../components/RecompensaCard.jsx'

export default function Login({ onLogin }) {
  const [recompensas, setRecompensas] = useState([])
  const [tasa, setTasa] = useState(0)
  const [paso, setPaso] = useState('placa')
  const [placa, setPlaca] = useState('')
  const [telefono, setTelefono] = useState('')
  const [nombre, setNombre] = useState('')
  const [codigo, setCodigo] = useState('')
  const [telefonoParcial, setTelefonoParcial] = useState('')
  const [debug, setDebug] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    api('/recompensas').then(setRecompensas).catch(() => {})
    api('/config').then((c) => setTasa(c.puntos_por_litro)).catch(() => {})
  }, [])

  async function pedirCodigo(telefonoRegistro) {
    setError('')
    setCargando(true)
    try {
      const body = { placa }
      if (telefonoRegistro) {
        body.telefono = telefonoRegistro
        body.nombre = nombre
      }
      const data = await api('/auth/otp/request', { method: 'POST', body })
      setTelefonoParcial(data.telefono_parcial || '')
      setDebug(data.debug_codigo || '')
      setPaso('codigo')
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  async function consultarPlaca(e) {
    e.preventDefault()
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
        <div className="llama" />
        <h1>GasLP Puntos</h1>
        <p>Suma puntos por cada litro que cargas y canjealos por recompensas.</p>
      </div>

      {paso === 'placa' && (
        <form onSubmit={consultarPlaca}>
          <label>
            Numero de placa
            <input
              className="entrada-placa"
              placeholder="Ej. ABC123"
              autoComplete="off"
              autoCapitalize="characters"
              value={placa}
              onChange={(e) => setPlaca(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 10))}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button disabled={cargando}>{cargando ? 'Consultando...' : 'Continuar'}</button>
        </form>
      )}

      {paso === 'registro' && (
        <form onSubmit={registrar}>
          <p className="muted">No encontramos tu placa. Registrate para empezar.</p>
          <label>
            Numero de celular
            <input
              inputMode="tel"
              placeholder="300 000 0000"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
              required
            />
          </label>
          <label>
            Tu nombre
            <input placeholder="Opcional" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </label>
          {error && <p className="error">{error}</p>}
          <button disabled={cargando}>{cargando ? 'Enviando...' : 'Recibir codigo'}</button>
          <button type="button" className="link" onClick={() => setPaso('placa')}>
            Cambiar placa
          </button>
        </form>
      )}

      {paso === 'codigo' && (
        <form onSubmit={verificar}>
          <p className="muted">Enviamos un codigo al celular {telefonoParcial}.</p>
          <label>
            Codigo de verificacion
            <input
              inputMode="numeric"
              maxLength="6"
              placeholder="000000"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              required
            />
          </label>
          {debug && <p className="demo">Codigo de prueba: {debug}</p>}
          {error && <p className="error">{error}</p>}
          <button disabled={cargando}>{cargando ? 'Verificando...' : 'Entrar'}</button>
          <button type="button" className="link" onClick={() => setPaso('placa')}>
            Cambiar placa
          </button>
        </form>
      )}

      {recompensas.length > 0 && (
        <section className="login-premios">
          <h2>Recompensas</h2>
          <div className="premios">
            {recompensas.map((r) => (
              <RecompensaCard key={r.id} recompensa={r} tasa={tasa} mostrarProgreso={false} sobreVerde />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
