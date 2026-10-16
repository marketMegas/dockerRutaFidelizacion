# Sistema de interfaz — Fidelizacion GLP

## Direccion

Programa de puntos de una estacion de GLP en Colombia. La PWA la usa el cliente de pie
junto al carro o el surtidor, con el celular, medio minuto. Debe leerse como el tablero
de una bomba: jerarquia inmediata, cero ornamento.

Sensacion: **clara como un tablero de surtidor**, no "app de banco".

## Vocabulario del dominio

Surtidor, manguera y pico de carga, tanque y medidor de nivel, cilindro 17.5 kg,
regulador, llama piloto, factura de tanqueo, cartilla de sellos, "tanquear", litros vs pesos.

**1 punto = 1 litro** (mientras la regla vigente este a 1.00 pt/L). El costo de cada
recompensa se lee tambien en litros equivalentes, leido de `GET /fid-api/config`.

## Firma

**Medidor de nivel de tanque.** El avance hacia cada recompensa se dibuja como una barra
segmentada de nivel de combustible (puntos actuales / costo). Completan la firma:

1. `.medidor` — pista segmentada en 10 tramos (surtidor).
2. `.nivel` — relleno naranja, ancho = avance.
3. `.premio-estado` — "Te faltan N pts" / "Listo para canjear".
4. `.premio-costo` — numeral en Space Grotesk tabular, como lectura de odometro.
5. `.premio-litros` — "Equivale a N L de GLP" (solo en el login, sin saldo).
6. `.premio-media` — miniatura de referencia a la izquierda de cada tarjeta (imagen
   `recompensa.imagen`); si no hay imagen, un bloque de rayas diagonales en
   `--surface-track`. Nunca dejar el hueco vacio.

## Profundidad

**Un solo enfoque: sombras suaves.** Las tarjetas usan `--depth-card`; el borde es un
hairline tenue (`--line-card`), nunca la fuente de jerarquia. No mezclar con cambios de
color de superficie para dar elevacion.

## Proporcion y tamano

Las recompensas se disponen como **tarjetas tipo tarjeta de credito**: rejilla de
**2 columnas**, `aspect-ratio: 1.586 / 1` (85.6 x 53.98 mm), `min-height: 140px`
(112px en la variante sobre verde, que lleva menos contenido). El `min-height` evita que
el contenido se recorte en telefonos angostos, donde la razon no se puede respetar.

- `.premios` — `display: grid; grid-template-columns: repeat(2, minmax(0, 1fr))`.
- `.premio-card` — `flex-direction: row`, `padding: var(--space-3)`, `gap: var(--space-3)`,
  `overflow: hidden`.
- `.premio-media` — `flex: 0 0 32%`, `min-width: 54px`, `max-width: 96px`, radio 10px,
  `overflow: hidden`; la imagen es `object-fit: cover` a todo el alto de la tarjeta.
- `.premio-cuerpo` — columna flexible con el texto: nombre a 2 lineas
  (`-webkit-line-clamp: 2`), descripcion a 1 linea, medidor de 8px anclado abajo con
  `margin-top: auto`, pie con estado + boton.
- Contenido compacto para que quepa en la columna derecha (aprox. 130px con dos columnas).
- `.premio-card--verde` — sobre el degradado del login: superficie translucida
  `rgba(255,255,255,.12)` + `backdrop-filter: blur(8px)`; el media pasa a
  `rgba(255,255,255,.2)`. Nunca tarjeta blanca pura sobre fondo de color.

## Espaciado

Base **0.25rem**. Escala `--space-1` (0.25) a `--space-5` (1.5). Radios: 8px controles
pequenos, 10px controles, 16px tarjetas.

## Tipografia

- IBM Plex Sans — cuerpo, labels, descripciones.
- Space Grotesk — titulos y **todos los numeros** (costo, saldo, deltas), siempre con
  `font-variant-numeric: tabular-nums`.

## Color

- Verde institucional `--green #5fbd44` (marca, cabecera, tanques).
- Naranja `--orange #f68811` (llama). Reservado a accion y al nivel del medidor.
- Texto `--text #17331c`; secundario `--muted #6d8a72`.
- El color significa; no se usa para decorar.

## Componentes clave

- `pwa/src/components/RecompensaCard.jsx` — tarjeta de recompensa. Props: `recompensa`,
  `puntos`, `tasa` (puntos por litro), `onCanjear`, `mostrarProgreso`, `sobreVerde`.
  Lee `recompensa.imagen`; si la URL falla (`onError`) vuelve al bloque de rayas.
  Se usa en `views/Canjes.jsx` (con progreso y boton) y en `views/Login.jsx`
  (sin progreso, sobre verde).
- Estados obligatorios: cargando (`.esqueleto` con `.premio-media` + `.premio-cuerpo`,
  pulso 1.4s), vacio (`.vacio`), agotado (`--agotado`), boton `disabled` cuando no
  alcanza o stock 0.
- `panel/src/views/Recompensas.jsx` — tabla con miniatura 44x44, creacion e edicion
  inline. La columna `imagen` es una URL publica que se pega en el panel; el backend no
  almacena archivos.

## Tokens (pwa/src/styles.css)

```
--space-1..5      escala de espaciado (base 0.25rem)
--surface-card    superficie de tarjeta
--surface-track   pista del medidor, esqueletos, controles deshabilitados
--line-card       hairline de tarjeta
--depth-card      sombra de tarjeta
```

## Verificacion

`ruff check .` + `pytest` en `api/`; `docker compose up -d --build api panel pwa` (la
migracion nueva se aplica sola al reiniciar el api); `.\dev.ps1 health` (5x200);
`.\dev.ps1 e2e`. Verificar clases nuevas en el bundle servido en `http://127.0.0.1:5140/`.
