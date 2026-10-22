import { useEffect, useState } from 'react'
import {
  cargarCatalogo,
  claveDesdeNombre,
  codigosDesdeTexto,
  generarCodigos,
  guardarCatalogo,
  normalizarCodigo,
  textoDesdeCodigos,
} from '../catalogo.js'

const VACIA = { nombre: '', descripcion: '', imagen: '', costo_puntos: 100 }

export default function Catalogo() {
  const [datos, setDatos] = useState(null)
  const [form, setForm] = useState(VACIA)
  const [editando, setEditando] = useState(null)
  const [edit, setEdit] = useState(null)
  const [codigosDe, setCodigosDe] = useState(null)
  const [codigosTexto, setCodigosTexto] = useState('')
  const [generarCantidad, setGenerarCantidad] = useState(100)
  const [error, setError] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [guardando, setGuardando] = useState(false)

  function cargar() {
    return cargarCatalogo()
      .then(setDatos)
      .catch((e) => setError(e.message))
  }

  useEffect(() => {
    cargar()
  }, [])

  function cambiar(setter, campo) {
    return (e) => setter((prev) => ({ ...prev, [campo]: e.target.value }))
  }

  async function guardar(actualizado, aviso) {
    setError('')
    setMensaje('')
    setGuardando(true)
    try {
      await guardarCatalogo(actualizado)
      setDatos(await cargarCatalogo())
      setMensaje(aviso)
      return true
    } catch (err) {
      setError(err.message)
      return false
    } finally {
      setGuardando(false)
    }
  }

  function editar(p) {
    setError('')
    setMensaje('')
    setCodigosDe(null)
    setEditando(p.clave)
    setEdit({
      nombre: p.nombre,
      descripcion: p.descripcion || '',
      imagen: p.imagen || '',
      costo_puntos: p.costo_puntos,
    })
  }

  function cancelar() {
    setEditando(null)
    setEdit(null)
  }

  async function guardarPremio() {
    const premios = datos.premios.map((p) =>
      p.clave === editando ? { ...p, ...edit, costo_puntos: Number(edit.costo_puntos) } : p,
    )
    if (await guardar({ ...datos, premios }, 'Premio actualizado.')) cancelar()
  }

  async function alternar(p) {
    const premios = datos.premios.map((x) =>
      x.clave === p.clave ? { ...x, activo: !x.activo } : x,
    )
    await guardar({ ...datos, premios }, p.activo ? 'Premio desactivado.' : 'Premio activado.')
  }

  async function crear(e) {
    e.preventDefault()
    const clave = claveDesdeNombre(form.nombre, new Set(datos.premios.map((p) => p.clave)))
    const premios = [
      ...datos.premios,
      {
        clave,
        nombre: form.nombre.trim(),
        descripcion: form.descripcion.trim(),
        imagen: form.imagen.trim(),
        costo_puntos: Number(form.costo_puntos),
        activo: true,
        codigos: [],
      },
    ]
    setError('')
    setMensaje('')
    setGuardando(true)
    try {
      await guardarCatalogo({ ...datos, premios })
      const frescos = await cargarCatalogo()
      setDatos(frescos)
      setForm(VACIA)
      setMensaje('Premio creado. Agrega códigos para que se pueda canjear.')
      abrirCodigos(frescos.premios.find((p) => p.clave === clave))
    } catch (err) {
      setError(err.message)
    } finally {
      setGuardando(false)
    }
  }

  function abrirCodigos(p) {
    if (!p) return
    setError('')
    setMensaje('')
    setEditando(null)
    setEdit(null)
    setCodigosDe(p.clave)
    setCodigosTexto(textoDesdeCodigos(p.codigos))
  }

  const premioCodigos = datos?.premios.find((p) => p.clave === codigosDe) || null
  const sinGuardar = premioCodigos
    ? codigosTexto !== textoDesdeCodigos(premioCodigos.codigos)
    : false

  async function guardarCodigos() {
    setError('')
    setMensaje('')
    const invalidos = []
    const normalizados = []
    for (const linea of codigosDesdeTexto(codigosTexto)) {
      const codigo = normalizarCodigo(linea)
      if (codigo) normalizados.push(codigo)
      else invalidos.push(linea)
    }
    if (invalidos.length > 0) {
      setError(`Códigos inválidos (8 caracteres, sin 0 ni 1): ${invalidos.slice(0, 6).join(', ')}`)
      return
    }
    if (new Set(normalizados).size !== normalizados.length) {
      setError('Hay códigos repetidos en este premio.')
      return
    }
    const otros = datos.premios.filter((p) => p.clave !== codigosDe).flatMap((p) => p.codigos)
    const choque = normalizados.find((c) => otros.includes(c))
    if (choque) {
      setError(`El código ${choque} ya está en otro premio.`)
      return
    }
    const premios = datos.premios.map((p) =>
      p.clave === codigosDe ? { ...p, codigos: normalizados } : p,
    )
    if (await guardar({ ...datos, premios }, `Códigos guardados (${normalizados.length}).`)) {
      setCodigosTexto(textoDesdeCodigos(normalizados))
    }
  }

  async function generar() {
    setError('')
    setMensaje('')
    setGuardando(true)
    try {
      const res = await generarCodigos(codigosDe, generarCantidad)
      const frescos = await cargarCatalogo()
      setDatos(frescos)
      const premio = frescos.premios.find((p) => p.clave === codigosDe)
      setCodigosTexto(textoDesdeCodigos(premio.codigos))
      setMensaje(`Se generaron ${res.codigos.length} códigos.`)
    } catch (err) {
      setError(err.message)
    } finally {
      setGuardando(false)
    }
  }

  if (!datos) return <p className="muted">{error || 'Cargando...'}</p>

  const totalCodigos = datos.premios.reduce((s, p) => s + p.codigos.length, 0)
  const totalDisponibles = datos.premios.reduce((s, p) => s + p.codigos_disponibles, 0)

  return (
    <div>
      <h2>Catálogo</h2>
      <p className="muted">
        El catálogo vive en un archivo del servidor (versión {datos.version}).{' '}
        {totalDisponibles.toLocaleString('es-CO')} códigos disponibles de{' '}
        {totalCodigos.toLocaleString('es-CO')}. Los niveles se editan en la pestaña Niveles.
      </p>
      {mensaje && <p className="ok">{mensaje}</p>}
      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Imagen</th>
            <th>Premio</th>
            <th>Descripción</th>
            <th>Costo (pts)</th>
            <th>Códigos</th>
            <th>Estado</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {datos.premios.map((p) => {
            if (editando === p.clave) {
              return (
                <tr key={p.clave} className="fila-edicion">
                  <td colSpan={7} className="celda-edicion">
                    <div className="form-edicion">
                      <p className="form-edicion-titulo">Editando {p.nombre}</p>

                      <label className="campo-imagen">
                        <span>Imagen (URL)</span>
                        <div className="campo-imagen-fila">
                          {edit.imagen ? (
                            <img
                              className="miniatura-edicion"
                              src={edit.imagen}
                              alt=""
                              onError={(e) => {
                                e.currentTarget.style.visibility = 'hidden'
                              }}
                            />
                          ) : null}
                          <input
                            type="url"
                            placeholder="https://..."
                            value={edit.imagen}
                            onChange={cambiar(setEdit, 'imagen')}
                          />
                        </div>
                      </label>

                      <label>
                        <span>Nombre</span>
                        <input value={edit.nombre} onChange={cambiar(setEdit, 'nombre')} required />
                      </label>

                      <label>
                        <span>Descripción</span>
                        <input
                          value={edit.descripcion}
                          onChange={cambiar(setEdit, 'descripcion')}
                        />
                      </label>

                      <label>
                        <span>Costo (pts)</span>
                        <input
                          type="number"
                          min="1"
                          value={edit.costo_puntos}
                          onChange={cambiar(setEdit, 'costo_puntos')}
                        />
                      </label>

                      <div className="acciones">
                        <button onClick={guardarPremio} disabled={guardando}>
                          Guardar
                        </button>
                        <button onClick={cancelar}>Cancelar</button>
                      </div>
                    </div>
                  </td>
                </tr>
              )
            }

            if (codigosDe === p.clave) {
              return (
                <tr key={p.clave} className="fila-edicion">
                  <td colSpan={7} className="celda-edicion">
                    <div className="form-edicion">
                      <p className="form-edicion-titulo">Códigos de {p.nombre}</p>

                      <div className="campo-codigos">
                        <div className="contador-codigos">
                          <span>
                            <strong>{p.codigos_disponibles}</strong> disponibles ·{' '}
                            <strong>{p.codigos_entregados}</strong> entregados ·{' '}
                            {p.codigos.length} en total
                          </span>
                          <span>No quites códigos ya entregados: el cliente los conserva.</span>
                        </div>
                        <textarea
                          className="area-codigos"
                          value={codigosTexto}
                          onChange={(e) => setCodigosTexto(e.target.value)}
                          spellCheck={false}
                          aria-label={`Códigos de ${p.nombre}`}
                        />
                        <div className="fila-codigos">
                          <span className="campo-generar">
                            <label>
                              <span>Cantidad</span>
                              <input
                                type="number"
                                min="1"
                                value={generarCantidad}
                                onChange={(e) => setGenerarCantidad(e.target.value)}
                              />
                            </label>
                            <button type="button" onClick={generar} disabled={guardando || sinGuardar}>
                              Generar códigos
                            </button>
                          </span>
                          {sinGuardar && (
                            <span className="sin-guardar">Guarda los cambios antes de generar.</span>
                          )}
                        </div>
                      </div>

                      <div className="acciones">
                        <button onClick={guardarCodigos} disabled={guardando}>
                          Guardar códigos
                        </button>
                        <button onClick={() => setCodigosDe(null)}>Cerrar</button>
                      </div>
                    </div>
                  </td>
                </tr>
              )
            }

            return (
              <tr key={p.clave}>
                <td className="celda-imagen" data-label="Imagen">
                  {p.imagen ? (
                    <img className="miniatura" src={p.imagen} alt="" />
                  ) : (
                    <span className="miniatura miniatura-vacia" />
                  )}
                </td>
                <td data-label="Premio">{p.nombre}</td>
                <td data-label="Descripción">{p.descripcion || '-'}</td>
                <td data-label="Costo (pts)">{p.costo_puntos}</td>
                <td data-label="Códigos">
                  {p.codigos_disponibles} / {p.codigos.length}
                  {p.codigos_entregados > 0 && (
                    <span className="muted"> ({p.codigos_entregados} entregados)</span>
                  )}
                </td>
                <td data-label="Estado">{p.activo ? 'Activo' : 'Inactivo'}</td>
                <td className="celda-acciones">
                  <div className="reglas-acciones">
                    <button onClick={() => editar(p)}>Editar</button>
                    <button onClick={() => abrirCodigos(p)}>Códigos</button>
                    <button onClick={() => alternar(p)}>{p.activo ? 'Desactivar' : 'Activar'}</button>
                  </div>
                </td>
              </tr>
            )
          })}
          {datos.premios.length === 0 && (
            <tr>
              <td colSpan="7" className="muted">
                Aún no hay premios en el catálogo
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <h3>Nuevo premio</h3>
      <form className="fila" onSubmit={crear}>
        <input
          placeholder="Nombre"
          value={form.nombre}
          onChange={cambiar(setForm, 'nombre')}
          required
        />
        <input
          placeholder="Descripción"
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
          required
        />
        <button disabled={guardando}>Crear premio</button>
      </form>
    </div>
  )
}
