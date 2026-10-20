import { useCallback, useEffect, useState } from 'react'
import { api, getToken, setToken } from './api.js'
import Navbar from './components/Navbar.jsx'
import Sidebar from './components/Sidebar.jsx'
import Login from './views/Login.jsx'
import Datos from './views/Datos.jsx'
import Saldo from './views/Saldo.jsx'
import Historial from './views/Historial.jsx'
import Canjes from './views/Canjes.jsx'
import Funcionamiento from './views/Funcionamiento.jsx'
import Ayuda from './views/Ayuda.jsx'
import Recompensas from './views/Recompensas.jsx'

const TABS_CLIENTE = [
  { key: 'datos', label: 'Mis datos' },
  { key: 'historial', label: 'Historial' },
]

export default function App() {
  const [logueado, setLogueado] = useState(!!getToken())
  const [cliente, setCliente] = useState(null)
  const [vista, setVista] = useState('inicio')
  const [error, setError] = useState('')

  const cargarPerfil = useCallback(async () => {
    try {
      setCliente(await api('/clientes/me'))
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    if (logueado) cargarPerfil()
  }, [logueado, cargarPerfil])

  function entrar() {
    setLogueado(true)
    setVista('inicio')
  }

  function salir() {
    setToken('')
    setLogueado(false)
    setCliente(null)
    setVista('inicio')
  }

  function seccion() {
    switch (vista) {
      case 'funcionamiento':
        return <Funcionamiento />
      case 'ayuda':
        return <Ayuda />
      case 'recompensas':
        return logueado ? (
          <Canjes cliente={cliente} refrescar={cargarPerfil} />
        ) : (
          <Recompensas onSesion={() => setVista('inicio')} />
        )
      case 'inicio':
        return logueado ? (
          <Saldo cliente={cliente} refrescar={cargarPerfil} />
        ) : (
          <Login onLogin={entrar} />
        )
      case 'datos':
        return <Datos cliente={cliente} refrescar={cargarPerfil} />
      case 'historial':
        return <Historial cliente={cliente} refrescar={cargarPerfil} />
      default:
        return null
    }
  }

  const enLogin = !logueado && vista === 'inicio'
  const conTabsCliente = logueado && (vista === 'datos' || vista === 'historial')

  return (
    <div className={`app${logueado ? ' con-sidebar' : ''}${conTabsCliente ? ' con-tabs' : ''}`}>
      <Navbar
        vista={vista}
        onNavegar={setVista}
        logueado={logueado}
        puntos={cliente?.puntos}
        onSesion={logueado ? salir : () => setVista('inicio')}
      />

      <div className="contenido">
        {logueado && (
          <Sidebar cliente={cliente} vista={vista} onNavegar={setVista} onSalir={salir} />
        )}

        <div className="contenido-principal">
          {enLogin ? (
            seccion()
          ) : (
            <main className={`vista${vista === 'recompensas' ? ' vista--recompensas' : ''}`}>
              {error && <p className="error">{error}</p>}
              {seccion()}
            </main>
          )}
        </div>
      </div>

      {conTabsCliente && (
        <nav className="tabs" aria-label="Mi cuenta">
          {TABS_CLIENTE.map((t) => (
            <button
              key={t.key}
              type="button"
              className={t.key === vista ? 'activo' : ''}
              aria-current={t.key === vista ? 'page' : undefined}
              onClick={() => setVista(t.key)}
            >
              {t.label}
            </button>
          ))}
        </nav>
      )}
    </div>
  )
}
