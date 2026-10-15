import { useEffect, useState } from 'react'
import { api } from '../api.js'

const VACIA = { nombre: '', descripcion: '', costo_puntos: 100, stock: 10, activa: true }

export default function Recompensas() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState(VACIA)
  const [error, setError] = useState('')

  function cargar() {
    api('/admin/recompensas').then(setItems).catch((e) => setError(e.message))
  }

  useEffect(() => {
    cargar()
  }, [])

  async function crear(e) {
    e.preventDefault()
    setError('')
    try {
      await api('/admin/recompensas', {
        method: 'POST',
        body: { ...form, costo_puntos: Number(form.costo_puntos), stock: Number(form.stock) },
      })
      setForm(VACIA)
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  async function alternar(r) {
    try {
      await api(`/admin/recompensas/${r.id}`, { method: 'PUT', body: { ...r, activa: !r.activa } })
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <h2>Recompensas</h2>
      {error && <p className="error">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Descripcion</th>
            <th>Costo (pts)</th>
            <th>Stock</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => (
            <tr key={r.id}>
              <td>{r.nombre}</td>
              <td>{r.descripcion || '-'}</td>
              <td>{r.costo_puntos}</td>
              <td>{r.stock}</td>
              <td>{r.activa ? 'Activa' : 'Inactiva'}</td>
              <td>
                <button onClick={() => alternar(r)}>{r.activa ? 'Desactivar' : 'Activar'}</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Nueva recompensa</h3>
      <form className="fila" onSubmit={crear}>
        <input
          placeholder="Nombre"
          value={form.nombre}
          onChange={(e) => setForm({ ...form, nombre: e.target.value })}
          required
        />
        <input
          placeholder="Descripcion"
          value={form.descripcion}
          onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
        />
        <input
          type="number"
          min="1"
          value={form.costo_puntos}
          onChange={(e) => setForm({ ...form, costo_puntos: e.target.value })}
        />
        <input type="number" min="0" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} />
        <button>Crear</button>
      </form>
    </div>
  )
}
