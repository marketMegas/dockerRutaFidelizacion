const SECCIONES = [
  { key: 'inicio', label: 'Inicio' },
  { key: 'funcionamiento', label: 'Funcionamiento' },
  { key: 'recompensas', label: 'Recompensas' },
  { key: 'ayuda', label: 'Ayuda' },
]

export default function Navbar({ vista, onNavegar, logueado, puntos, onSesion }) {
  return (
    <header className="navbar">
      <div className="navbar-fila">
        <div className="navbar-logo">
          <span className="navbar-marca">Fidelización puntos g-max</span>
        </div>

        <div className="navbar-acciones">
          {logueado && (
            <div className="saldo-mini">
              <span className="saldo-mini-v">{puntos ?? '-'}</span>
              <span className="saldo-mini-t">puntos</span>
            </div>
          )}
          <button
            type="button"
            className={`sesion ${logueado ? 'salir' : 'primario'}`}
            onClick={onSesion}
          >
            {logueado ? 'Salir' : 'Iniciar sesión'}
          </button>
        </div>
      </div>

      <nav className="navbar-tabs" aria-label="Secciones">
        {SECCIONES.map((s) => (
          <button
            key={s.key}
            type="button"
            className={s.key === vista ? 'activo' : ''}
            aria-current={s.key === vista ? 'page' : undefined}
            onClick={() => onNavegar(s.key)}
          >
            {s.label}
          </button>
        ))}
      </nav>
    </header>
  )
}
