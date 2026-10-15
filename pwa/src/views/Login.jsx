import { useState } from 'react'
import { api, setToken } from '../api.js'

export default function Login({ onLogin }) {
  const [paso, setPaso] = useState('telefono')
  const [telefono, setTelefono] = useState('')
  const [nombre, setNombre] = useState('')
  const [codigo, setCodigo] = useState('')
  const [debug, setDebug] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function pedirCodigo(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const data = await api('/auth/otp/request', { method: 'POST', body: { telefono, nombre } })
      if (data.debug_codigo) setDebug(data.debug_codigo)
      setPaso('codigo')
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  async function verificar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const data = await api('/auth/otp/verify', { method: 'POST', body: { telefono, codigo } })
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

      {paso === 'telefono' ? (
        <form onSubmit={pedirCodigo}>
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
        </form>
      ) : (
        <form onSubmit={verificar}>
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
          <button type="button" className="link" onClick={() => setPaso('telefono')}>
            Cambiar numero
          </button>
        </form>
      )}
    </div>
  )
}
