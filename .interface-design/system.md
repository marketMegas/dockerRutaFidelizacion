# Sistema de interfaz — Fidelizacion GLP

## Direccion

Programa de puntos de una estacion de GLP en Colombia. La PWA la usa el cliente de pie
junto al carro o el surtidor, con el celular, medio minuto. Debe leerse como el tablero
de una bomba: jerarquia inmediata, cero ornamento.

Nombre del programa: **Programa: Fidelización puntos g-max**. Esta cadena vive en cuatro
sitios que hay que cambiar juntos: `<title>` y `theme-color` de `pwa/index.html`,
`name`/`short_name`/`theme_color`/`background_color` de `pwa/public/manifest.webmanifest`,
el `h1` del hero de `views/Login.jsx` (con "Programa:" como eyebrow en
`.login-hero-label`) y `.navbar-marca` de `components/Navbar.jsx`. En el hero y en la barra
de navegacion se muestra sin el prefijo "Programa:" porque ahi ya esta la etiqueta.

Sensacion: **clara como un tablero de surtidor**, con la lectura de benefits de un
programa de fidelizacion de combustible (balance como tarjeta de socio, catalogo de
recompensas, extracto de movimientos).

## Vocabulario del dominio

Surtidor, manguera y pico de carga, tanque y medidor de nivel, cilindro 17.5 kg,
regulador, llama piloto, factura de tanqueo, cartilla de sellos, "tanquear", litros vs pesos.

**1 punto = 1 litro** (mientras la regla vigente este a 1.00 pt/L). El costo de cada
recompensa se lee tambien en litros equivalentes, leido de `GET /fid-api/config`.

## Firma

**Medidor de nivel de tanque.** El avance hacia cada recompensa se dibuja como una barra
segmentada de nivel de combustible (puntos actuales / costo). Completan la firma:

1. `.medidor` — pista segmentada en 10 tramos (surtidor), 9px, con sombra interior.
2. `.nivel` — relleno naranja (la llama), ancho = avance.
3. `.premio-estado` — "Te faltan N pts" / "Listo para canjear" (este ultimo en pastilla verde).
4. `.premio-costo` — numeral en Barlow Condensed tabular, como lectura de odometro, con la
   unidad en la pildora verde `.premio-costo-u` (`--verde-hondo` con `--verde-claro`).
5. `.premio-litros` — "Equivale a N L de GLP" (solo en el login, sin saldo).
6. `.premio-media` — miniatura de referencia a la izquierda de cada tarjeta (imagen
   `recompensa.imagen`); si no hay imagen, un bloque de rayas diagonales en
   `--surface-track`. Nunca dejar el hueco vacio.
7. `.placa-chip` — la placa del cliente escrita sobre amarillo placa, en la cabecera.

## Profundidad

**Un solo enfoque: sombras suaves.** Las tarjetas usan `--sombra-card`; el borde es un
hairline tenue (`--linea`), nunca la fuente de jerarquia. No mezclar con cambios de
color de superficie para dar elevacion. La elevacion fuerte queda reservada a la barra de
tabs (`--sombra-nav`); el formulario del login paso a `--sombra-card` cuando el inicio
quedo sobre body blanco.

## Proporcion y tamano

El catalogo de recompensas es de **una columna**. A dos columnas el pie de tarjeta no da
para el estado y el boton juntos: en un contenedor de 520px cada tarjeta queda en ~205px
y el texto se recorta. La razon 1.586/1 de tarjeta de credito se retiro del contenedor:
`.premio-card` toma su alto del contenido (`min-height: 124px`) y `.premio-media` se
estira a ese alto.

- `.premios` — `display: grid; grid-template-columns: minmax(0, 1fr)`.
- `.premio-card` — `flex-direction: row`, `padding: var(--space-3)`, `gap: var(--space-3)`,
  `min-height: 124px`, `overflow: hidden`.
- `.premio-media` — `flex: 0 0 32%`, `min-width: 54px`, `max-width: 128px`, radio 10px,
  `overflow: hidden`; la imagen es `object-fit: cover` a todo el alto de la tarjeta.
- `.premio-cuerpo` — columna flexible con el texto: nombre a 2 lineas
  (`-webkit-line-clamp: 2`), descripcion a 1 linea, medidor de 9px anclado abajo con
  `margin-top: auto`, pie con estado + boton.
- `.premio-card--verde` — las tarjetas de muestra del inicio, sobre body blanco: panel
  `--verde-claro` con hairline `#b6e3c2` y `--sombra-card`, tinta normal. El nombre
  "verde" es historico (vino de cuando iban sobre superficie oscura); hoy es literal: es
  el unico verde de superficie que queda en la PWA.

## Espaciado

Base **0.25rem**. Escala `--space-1` (0.25) a `--space-5` (1.5). Radios: `--radius-ctrl`
10px controles, `--radius-card` 16px tarjetas, `--radius-panel` 20px superficies de
peso (tarjeta de socio, formulario). Pastillas y estados: 999px.

## Tipografia

