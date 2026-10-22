import { useEffect, useState } from 'react'
import { cargarCatalogo, guardarCatalogo } from '../catalogo.js'

function fmtNum(valor) {
  return (Number(valor) || 0).toLocaleString('es-CO', { maximumFractionDigits: 2 })
}

export default function Niveles() {
  const [datos, setDatos] = useState(null)
  const [editando, setEditando] = useState(null)
  const [edit, setEdit] = useState(null)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')

  function cargar() {
    return cargarCatalogo()
      .then(setDatos)
      .catch((e) => setError(e.message))
  }

  useEffect(() => {
    cargar()
  }, [])

  function cambiar(campo) {
    return (e) => setEdit((prev) => ({ ...prev, [campo]: e.target.value }))
  }

  function cancelar() {
    setEditando(null)
    setEdit(null)
  }

  async function guardar() {
    const niveles = datos.niveles.map((n) =>
      n.clave === editando
        ? {
            ...n,
            nombre: edit.nombre,
            minimo: Number(edit.minimo),
            multiplicador: Number(edit.multiplicador),
            descripcion: edit.descripcion,
          }
        : n,
    )
    setError('')
    setMensaje('')
    try {
      await guardarCatalogo({ ...datos, niveles })
      await cargar()
      cancelar()
      setMensaje('Nivel actualizado.')
    } catch (err) {
      setError(err.message)
    }
  }

  if (!datos) return <p className="muted">{error || 'Cargando...'}</p>

  return (
    <div>
      <h2>Niveles</h2>
      <p className="muted">
        El nivel se calcula con los litros del mes en curso y del mes anterior: cuenta el mayor.
        Al cruzar un umbral, los siguientes litros suman con el multiplicador nuevo.
      </p>
      {mensaje && <p className="ok">{mensaje}</p>}
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Nivel</th>
            <th>Litros en el mes</th>
            <th>Multiplicador</th>
            <th>Descripción</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {datos.niveles.map((n) => {
            if (editando === n.clave) {
              return (
                <tr key={n.clave} className="fila-edicion">
                  <td colSpan={5} className="celda-edicion">
                    <div className="form-edicion">
                      <p className="form-edicion-titulo">Editando {n.nombre}</p>

                      <label>
                        <span>Nombre</span>
                        <input value={edit.nombre} onChange={cambiar('nombre')} required />
                      </label>

                      <label>
                        <span>Litros en el mes</span>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={edit.minimo}
                          onChange={cambiar('minimo')}
                        />
                      </label>

                      <label>
                        <span>Multiplicador</span>
                        <input
                          type="number"
                          min="0.01"
                          step="0.01"
                          value={edit.multiplicador}
                          onChange={cambiar('multiplicador')}
                        />
                      </label>

                      <label>
                        <span>Descripción</span>
                        <input value={edit.descripcion} onChange={cambiar('descripcion')} />
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
              <tr key={n.clave}>
                <td data-label="Nivel">{n.nombre}</td>
                <td data-label="Litros en el mes">{fmtNum(n.minimo)} L</td>
                <td data-label="Multiplicador">×{fmtNum(n.multiplicador)}</td>
                <td data-label="Descripción">{n.descripcion || '-'}</td>
                <td className="celda-acciones">
                  <button
                    onClick={() => {
                      setError('')
                      setMensaje('')
                      setEditando(n.clave)
                      setEdit({
                        nombre: n.nombre,
                        minimo: n.minimo,
                        multiplicador: n.multiplicador,
                        descripcion: n.descripcion || '',
                      })
                    }}
                  >
                    Editar
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
