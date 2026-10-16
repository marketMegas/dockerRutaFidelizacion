import { useEffect, useState } from 'react'
import { api } from '../api.js'

const VACIA = { nombre: '', descripcion: '', imagen: '', costo_puntos: 100, stock: 10, activa: true }

function aNumero(valor) {
  return Number(valor)
}

export default function Recompensas() {
  const [items, setItems] = useState([])
  const [form, setForm] = useState(VACIA)
  const [editando, setEditando] = useState(null)
  const [edit, setEdit] = useState(null)
  const [error, setError] = useState('')

  function cargar() {
    api('/admin/recompensas').then(setItems).catch((e) => setError(e.message))
  }

  useEffect(() => {
    cargar()
  }, [])

  function cambiar(setter, campo) {
    return (e) => setter((prev) => ({ ...prev, [campo]: e.target.value }))
  }

  async function crear(e) {
    e.preventDefault()
    setError('')
    try {
      await api('/admin/recompensas', {
        method: 'POST',
        body: {
          ...form,
          imagen: form.imagen.trim() || null,
          costo_puntos: aNumero(form.costo_puntos),
          stock: aNumero(form.stock),
        },
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

  function editar(r) {
    setError('')
    setEditando(r.id)
    setEdit({
      nombre: r.nombre,
      descripcion: r.descripcion || '',
      imagen: r.imagen || '',
      costo_puntos: r.costo_puntos,
      stock: r.stock,
      activa: r.activa,
    })
  }

  function cancelar() {
    setEditando(null)
    setEdit(null)
  }

  async function guardar() {
    setError('')
    try {
      await api(`/admin/recompensas/${editando}`, {
        method: 'PUT',
        body: {
          ...edit,
          imagen: edit.imagen.trim() || null,
          costo_puntos: aNumero(edit.costo_puntos),
          stock: aNumero(edit.stock),
        },
      })
      cancelar()
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <h2>Recompensas</h2>
      <p className="muted">La imagen es una URL publica que se muestra en la tarjeta de la PWA.</p>
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Imagen</th>
            <th>Nombre</th>
            <th>Descripcion</th>
            <th>Costo (pts)</th>
            <th>Stock</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((r) => {
            if (editando === r.id) {
              return (
                <tr key={r.id}>
                  <td>
                    <input
                      type="url"
                      placeholder="https://..."
                      value={edit.imagen}
                      onChange={cambiar(setEdit, 'imagen')}
                    />
                  </td>
                  <td>
                    <input value={edit.nombre} onChange={cambiar(setEdit, 'nombre')} required />
                  </td>
                  <td>
                    <input value={edit.descripcion} onChange={cambiar(setEdit, 'descripcion')} />
                  </td>
                  <td>
                    <input
                      type="number"
                      min="1"
                      value={edit.costo_puntos}
                      onChange={cambiar(setEdit, 'costo_puntos')}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      min="0"
                      value={edit.stock}
                      onChange={cambiar(setEdit, 'stock')}
                    />
                  </td>
                  <td>
                    <input
                      type="checkbox"
                      checked={!!edit.activa}
                      onChange={(e) => setEdit({ ...edit, activa: e.target.checked })}
                    />
                  </td>
                  <td>
                    <button onClick={guardar}>Guardar</button>
                    <button onClick={cancelar}>Cancelar</button>
                  </td>
                </tr>
              )
            }
            return (
              <tr key={r.id}>
                <td>
                  {r.imagen ? (
                    <img className="miniatura" src={r.imagen} alt="" />
                  ) : (
                    <span className="miniatura miniatura-vacia" />
                  )}
                </td>
                <td>{r.nombre}</td>
                <td>{r.descripcion || '-'}</td>
                <td>{r.costo_puntos}</td>
                <td>{r.stock}</td>
                <td>{r.activa ? 'Activa' : 'Inactiva'}</td>
                <td>
                  <button onClick={() => editar(r)}>Editar</button>
                  <button onClick={() => alternar(r)}>{r.activa ? 'Desactivar' : 'Activar'}</button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <h3>Nueva recompensa</h3>
      <form className="fila" onSubmit={crear}>
        <input
          placeholder="Nombre"
          value={form.nombre}
          onChange={cambiar(setForm, 'nombre')}
          required
        />
        <input
          placeholder="Descripcion"
          value={form.descripcion}
          onChange={cambiar(setForm, 'descripcion')}
        />
        <input
          type="url"
          placeholder="URL de la imagen"
          value={form.imagen}
          onChange={cambiar(setForm, 'imagen')}
        />
        <input
          type="number"
          min="1"
          placeholder="Costo"
          value={form.costo_puntos}
          onChange={cambiar(setForm, 'costo_puntos')}
        />
        <input
          type="number"
          min="0"
          placeholder="Stock"
          value={form.stock}
          onChange={cambiar(setForm, 'stock')}
        />
        <button>Crear</button>
      </form>
    </div>
  )
}
