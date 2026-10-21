import { useEffect, useState } from 'react'
import { api, fmtFecha } from '../api.js'

const VACIA = { nombre: '', puntos_por_litro: 1, activa: true, desde: '', hasta: '' }

function aLocal(iso) {
  if (!iso) return ''
  const normal = iso.endsWith('Z') || iso.includes('+') ? iso : `${iso.split('.')[0]}Z`
  const d = new Date(normal)
  if (Number.isNaN(d.getTime())) return ''
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}

function aUtc(valor) {
  if (!valor) return null
  const d = new Date(valor)
  if (Number.isNaN(d.getTime())) return null
  return d.toISOString().slice(0, 19)
}

function aFecha(valor) {
  return valor ? aUtc(valor).slice(0, 10) : null
}

export default function Reglas() {
  const [reglas, setReglas] = useState([])
  const [form, setForm] = useState(VACIA)
  const [editando, setEditando] = useState(null)
  const [edit, setEdit] = useState(null)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')

  function cargar() {
    api('/admin/reglas').then(setReglas).catch((e) => setError(e.message))
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
    setMensaje('')
    try {
      await api('/admin/reglas', {
        method: 'POST',
        body: {
          nombre: form.nombre,
          puntos_por_litro: Number(form.puntos_por_litro),
          activa: true,
          desde: aFecha(form.desde),
          hasta: aFecha(form.hasta),
        },
      })
      setForm(VACIA)
      setMensaje('Regla creada.')
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  async function alternar(r) {
    setError('')
    setMensaje('')
    try {
      await api(`/admin/reglas/${r.id}`, { method: 'PUT', body: { activa: !r.activa } })
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  function editar(r) {
    setError('')
    setMensaje('')
    setEditando(r.id)
    setEdit({
      nombre: r.nombre,
      puntos_por_litro: r.puntos_por_litro,
      activa: r.activa,
      desde: aLocal(r.desde),
      hasta: aLocal(r.hasta),
    })
  }

  function cancelar() {
    setEditando(null)
    setEdit(null)
  }

  async function guardar() {
    setError('')
    try {
      await api(`/admin/reglas/${editando}`, {
        method: 'PUT',
        body: {
          nombre: edit.nombre,
          puntos_por_litro: Number(edit.puntos_por_litro),
          activa: !!edit.activa,
          desde: aUtc(edit.desde),
          hasta: aUtc(edit.hasta),
        },
      })
      cancelar()
      setMensaje('Regla actualizada.')
      cargar()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <h2>Reglas de puntos</h2>
      <p className="muted">Los puntos se calculan por litro. Solo puede haber una regla activa a la vez.</p>
      {mensaje && <p className="ok">{mensaje}</p>}
      {error && <p className="error">{error}</p>}

      <table className="reglas-tabla">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Puntos / litro</th>
            <th>Desde</th>
            <th>Hasta</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {reglas.map((r) => {
            if (editando === r.id) {
              return (
                <tr key={r.id} className="fila-edicion">
                  <td colSpan={6} className="celda-edicion">
                    <div className="form-edicion">
                      <p className="form-edicion-titulo">Editando regla</p>

                      <label>
                        <span>Nombre</span>
                        <input value={edit.nombre} onChange={cambiar(setEdit, 'nombre')} required />
                      </label>

                      <label>
                        <span>Puntos / litro</span>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          value={edit.puntos_por_litro}
                          onChange={cambiar(setEdit, 'puntos_por_litro')}
                        />
                      </label>

                      <label>
                        <span>Desde</span>
                        <input
                          type="datetime-local"
                          value={edit.desde}
                          onChange={cambiar(setEdit, 'desde')}
                        />
                      </label>

                      <label>
                        <span>Hasta</span>
                        <input
                          type="datetime-local"
                          value={edit.hasta}
                          onChange={cambiar(setEdit, 'hasta')}
                        />
                      </label>

                      <label className="campo-check">
                        <span>Activa</span>
                        <input
                          type="checkbox"
                          checked={!!edit.activa}
                          onChange={(e) => setEdit({ ...edit, activa: e.target.checked })}
                        />
                      </label>

                      <div className="acciones">
                        <button onClick={guardar}>Guardar</button>
                        <button onClick={cancelar}>Cancelar</button>
                      </div>
                    </div>
                  </td>
                </tr>
              )
            }
            return (
              <tr key={r.id}>
                <td data-label="Nombre">{r.nombre}</td>
                <td data-label="Puntos / litro">{r.puntos_por_litro}</td>
                <td data-label="Desde">{r.desde ? fmtFecha(r.desde) : '-'}</td>
                <td data-label="Hasta">{r.hasta ? fmtFecha(r.hasta) : '-'}</td>
                <td data-label="Estado">{r.activa ? 'Activa' : 'Inactiva'}</td>
                <td className="celda-acciones" data-label="Acciones">
                  <div className="reglas-acciones">
                    <button onClick={() => editar(r)}>Editar</button>
                    <button
                      onClick={() => alternar(r)}
                      className={r.activa ? 'activada' : ''}
                    >
                      {r.activa ? 'Activada' : 'Activar'}
                    </button>
                  </div>
                </td>
              </tr>
            )
          })}
          {reglas.length === 0 && (
            <tr>
              <td colSpan="6" className="muted reglas-vacia">
                Aún no hay reglas
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <h3>Nueva regla</h3>
      <form className="fila" onSubmit={crear}>
        <input
          placeholder="Nombre"
          value={form.nombre}
          onChange={cambiar(setForm, 'nombre')}
          required
        />
        <input
          type="number"
          step="0.01"
          min="0"
          placeholder="Puntos / litro"
          value={form.puntos_por_litro}
          onChange={cambiar(setForm, 'puntos_por_litro')}
        />
        <input type="datetime-local" value={form.desde} onChange={cambiar(setForm, 'desde')} />
        <input type="datetime-local" value={form.hasta} onChange={cambiar(setForm, 'hasta')} />
        <button>Crear</button>
      </form>
    </div>
  )
}
