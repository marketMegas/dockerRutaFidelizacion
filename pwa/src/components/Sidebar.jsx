const PRINCIPAL = [
  { key: 'inicio', label: 'Inicio' },
  { key: 'recompensas', label: 'Recompensas' },
  { key: 'historial', label: 'Historial' },
  { key: 'datos', label: 'Mis datos' },
]

const SECUNDARIO = [
  { key: 'funcionamiento', label: 'Funcionamiento' },
  { key: 'ayuda', label: 'Ayuda' },
]

export default function Sidebar({ cliente, vista, onNavegar, onSalir }) {
  const placas = cliente?.placas?.length ? cliente.placas : cliente?.placa ? [cliente.placa] : []

  function item(n) {
    return (
      <button
        key={n.key}
        type="button"
        className={n.key === vista ? 'activo' : ''}
        aria-current={n.key === vista ? 'page' : undefined}
        onClick={() => onNavegar(n.key)}
      >
        {n.label}
      </button>
    )
  }

  return (
    <aside className="sidebar" aria-label="Mi cuenta">
      <div className="sidebar-cuenta">
        <div className="sidebar-id">
          <span className="saludo">Hola</span>
          <strong>{cliente?.nombre || 'Cliente'}</strong>
          <span className="muted">{cliente?.telefono || '-'}</span>
          <span className="muted">{cliente?.cedula ? `C.C. ${cliente.cedula}` : 'Sin cedula'}</span>
        </div>
      </div>

      <div className="sidebar-puntos">
        <span className="sidebar-puntos-v">{cliente?.puntos ?? 0}</span>
        <span className="sidebar-puntos-t">puntos disponibles</span>
      </div>

      {placas.length > 0 && (
        <div className="sidebar-placas">
          {placas.map((p) => (
            <span key={p} className="placa-chip">
              {p}
            </span>
          ))}
        </div>
      )}

      <nav className="sidebar-nav" aria-label="Secciones de la cuenta">
        {PRINCIPAL.map(item)}
      </nav>

      <nav className="sidebar-nav sidebar-nav--sec" aria-label="Mas informacion">
        {SECUNDARIO.map(item)}
      </nav>

      <button type="button" className="sidebar-salir" onClick={onSalir}>
        Cerrar sesion
      </button>
    </aside>
  )
}
