"""Preguntas frecuentes compartidas por las reglas y el contexto del LLM."""

FAQ = [
    (
        "Cómo entro si ya estoy registrado?",
        "Escribe la placa de tu vehículo y te enviaremos un código de 6 dígitos al celular registrado.",
    ),
    (
        "No me llega el código",
        "Espera un momento y pide uno nuevo. Verifica que el celular sea el número con el que te registraste.",
    ),
    (
        "Qué es el nivel y cómo funciona?",
        "Es el multiplicador de puntos según los litros que cargas en el mes. Se calcula con los litros "
        "del mes en curso y del mes anterior, y cuenta el mayor de los dos.",
    ),
    (
        "Por qué bajó mi nivel?",
        "El nivel se recalcula cada mes con los litros cargados. Si no alcanzas el mínimo del nivel, "
        "vuelves al nivel que corresponde a tu consumo.",
    ),
    (
        "Cómo canjeo una recompensa?",
        "En Recompensas elige un premio que alcance con tus puntos y toca Canjear. El código queda "
        "guardado en Recompensas, en Mis códigos.",
    ),
    (
        "Dónde veo mi código?",
        "En Recompensas, sección Mis códigos. Puedes copiarlo o compartirlo cuando quieras.",
    ),
    (
        "Cambié de vehículo o de placa",
        "Ingresa con la nueva placa y registra tu mismo celular para conservar tus puntos en la misma cuenta.",
    ),
    (
        "No veo mis puntos",
        "Puede tardar unos segundos después de cada carga. En Inicio usa Actualizar saldo para consultarlos de nuevo.",
    ),
]

FAQ_TEXTO = [{"pregunta": pregunta, "respuesta": respuesta} for pregunta, respuesta in FAQ]
