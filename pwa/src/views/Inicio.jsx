import { useCallback, useEffect, useState } from 'react'
import QRCode from 'qrcode'
import { api } from '../api.js'

export default function Inicio({ cliente, refrescar }) {
  const [qr, setQr] = useState('')
  const [segundos, setSegundos] = useState(0)
  const [error, setError] = useState('')

  const generar = useCallback(async () => {
    try {
      const data = await api('/clientes/me/qr')
      setQr(await QRCode.toDataURL(data.payload, { width: 260, margin: 1, color: { dark: '#0e1b2a', light: '#ffffff' } }))
      setSegundos(data.expira_en_segundos)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    generar()
  }, [generar])

  useEffect(() => {
    if (segundos <= 0) return
    const t = setInterval(() => setSegundos((s) => s - 1), 1000)
    return () => clearInterval(t)
  }, [segundos])

  async function actualizar() {
    await refrescar()
    await generar()
  }

  return (
    <div className="inicio">
      <div className="saldo">
        <span className="saldo-v">{cliente?.puntos ?? 0}</span>
        <span className="saldo-t">puntos disponibles</span>
      </div>

      <div className="qr-card">
        <p className="qr-titulo">Muestra este codigo al despachador</p>
        {qr ? <img src={qr} alt="Codigo QR de fidelizacion" className="qr-img" /> : <div className="qr-vacio" />}
        <p className="qr-hint">
          {segundos > 0 ? `Se renueva en ${segundos}s` : 'Codigo vencido, actualiza'}
        </p>
      </div>

      {error && <p className="error">{error}</p>}

      <button className="primario" onClick={actualizar}>
        Actualizar codigo y saldo
      </button>
    </div>
  )
}
