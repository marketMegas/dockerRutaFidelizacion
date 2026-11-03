import { useState } from 'react'
import { getNombre, getRol, getToken, limpiarSesion } from './api.js'
import Login from './views/Login.jsx'
import Dashboard from './views/Dashboard.jsx'
import Clientes from './views/Clientes.jsx'
import Reglas from './views/Reglas.jsx'
import Niveles from './views/Niveles.jsx'
import Catalogo from './views/Catalogo.jsx'
import Reportes from './views/Reportes.jsx'
import Isleros from './views/Isleros.jsx'
import IsleroRegistro from './views/IsleroRegistro.jsx'

const NAV_ADMIN = [
  { key: 'dashboard', label: 'Resumen', Comp: Dashboard },
  { key: 'clientes', label: 'Clientes', Comp: Clientes },
  { key: 'reglas', label: 'Reglas de puntos', Comp: Reglas },
  { key: 'niveles', label: 'Niveles', Comp: Niveles },
  { key: 'catalogo', label: 'Catálogo', Comp: Catalogo },
  { key: 'reportes', label: 'Reportes', Comp: Reportes },
  { key: 'isleros', label: 'Isleros', Comp: Isleros },
]

const NAV_ISLERO = [{ key: 'registro', label: 'Registrar cliente', Comp: IsleroRegistro }]

function vistaInicial(rol) {
  return rol === 'islero' ? 'registro' : 'dashboard'
}

export default function App() {
  const [logueado, setLogueado] = useState(!!getToken())
  const [rol, setRol] = useState(getRol())
  const [nombre, setNombre] = useState(getNombre())
  const [vista, setVista] = useState(vistaInicial(getRol()))

  if (!logueado) {
    return (
      <Login
        onLogin={(nuevoRol, nuevoNombre) => {
          setRol(nuevoRol)
          setNombre(nuevoNombre)
          setVista(vistaInicial(nuevoRol))
          setLogueado(true)
        }}
      />
    )
  }

  const nav = rol === 'islero' ? NAV_ISLERO : NAV_ADMIN
  const actual = nav.find((n) => n.key === vista) || nav[0]
  const Comp = actual.Comp

  function salir() {
    limpiarSesion()
    setLogueado(false)
    setRol('admin')
    setNombre('')
    setVista('dashboard')
  }

  return (
    <div className={rol === 'islero' ? 'layout layout-islero' : 'layout'}>

      <aside className="sidebar">
        <h1 className="brand">
          {rol === 'islero' ? 'Módulo de isleros' : 'Panel de control Fidelización'} <span>g-max</span>
        </h1>
        {nombre && <p className="sidebar-usuario">{nombre}</p>}
        <nav>
          {nav.map((n) => (
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
