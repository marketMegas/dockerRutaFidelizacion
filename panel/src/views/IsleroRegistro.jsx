import { useCallback, useEffect, useState } from 'react'
import { api, fmtFecha } from '../api.js'

const PLACA_RE = /^[A-Z]{3}[0-9]{3}$/
const CEDULA_RE = /^[0-9]{6,10}$/
const TELEFONO_RE = /^[0-9]{10}$/

const PLACA_MSG = 'La placa debe tener 3 letras y 3 números (ej. ABC123)'
const CEDULA_MSG = 'La cédula debe tener solo números (6 a 10)'
const TELEFONO_MSG = 'El celular debe tener 10 dígitos'

function formatearPlaca(valor) {
  const limpio = valor.toUpperCase().replace(/[^A-Z0-9]/g, '')
  const letras = limpio.replace(/[0-9]/g, '').slice(0, 3)
  const numeros = limpio.replace(/[A-Z]/g, '').slice(0, 3)
  return letras + numeros
}

function formularioVacio() {
  return { placa: '', cedula: '', telefono: '', nombre: '' }
}

export default function IsleroRegistro() {
  const [form, setForm] = useState(formularioVacio())
  const [existente, setExistente] = useState(null)
  const [registros, setRegistros] = useState([])
  const [resultado, setResultado] = useState(null)
  const [aviso, setAviso] = useState('')
  const [error, setError] = useState('')
  const [consultando, setConsultando] = useState(false)
  const [guardando, setGuardando] = useState(false)

  const cargarRegistros = useCallback(async () => {
    try {
      setRegistros(await api('/islero/registros?limite=10'))
    } catch {
      setRegistros([])
    }
  }, [])

  useEffect(() => {
    cargarRegistros()
  }, [cargarRegistros])

  function campo(nombre, valor) {
    setForm((actual) => ({ ...actual, [nombre]: valor }))
  }

  function cambiarPlaca(valor) {
    setForm((actual) => ({ ...actual, placa: formatearPlaca(valor) }))
    setExistente(null)
    setResultado(null)
    setAviso('')
    setError('')
  }

  async function consultar() {
    if (!PLACA_RE.test(form.placa)) return
    setError('')
    setAviso('')
    setResultado(null)
    setConsultando(true)
    try {
      const data = await api(`/islero/clientes?placa=${encodeURIComponent(form.placa)}`)
      if (data.existe) {
        setExistente(data.cliente)
        setForm((actual) => ({
          ...actual,
          cedula: data.cliente.cedula || '',
          telefono: data.cliente.telefono || '',
          nombre: data.cliente.nombre || '',
        }))
        setAviso(
          data.cliente.activo
            ? 'Placa ya registrada. Puedes corregir la cédula o el celular del dueño.'
            : 'El cliente asociado está inactivo. Contacta al administrador.',
        )
      } else {
        setExistente(null)
        setForm((actual) => ({ ...actual, cedula: '', telefono: '', nombre: '' }))
        setAviso('Placa nueva: completa los datos del dueño del vehículo.')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setConsultando(false)
    }
  }

  async function guardar(e) {
    e.preventDefault()
    setError('')
    setResultado(null)

    if (!PLACA_RE.test(form.placa)) {
      setError(PLACA_MSG)
      return
    }
    if (!CEDULA_RE.test(form.cedula)) {
      setError(CEDULA_MSG)
      return
    }
    if (!TELEFONO_RE.test(form.telefono)) {
      setError(TELEFONO_MSG)
      return
    }
    setGuardando(true)
    try {
      let actual = existente
      if (!actual) {
        const consulta = await api(`/islero/clientes?placa=${encodeURIComponent(form.placa)}`)
        actual = consulta.existe ? consulta.cliente : null
        if (actual) setExistente(actual)
      }
      if (actual) {
        if (!actual.activo) {
          setError('El cliente asociado a esta placa está inactivo. Contacta al administrador.')
          return
        }
        const dueno = actual.nombre ? ` a nombre de ${actual.nombre}` : ''
        if (
          !window.confirm(
            `La placa ${form.placa} ya está registrada${dueno}. ¿Actualizar cédula/celular con los datos ingresados?`,
          )
        ) {
          return
        }
      }

      const data = await api('/islero/clientes', { method: 'POST', body: form })
      setResultado(data)
      setForm(formularioVacio())
      setExistente(null)
      setAviso('')
      await cargarRegistros()
    } catch (err) {
      setError(err.message)
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div>
      <h2>Registrar cliente</h2>
      <p className="muted">
        Captura la placa, cédula y celular del dueño. Los puntos se acreditan cuando Zencillo reporta la venta de esa
        placa.
      </p>

      <form className="islero-form" onSubmit={guardar}>
        <div className="campo-placa">
          <label>
            Placa del vehículo
            <input
              placeholder="ABC123"
              autoComplete="off"
              autoCapitalize="characters"
              spellCheck={false}
              maxLength={6}
              value={form.placa}
              onChange={(e) => cambiarPlaca(e.target.value)}
              required
            />
          </label>
          <button
            type="button"
            onClick={consultar}
            disabled={!PLACA_RE.test(form.placa) || consultando}
          >
            {consultando ? 'Consultando...' : 'Consultar'}
          </button>
        </div>

        {aviso && <p className={existente && !existente.activo ? 'error' : 'ok'}>{aviso}</p>}

        <label>
          Cédula del dueño
          <input
            inputMode="numeric"
            placeholder="1098765432"
            value={form.cedula}
            onChange={(e) => campo('cedula', e.target.value.replace(/[^0-9]/g, '').slice(0, 10))}
            required
          />
        </label>
        <label>
          Celular del dueño
          <input
            inputMode="tel"
            placeholder="3001234567"
            value={form.telefono}
            onChange={(e) => campo('telefono', e.target.value.replace(/[^0-9]/g, '').slice(0, 10))}
            required
          />
        </label>
        <label>
          Nombre del dueño (opcional)
          <input
            placeholder="Juan Pérez"
            maxLength={120}
            value={form.nombre}
            onChange={(e) => campo('nombre', e.target.value)}
          />
        </label>

        {error && <p className="error">{error}</p>}

        <div className="acciones">
          <button disabled={guardando}>{guardando ? 'Guardando...' : existente ? 'Actualizar datos' : 'Registrar cliente'}</button>
        </div>
      </form>

      {resultado && (
        <div className="panel-detalle">
          <h3>{resultado.creado ? 'Cliente registrado' : 'Datos actualizados'}</h3>
          <p className="ok">
            {resultado.placa} · C.C. {resultado.cedula} · {resultado.telefono}
            {resultado.nombre ? ` · ${resultado.nombre}` : ''}
          </p>
          <p className="muted">Placas activas: {(resultado.placas || []).join(', ')}</p>
        </div>
      )}

      <h3>Mis últimos registros</h3>
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Placa</th>
            <th>Acción</th>
            <th>Cédula</th>
            <th>Celular</th>
          </tr>
        </thead>
        <tbody>
          {registros.map((r) => (
            <tr key={r.id}>
              <td data-label="Fecha">{fmtFecha(r.created_at)}</td>
              <td data-label="Placa">{r.placa}</td>
              <td data-label="Acción">{r.accion === 'crear' ? 'Registro' : 'Actualización'}</td>
              <td data-label="Cédula">{r.detalle?.despues?.cedula || '-'}</td>
              <td data-label="Celular">{r.detalle?.despues?.telefono || '-'}</td>
            </tr>
          ))}
          {registros.length === 0 && (
            <tr>
              <td colSpan="5" className="muted">
                Aún no hay registros.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
