const PREGUNTAS = [
  {
    q: 'Cómo entro si ya estoy registrado?',
    a: 'Escribe la placa de tu vehículo (3 letras y 3 números, ej. ABC123) y te enviaremos un código de 6 dígitos al celular registrado.',
  },
  {
    q: 'No me llega el código',
    a: 'Espera un momento y pide uno nuevo. Verifica que el celular sea el número con el cual te registraste y sea el correcto.',
  },
  {
    q: 'Cambié de vehículo o de placa',
    a: 'Ingresa con la nueva placa y registra tu mismo celular para conservar tus puntos en la misma cuenta.',
  },
  {
    q: 'No veo mis puntos',
    a: 'Puede tardar unos segundos después de cada carga. En Inicio usa Actualizar saldo para consultarlos de nuevo.',
  },
  {
    q: 'Cómo canjeo una recompensa?',
    a: 'En Recompensas elige una disponible con tus puntos, toca Canjear y presenta tu cédula para reclamarla.',
  },
  {
    q: 'Puedo usar la app sin internet?',
    a: 'La app instalada abre sin conexión, pero para iniciar sesión y ver tu saldo necesitas internet.',
  },
]

export default function Ayuda() {
  return (
    <div>
      <h2>Ayuda</h2>
      <p className="muted">Respuestas rápidas a las dudas más comunes del programa.</p>

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
            <strong>Atención en la estación</strong>
            <span className="muted">Consulta al personal de la estación de servicio.</span>
          </div>
        </li>
        <li>
          <div className="lista-info">
            <strong>Soporte del programa</strong>
            <span className="muted">Informa tu cédula o placa para revisar tu cuenta más rápido.</span>
          </div>
        </li>
      </ul>
    </div>
  )
}