- Barlow — cuerpo, labels, titulos de tarjeta.
- Barlow Condensed (`--display`) — titulos de seccion y **todos los numeros** (costo,
  saldo, deltas, placa), siempre con `font-variant-numeric: tabular-nums`.
- Se cargan por `@import` de Google Fonts. Sin red caen a Arial Narrow / system-ui: la
  PWA debe seguir leyendose bien, pero el odometro pierde caracter. Revisar antes de
  publicar si conviene autohospedarlas.

## Color

Los valores de `--verde`, `--placa`, `--naranja` y sus variantes hondas estan
**bloqueados por el dueno del producto**. Lo que cambio fue a que superficie va cada uno.

- Naranja marca `--marca #ff9842` — **superficies de marca**: barra de navegacion, cabecera,
  tarjeta de socio, pestana activa del menu inferior. Reemplazo del verde oscuro por
  decision del dueno. El inicio/login **ya no es superficie de marca**: su cuerpo es blanco
  y la marca queda solo en la barra de arriba.
- Fondo del body **blanco** (`--fondo #ffffff`, pedido por el dueno junto con la barra
  naranja). Con el fondo blanco el hairline `--linea` dejo de alcanzar para separar: las
  filas `.lista li` llevan ahora `--sombra-card` y la `.badge` neutra usa
  `--surface-track` en vez de `--fondo`. No quitar esas dos piezas "porque el borde ya
  basta": sobre blanco vuelven a fundirse.
- Sobre `--marca` la tinta es oscura (`--tinta-sobre-marca #2b1204`), **nunca blanca ni
  amarilla**: blanco 2.60:1 y amarillo placa 1.79:1 sobre #ff9842, ambos fuera de WCAG;
  el dark ink rinde 6.78:1 en el centro del degradado.
- Verde marca `--verde #5fbd44` y `--verde-2` — acento: foco, franja tricolor de los tabs.
- Verde hondo `--verde-hondo #1b4d24` — **solo texto sobre superficie clara**: `.pos`,
  `.premio-estado.listo`, badges `entregado`/`canjeado`, `.ok`, hover de tabs. No vuelve a
  aparecer como fondo.
- Amarillo placa `--placa #f6d51e` sobre `--placa-tinta` — **solo la placa del vehiculo y
  los acentos de marca**: `.placa-chip`, la cornisa del formulario, las franjas de
  `.navbar::after` y `.tabs::before`, el chip dorado de la tarjeta de socio y la placa de
  OTP. Los puntos ya no van en amarillo: `.saldo-mini` y `.premio-costo-u` son pastillas
  `--verde-hondo` con numero `--verde-claro` (8.53:1), pedido por el dueno.
- Naranja `--naranja #ff9842` (llama) — reservado a accion (botones) y al nivel del medidor.
- Texto `--tinta #14251a`; secundario `--muted #4d6453`.
- El color significa; no se usa para decorar.

Contraste medido, para no re-decirlo: tinta sobre placa 11.94, tinta sobre boton naranja
6.98, `--muted` sobre papel 6.44, `--verde-hondo` sobre `--verde-claro` 8.53,
`--naranja-hondo` sobre papel 4.30, `--peligro` sobre `--peligro-fondo` 4.76, tinta de
marca sobre la barra naranja 6.78 y sobre el chip translucente `rgba(43,18,4,.14)` del
boton "Salir" 5.34. El login perdio el degradado cuando el inicio paso a body blanco, asi
que el viejo 4.25:1 del hero en la esquina oscura del radial ya no aplica: el hero usa
`--tinta` y `--muted` sobre blanco.

## Componentes clave

- `pwa/src/components/Navbar.jsx` — barra superior: `.navbar-marca` sola (el logo viejo
  `antiguoicon.svg` fue borrado de `public/`, de la barra y del `SHELL` del
  serviceworker; el icon de la app instalada sigue siendo `icon.png`),
  acciones (`.saldo-mini` y boton `.sesion`) y `.navbar-tabs` con Inicio / Funcionamiento /
  Recompensas / Ayuda. Es `position: sticky` sobre `--marca`, cierra con la franja
  `--placa` en `.navbar::after`, la pestana activa es una pastilla blanca
  (`--papel` + `--tinta`) y el foco de los controles sobre naranja va en
  `--tinta-sobre-marca`, no en `--verde`.
- `pwa/src/components/RecompensaCard.jsx` — tarjeta de recompensa. Props: `recompensa`,
  `puntos`, `tasa` (puntos por litro), `onCanjear`, `mostrarProgreso`, `sobreVerde`.
  Lee `recompensa.imagen`; si la URL falla (`onError`) vuelve al bloque de rayas.
  Se usa en `views/Canjes.jsx` (con progreso y boton) y en `views/Login.jsx`
  (sin progreso, con `sobreVerde=true` — la prop se llama asi por historia, hoy pinta el
  panel tenue `.premio-card--verde` sobre el body blanco del inicio).
- `.saldo` — tarjeta de socio: `--grad-socio` (naranja), numero en `--tinta-sobre-marca`
  con relieve claro, chip dorado en `.saldo::after` (40x29, arriba a la izquierda) y
  textura de rejilla en `.saldo::before`.
