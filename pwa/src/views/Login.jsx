import { useState } from 'react'
import { api, setToken } from '../api.js'

export default function Login({ onLogin }) {
  const [paso, setPaso] = useState('cedula')
  const [cedula, setCedula] = useState('')
  const [telefono, setTelefono] = useState('')
  const [nombre, setNombre] = useState('')
  const [codigo, setCodigo] = useState('')
  const [telefonoParcial, setTelefonoParcial] = useState('')
  const [debug, setDebug] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function pedirCodigo(telefonoRegistro) {
    setError('')
    setCargando(true)
    try {
      const body = { cedula }
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

  async function consultarCedula(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const data = await api('/auth/identificar', { method: 'POST', body: { cedula } })
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
      const data = await api('/auth/otp/verify', { method: 'POST', body: { cedula, codigo } })
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

      {paso === 'cedula' && (
        <form onSubmit={consultarCedula}>
          <label>
            Numero de cedula
            <input
              inputMode="numeric"
              placeholder="Sin puntos ni espacios"
              value={cedula}
              onChange={(e) => setCedula(e.target.value)}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button disabled={cargando}>{cargando ? 'Consultando...' : 'Continuar'}</button>
        </form>
      )}

      {paso === 'registro' && (
        <form onSubmit={registrar}>
          <p className="muted">No encontramos tu cedula. Registrate para empezar.</p>
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
          <button type="button" className="link" onClick={() => setPaso('cedula')}>
            Cambiar cedula
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
          <button type="button" className="link" onClick={() => setPaso('cedula')}>
            Cambiar cedula
          </button>
        </form>
      )}
    </div>
  )
}
