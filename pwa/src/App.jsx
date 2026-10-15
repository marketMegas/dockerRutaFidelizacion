import { useCallback, useEffect, useState } from 'react'
import { api, getToken, setToken } from './api.js'
import Login from './views/Login.jsx'
import Inicio from './views/Inicio.jsx'
import Historial from './views/Historial.jsx'
import Canjes from './views/Canjes.jsx'

const TABS = [
  { key: 'inicio', label: 'Mi QR', Comp: Inicio },
  { key: 'historial', label: 'Historial', Comp: Historial },
  { key: 'canjes', label: 'Recompensas', Comp: Canjes },
]

export default function App() {
  const [logueado, setLogueado] = useState(!!getToken())
  const [cliente, setCliente] = useState(null)
  const [tab, setTab] = useState('inicio')
  const [error, setError] = useState('')

  const cargarPerfil = useCallback(async () => {
    try {
      setCliente(await api('/clientes/me'))
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    if (logueado) cargarPerfil()
  }, [logueado, cargarPerfil])

  if (!logueado) return <Login onLogin={() => setLogueado(true)} />

  const actual = TABS.find((t) => t.key === tab) || TABS[0]
  const Comp = actual.Comp

  function salir() {
    setToken('')
    setLogueado(false)
    setCliente(null)
  }

  return (
    <div className="app">
      <header className="cabecera">
        <div>
          <span className="saludo">Hola</span>
          <strong>{cliente?.nombre || cliente?.telefono || '...'}</strong>
        </div>
        <div className="saldo-mini">
          <span className="saldo-mini-v">{cliente?.puntos ?? '-'}</span>
          <span className="saldo-mini-t">puntos</span>
        </div>
      </header>

      <main className="vista">
        {error && <p className="error">{error}</p>}
        <Comp cliente={cliente} refrescar={cargarPerfil} />
      </main>

      <nav className="tabs">
        {TABS.map((t) => (
          <button key={t.key} className={t.key === tab ? 'activo' : ''} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
        <button className="salir" onClick={salir}>
          Salir
        </button>
      </nav>
    </div>
  )
}
