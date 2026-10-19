const PREGUNTAS = [
  {
    q: 'Como entro si ya estoy registrado?',
    a: 'Escribe la placa de tu vehiculo (3 letras y 3 numeros, ej. ABC123) y te enviaremos un codigo de 6 digitos al celular registrado.',
  },
  {
    q: 'No me llega el codigo',
    a: 'Espera un momento y pide uno nuevo. Verifica que el celular sea correcto; si cambiaste de numero, registra la placa con tu nuevo celular.',
  },
  {
    q: 'Cambie de vehiculo o de placa',
    a: 'Ingresa con la nueva placa y registra tu mismo celular para conservar tus puntos en la misma cuenta.',
  },
  {
    q: 'No veo mis puntos',
    a: 'Puede tardar unos segundos despues de cada carga. En Inicio usa Actualizar saldo para consultarlos de nuevo.',
  },
  {
    q: 'Como canjeo una recompensa?',
    a: 'En Recompensas elige una disponible con tus puntos, toca Canjear y presenta tu cedula para reclamarla.',
  },
  {
    q: 'Puedo usar la app sin internet?',
    a: 'La app instalada abre sin conexion, pero para iniciar sesion y ver tu saldo necesitas internet.',
  },
]

export default function Ayuda() {
  return (
    <div>
      <h2>Ayuda</h2>
      <p className="muted">Respuestas rapidas a las dudas mas comunes del programa.</p>

      <dl className="faq">
        {PREGUNTAS.map((p) => (
          <div key={p.q} className="faq-item">
            <dt>{p.q}</dt>
            <dd>{p.a}</dd>
          </div>
        ))}
      </dl>

      <h2>Contacto</h2>
      <ul className="lista">
        <li>
          <div className="lista-info">
            <strong>Atencion en la estacion</strong>
            <span className="muted">Consulta al personal de la estacion de servicio.</span>
          </div>
        </li>
        <li>
          <div className="lista-info">
            <strong>Soporte del programa</strong>
            <span className="muted">Informa tu cedula o placa para revisar tu cuenta mas rapido.</span>
          </div>
        </li>
      </ul>
    </div>
  )
}
