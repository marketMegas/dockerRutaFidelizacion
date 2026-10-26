import { useState } from 'react'
import { api, setSesion } from '../api.js'

export default function Login({ onLogin }) {
  const [tipo, setTipo] = useState('admin')
  const [usuario, setUsuario] = useState('admin')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  function cambiarTipo(nuevo) {
    setTipo(nuevo)
    setUsuario(nuevo === 'admin' ? 'admin' : '')
    setPassword('')
    setError('')
  }

  async function entrar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const endpoint = tipo === 'islero' ? '/auth/islero' : '/auth/admin'
      const data = await api(endpoint, { method: 'POST', body: { usuario, password } })
      const rol = data.rol || tipo
      setSesion(data.access_token, rol, data.nombre || '')
      onLogin(rol, data.nombre || '')
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className={tipo === 'islero' ? 'login tema-islero' : 'login'}>
      <form onSubmit={entrar}>
        <h1>{tipo === 'islero' ? 'Módulo de isleros' : 'Panel de control Fidelización g-max'}</h1>
        <p className="muted">{tipo === 'islero' ? 'Registro de clientes en isla' : 'Acceso administrador'}</p>

        <div className="login-tabs" role="tablist" aria-label="Tipo de acceso">
          <button
            type="button"
            role="tab"
            aria-selected={tipo === 'admin'}
            className={tipo === 'admin' ? 'activo' : ''}
            onClick={() => cambiarTipo('admin')}
          >
            Administrador
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tipo === 'islero'}
            className={tipo === 'islero' ? 'activo' : ''}
            onClick={() => cambiarTipo('islero')}
          >
            Islero
          </button>
        </div>

        <label>
          Usuario
          <input value={usuario} onChange={(e) => setUsuario(e.target.value)} autoComplete="username" />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button disabled={cargando}>{cargando ? 'Entrando...' : 'Entrar'}</button>
      </form>
    </div>
  )
}