- `.cabecera` — sticky, `--grad-socio` con `border-bottom: 3px solid --placa`; `.saldo-mini`
  es una pildora amarilla (`--placa` + `--placa-tinta`, sombras interiores), no numero suelto.
- `.tabs` — fija abajo, regla tricolor verde-amarillo-naranja en `.tabs::before`; pestana
  activa en pastilla `--marca` con tinta oscura.
- `.lista li:has(.pos)` / `:has(.neg)` — acento lateral de 3px segun el signo del
  movimiento; `.delta` en pastilla tintada. Donde `:has()` no existe, el acento
  simplemente no aparece y la fila sigue siendo legible.
- `.datos .lista-info::after` — guion punteado entre etiqueta y valor, lectura de estado
  de cuenta.
- Estados obligatorios: cargando (`.esqueleto` con `.premio-media` + `.premio-cuerpo`,
  pulso 1.4s), vacio (`.vacio`, y `li.muted` con borde punteado), agotado
  (`--agotado`), boton `disabled` cuando no alcanza o stock 0.
- `panel/src/views/Recompensas.jsx` — tabla con miniatura 44x44, creacion e edicion
  inline. La columna `imagen` es una URL publica que se pega en el panel; el backend no
  almacena archivos.
- `.qr-card`, `.qr-img`, `.qr-titulo`, `.qr-hint`, `.qr-vacio` — estilos del ticket QR
  que siguen en la hoja pero sin uso desde que el QR salio de la PWA. Se conservan por si
  vuelve el canje con codigo; si no, son candidatos a borrarse.

## Reglas de layout que no hay que romper

- `.login` centra su contenido con `margin-top/bottom: auto` en el primer y ultimo hijo,
  **no** con `justify-content: center`: con `center` el hero se recorta arriba cuando el
  contenido supera la altura de la pantalla.
- Toda superficie que quepa texto usa `overflow: hidden` solo si el alto esta acotado;
  verificar `scrollWidth > clientWidth` en las tarjetas antes de dar por bueno un cambio.
- Respeta `env(safe-area-inset-top/bottom)` en cabecera, tabs y login, y
  `prefers-reduced-motion` en esqueletos, medidor y transiciones.

## Tokens (pwa/src/styles.css)

```
--fondo --papel --tinta --muted --linea        superficies y tinta (--fondo es blanco puro)
--marca                                        superficie de marca (barra, cabecera, socio, pestana activa)
--tinta-sobre-marca                            texto sobre --marca (oscura, nunca blanca)
--verde --verde-2 --verde-hondo                acento y texto de estado sobre claro
--placa --placa-tinta                          el numero que importa
--naranja --naranja-hondo                      accion y nivel
--peligro --peligro-fondo --peligro-linea      errores
--verde-claro --naranja-claro                  fondos de pastilla y badge
--surface-track                                pista del medidor, esqueletos, controles deshabilitados
--space-1..5                                   escala de espaciado (base 0.25rem)
--radius-ctrl --radius-card --radius-panel     radios
--sombra-card --sombra-nav --grad-socio        elevacion y superficie de socio
--anillo-focus                                 halo de foco en campos
--display                                      Barlow Condensed
```

El panel de administracion (`panel/src/styles.css`) conserva su propia paleta y tipos:
`--green #5fbd44`, `--orange #ff9842`, IBM Plex Sans para el cuerpo y Space Grotesk para
titulos y numeros, con tokens `--bg`, `--panel`, `--line`, `--shadow`. No esta
sincronizado con esta PWA: si se unifican, hacerlo a proposito y en un solo cambio.

Los nombres `--surface-card`, `--line-card` y `--depth-card` que aparecian en versiones
anteriores de este documento no existen en ninguno de los dos hojas de estilo. Solo
`--surface-track` es real, y esta en la PWA.

## Verificacion

`ruff check .` + `pytest` en `api/`; `docker compose up -d --build api panel pwa` (la
migracion nueva se aplica sola al reiniciar el api); `.\dev.ps1 health` (5x200);
`.\dev.ps1 e2e`. Verificar clases nuevas en el bundle servido en `http://127.0.0.1:5140/`.

Para revisar solo estilos sin tocar el stack: `npx vite build` en `pwa/` y
`docker cp pwa/dist/. fidelizacion-glp-pwa-1:/usr/share/nginx/html/`. El contenedor
queda sirviendo el bundle del host; `docker compose build pwa` lo revierte. `docker cp`
acumula hashes viejos en `assets/`: confirmar en el navegador que `index.html` apunta al
CSS nuevo, y si el `fetch` del documento sigue devolviendo el degradado anterior, el
serviceworker `fid-glp-v9` esta sirviendo cache — desregistrarlo y vaciar `caches` antes
de recargar con `ignoreCache`. La sesion de prueba se monta contra
`http://127.0.0.1:8002/fid-api` con `POST /auth/otp/request` (leer `debug_codigo`) y
`POST /auth/otp/verify`, guardando el token en `localStorage.fid_cliente_token`.
