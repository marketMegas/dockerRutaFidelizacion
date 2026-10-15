import { useEffect, useState } from 'react'
import { api } from '../api.js'

const VACIA = { nombre: '', puntos_por_litro: 1, prioridad: 0, activa: true }

export default function Reglas() {
  const [reglas, setReglas] = useState([])
  const [form, setForm] = useState(VACIA)
  const [error, setError] = useState('')

  function cargar() {
    api('/admin/reglas').then(setReglas).catch((e) => setError(e.message))
  }

  useEffect(() => {
    cargar()
  }, [])

  async function crear(e) {
    e.preventDefault()
    setError('')
    try {
      await api('/admin/reglas', {
        method: 'POST',
        body: { ...form, puntos_por_litro: Number(form.puntos_por_litro), prioridad: Number(form.prioridad) },
      })
      setForm(VACIA)
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  async function alternar(r) {
    try {
      await api(`/admin/reglas/${r.id}`, { method: 'PUT', body: { ...r, activa: !r.activa } })
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <h2>Reglas de puntos</h2>
      <p className="muted">Los puntos se calculan por litro. Gana la regla activa con mayor prioridad.</p>
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Puntos / litro</th>
            <th>Prioridad</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {reglas.map((r) => (
            <tr key={r.id}>
              <td>{r.nombre}</td>
              <td>{r.puntos_por_litro}</td>
              <td>{r.prioridad}</td>
              <td>{r.activa ? 'Activa' : 'Inactiva'}</td>
              <td>
                <button onClick={() => alternar(r)}>{r.activa ? 'Desactivar' : 'Activar'}</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Nueva regla</h3>
      <form className="fila" onSubmit={crear}>
        <input
          placeholder="Nombre"
          value={form.nombre}
          onChange={(e) => setForm({ ...form, nombre: e.target.value })}
          required
        />
        <input
          type="number"
          step="0.01"
          min="0"
          value={form.puntos_por_litro}
          onChange={(e) => setForm({ ...form, puntos_por_litro: e.target.value })}
        />
        <input
          type="number"
          value={form.prioridad}
          onChange={(e) => setForm({ ...form, prioridad: e.target.value })}
        />
        <button>Crear</button>
      </form>
    </div>
  )
}
