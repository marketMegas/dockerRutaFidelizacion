import { useState } from 'react'
import { api, getToken, setToken } from './api.js'
import Login from './views/Login.jsx'
import Dashboard from './views/Dashboard.jsx'
import Clientes from './views/Clientes.jsx'
import Reglas from './views/Reglas.jsx'
import Recompensas from './views/Recompensas.jsx'
import Reportes from './views/Reportes.jsx'

const NAV = [
  { key: 'dashboard', label: 'Resumen', Comp: Dashboard },
  { key: 'clientes', label: 'Clientes', Comp: Clientes },
  { key: 'reglas', label: 'Reglas de puntos', Comp: Reglas },
  { key: 'recompensas', label: 'Recompensas', Comp: Recompensas },
  { key: 'reportes', label: 'Reportes', Comp: Reportes },
]

export default function App() {
  const [logueado, setLogueado] = useState(!!getToken())
  const [vista, setVista] = useState('dashboard')

  if (!logueado) return <Login onLogin={() => setLogueado(true)} />

  const actual = NAV.find((n) => n.key === vista) || NAV[0]
  const Comp = actual.Comp

  function salir() {
    setToken('')
    setLogueado(false)
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1 className="brand">
          Panel de control Fidelización <span>g-max</span>
        </h1>
        <nav>
          {NAV.map((n) => (
            <button key={n.key} className={n.key === vista ? 'activo' : ''} onClick={() => setVista(n.key)}>
              {n.label}
            </button>
          ))}
        </nav>
        <button className="salir" onClick={salir}>
          Cerrar sesión
        </button>
      </aside>
      <main className="contenido">
        <Comp />
      </main>
    </div>
  )
}
