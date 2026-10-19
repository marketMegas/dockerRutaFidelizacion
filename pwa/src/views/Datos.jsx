import { fmtFecha } from '../api.js'

export default function Datos({ cliente, refrescar }) {
  if (!cliente) return <p className="muted">Cargando...</p>

  const filas = [
    { k: 'Placa', v: cliente.placa || '-' },
    { k: 'Celular', v: cliente.telefono },
    { k: 'Nombre', v: cliente.nombre || '-' },
  ]
  if (cliente.email) filas.push({ k: 'Email', v: cliente.email })
  filas.push({ k: 'Miembro desde', v: fmtFecha(cliente.created_at) })

  return (
    <div className="datos">
      <h2>Mis datos</h2>

      <div className="saldo">
        <span className="saldo-v">{cliente.puntos}</span>
        <span className="saldo-t">puntos disponibles</span>
      </div>

      <ul className="lista">
        {filas.map((f) => (
          <li key={f.k}>
            <div className="lista-info">
              <strong>{f.k}</strong>
            </div>
            <span className="valor">{f.v}</span>
          </li>
        ))}
      </ul>

      <button className="primario" onClick={refrescar}>
        Actualizar mis datos
      </button>
    </div>
  )
}
