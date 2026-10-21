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

**Medidor de avance.** El avance hacia cada recompensa es una barra plana (puntos actuales /
costo), a proposito igual a la `.barra` de Reportes del panel: nada de segmentos ni sombra
interior desde 2026-10-20, por orden del dueno. Completan la firma:

1. `.medidor` — pista 8px, radio 4px, fondo `--surface-track`, `overflow: hidden`.
2. `.nivel` — relleno degradado `linear-gradient(90deg, --verde, --naranja)`, ancho = avance,
   transicion de 0.4s (anulada en `prefers-reduced-motion: reduce`).
3. `.premio-estado` — "Te faltan N pts" / "Listo para canjear" (este ultimo en pastilla verde).
4. `.premio-costo` — numeral en Barlow Condensed tabular, como lectura de odometro, con la
   unidad en la pildora verde `.premio-costo-u` (`--verde-hondo` con `--verde-claro`).
5. `.premio-litros` — **eliminado (2026-10-21)**: la equivalencia "Equivale a N L de glp"
   ya no se muestra en ninguna tarjeta. El costo en puntos se lee solo en `.premio-costo`.
   No reintroducirlo: el pie de la tarjeta es para el estado y el canje.
6. `.premio-media` — miniatura de referencia a la izquierda de cada tarjeta (imagen
   `recompensa.imagen`); si no hay imagen, un bloque de rayas diagonales en
   `--surface-track`. Nunca dejar el hueco vacio.
7. `.placa-chip` — la placa del cliente escrita sobre amarillo placa, en la cabecera.
8. En el catalogo de recompensas (`main.vista--recompensas`) la **imagen es el fondo**
   de la tarjeta: todo el texto se invierte a blanco y el pie (estado + medidor) se
   apoya sobre un velo oscuro, no sobre papel. Ver "Color".

## Profundidad

**Un solo enfoque: sombras suaves.** Las tarjetas usan `--sombra-card`; el borde es un
hairline tenue (`--linea`), nunca la fuente de jerarquia. No mezclar con cambios de
color de superficie para dar elevacion. La elevacion fuerte queda reservada a la barra de
tabs (`--sombra-nav`); el formulario del login paso a `--sombra-card` cuando el inicio
quedo sobre body blanco.

## Proporcion y tamano

El catalogo de recompensas del **inicio/login** es de **una columna**: `.premio-card` toma
su alto del contenido (`min-height: 124px`) y `.premio-media` se estira a ese alto. El
catalogo de la vista **Recompensas** (`main.vista--recompensas`, con y sin sesion) si usa
la tarjeta tipo credito: `aspect-ratio: 1.586/1`, `max-width: 400px`, rejilla
`repeat(auto-fill, minmax(320px, 1fr))` y la imagen de `recompensa.imagen` como **fondo
completo** de la tarjeta, con un velo degradado encima.

- `.premios` — `display: grid; grid-template-columns: minmax(0, 1fr)` (base del inicio/login;
  la vista de recompensas la sobreescribe a `repeat(auto-fill, minmax(320px, 1fr))`).
- `.premio-card` — `flex-direction: row`, `padding: var(--space-3)`, `gap: var(--space-3)`,
  `min-height: 124px`, `overflow: hidden` (formato de fila del inicio/login).
- `.premio-media` — `flex: 0 0 32%`, `min-width: 54px`, `max-width: 128px`, radio 10px,
  `overflow: hidden`; la imagen es `object-fit: cover` a todo el alto de la tarjeta.
- `.premio-cuerpo` — columna flexible con el texto: nombre a 2 lineas
  (`-webkit-line-clamp: 2`), descripcion a 1 linea, medidor de 8px anclado abajo con
  `margin-top: auto`, pie con estado + boton.
- `.premio-card--verde` — las tarjetas de muestra del inicio, sobre body blanco: panel
  `--verde-claro` con hairline `#b6e3c2` y `--sombra-card`, tinta normal. El nombre
  "verde" es historico (vino de cuando iban sobre superficie oscura); hoy es literal: es
  el unico verde de superficie que queda en la PWA.
- `.vista.vista--recompensas .premio-card` — tarjeta tipo credito con la foto de fondo:
  `position: relative`, `aspect-ratio: 1.586/1`, `padding: 0`, `border-radius: 18px`,
  sin borde. `.premio-media` va en `inset: 0` (absoluta, 100% x 100%) y su `::after` pone
  el **velo doble** `linear-gradient(180deg, rgba(8,20,11,.68) 0%, rgba(8,20,11,.18) 30%,
  rgba(8,20,11,.6) 58%, rgba(8,20,11,.92) 100%)`: oscuro en el header y en el pie, la foto
  respira en la franja central. La imagen lleva `filter: saturate(1.06) brightness(0.92)`.
  `.premio-cuerpo` va en `position: relative; z-index: 1` para quedar encima de la foto.
  La tarjeta define `--halo: 0 1px 2px rgba(0,0,0,.7), 0 0 18px rgba(0,0,0,.5)` y todo el
  texto blanco lo usa: nombre `1.08rem`/800, costo `1.5rem`, descripcion `0.8rem`/500,
  litros `0.78rem`/500, estado 700.

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
- **Sobre foto** (`main.vista--recompensas`) el texto de la tarjeta va **en blanco**
  (`#fff`) con el halo `--halo` (`0 1px 2px rgba(0,0,0,.7), 0 0 18px rgba(0,0,0,.5)`):
  nombre, costo, descripcion, litros y estado ("Te faltan N pts"). Las pastillas
  `.premio-costo-u` y `.premio-estado.listo` usan el velo translucido `rgba(8,20,11,.8)` con
  borde interior `rgba(255,255,255,.3)` y texto blanco: el verde hondo tampoco se usa de
  fondo ahi. El boton "Canjear" conserva la tinta oscura (`--placa-tinta` 6.98:1 sobre
  `--naranja`).
- Contraste **sobre foto** (medido sobre las cuatro fotos del catalogo, blanco contra el
  velo): el peor caso del header pasa de 2.54:1 a **6.27:1** y el del pie de 3.68:1 a
  **14.24:1**. En la tarjeta renderizada la mediana del header da **12.17:1** y la del pie
  **15.56:1**. Si se toca el velo o el halo, volver a medir: el blanco sobre foto clara
  cae por debajo de 4.5:1 en cuanto se aligera el degrade.
- Amarillo placa `--placa #f6d51e` sobre `--placa-tinta` — **solo la placa del vehiculo y
  los acentos de marca**: `.placa-chip`, la cornisa del formulario, las franjas de
  `.navbar::after` y `.tabs::before`, el chip dorado de la tarjeta de socio y la placa de
  OTP. Los puntos ya no van en amarillo: `.saldo-mini` y `.premio-costo-u` son pastillas
  `--verde-hondo` con numero `--verde-claro` (8.53:1), pedido por el dueno.
- Naranja `--naranja #ff9842` (llama) — reservado a accion (botones) y al tramo final del
  degradado del medidor (`--verde` → `--naranja`), igual que en Reportes.
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

- `pwa/src/App.jsx` — pie de pagina `<footer className="pie-app">` con la marca
  "Fidelización PUNTOS G-MAX" (`.pie-app-marca`, Barlow Condensed 700, `--verde-hondo`
  porque es texto sobre blanco) y debajo el enlace `.pie-app-link` "Políticas de
  privacidad". Va al final de `.app`, antes de `.tabs`; en las vistas con barra inferior
  fija el `.app.con-tabs` reserva 96px de aire y el pie no queda tapado (verificado a
  390px: pie termina en y=748, la barra arranca en y=790).
- El enlace de politicas apunta al **PDF del dueno**, no a una pantalla propia:
  `pwa/public/Politica de Datos personales - Megas.pdf` servido en la raiz del PWA, por
  eso el href lleva espacios codificados (`/Politica%20de%20Datos%20personales%20-%20Megas.pdf`),
  `target="_blank"` y `rel="noopener noreferrer"`. Si se renombra el PDF hay que
  actualizar ese href. Verificado: responde 200 con `application/pdf` (187631 bytes).
- `pwa/src/components/Navbar.jsx` — barra superior: `.navbar-marca` sola (el logo viejo
  `antiguoicon.svg` fue borrado de `public/`, de la barra y del `SHELL` del
  serviceworker; el icon de la app instalada sigue siendo `icon.png`),
  acciones (`.saldo-mini` y boton `.sesion`) y `.navbar-tabs` con Inicio / Funcionamiento /
  Recompensas / Ayuda. Es `position: sticky` sobre `--marca`, cierra con la franja
  `--placa` en `.navbar::after`, la pestana activa es una pastilla blanca
  (`--papel` + `--tinta`) y el foco de los controles sobre naranja va en
  `--tinta-sobre-marca`, no en `--verde`.
- `pwa/src/views/Login.jsx` — el formulario de placa es el **sidebar del login** en
  escritorio (>=900px): columna de 300px pegada a la izquierda, `position: sticky`, con
  el hero y el catalogo de recompensas a su derecha. En movil sigue siendo una tarjeta
  centrada entre el hero y las recompensas. Los tres pasos (placa, registro, codigo)
  comparten la misma tarjeta y cambian el titulo `.login-panel-titulo`
   ("Registra tu placa" / "Crea tu cuenta" / "Verifica tu codigo").
- **Hero del login con foto (2026-10-21)**: `.login-hero` es una fila con el texto a la
  izquierda (`.login-hero-texto`) y la foto de marca a la derecha
  (`.login-hero-banner`, `object-fit: cover`). Medidas reales: en escritorio (>=900px) la
  foto es `flex: 0 0 58%` x `320px` de alto (589x320 a 1440px de ancho) y el `h1` del
  hero baja a `2.1rem` para que el titulo siga en una linea; en movil (<900px) el hero
  se apila (texto arriba, foto debajo) y la foto **sale del padding de `.login`**
  (`width: calc(100% + 3rem)`, `margin-inline: -1.5rem`, `border-radius: 0`) para tocar
  de borde a borde: 390x224 a 390px de pantalla. La foto es de Pexels
  (`referrerPolicy="no-referrer"`, como las imagenes de recompensa) y el CSP de
  `pwa/nginx.conf` ya permite `img-src https:`. No poner la foto en la barra superior
  (`.navbar`): ahi vive la marca de texto.
- `pwa/src/components/RecompensaCard.jsx` — tarjeta de recompensa. Props: `recompensa`,
  `puntos`, `tasa` (puntos por litro), `onCanjear`, `mostrarProgreso`, `sobreVerde`.
  Lee `recompensa.imagen`; si la URL falla (`onError`) vuelve al bloque de rayas.
  Se usa en `views/Canjes.jsx` (con progreso y boton) y en `views/Login.jsx`
  (sin progreso, con `sobreVerde=true` — la prop se llama asi por historia, hoy pinta el
  panel tenue `.premio-card--verde` sobre el body blanco del inicio).
- `.saldo` — tarjeta de socio: `--grad-socio` (naranja), numero en `--tinta-sobre-marca`
  con relieve claro y chip dorado en `.saldo::after` (40x29, arriba a la izquierda).
  Sin textura de rejilla: la rejilla de `.saldo::before` se elimino por pedido del dueno
  (2026-10-21), el numero se lee sobre el degradado limpio.
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
- `panel/src/views/Recompensas.jsx` — tabla con miniatura `220x147` (`.miniatura`, 3:2,
  `object-fit: cover`; en movil la tabla se vuelve tarjeta y la miniatura ocupa el ancho
  completo con 160px de alto), creacion e edicion inline. La columna `imagen` es una URL
  publica que se pega en el panel; el backend no almacena archivos.
- **La edicion del panel se despliega como un panel, no como inputs en las columnas.**
  La fila de edicion es una unica celda `colspan` (`.celda-edicion`) con el formulario en
  rejilla (`.form-edicion`, `repeat(auto-fit, minmax(200px, 1fr))`, campos con `<label>`,
  preview 84x56 de la imagen y botones `Guardar`/`Cancelar` alineados a la derecha).
  Motivo (2026-10-21): con un input por columna la tabla crecia de 1110px a 1515px y los
  botones quedaban fuera de la ventana; los inputs no pueden encogerse porque
  `table-layout: auto` usa su ancho intrinseco. Aplica a `Recompensas.jsx` y
  `Reglas.jsx` (mismo patron inline). No volver a meter los inputs en las columnas.
- `.qr-card`, `.qr-img`, `.qr-titulo`, `.qr-hint`, `.qr-vacio` — estilos del ticket QR
  que siguen en la hoja pero sin uso desde que el QR salio de la PWA. Se conservan por si
  vuelve el canje con codigo; si no, son candidatos a borrarse.

## Reglas de layout que no hay que romper

- `.login` centra su contenido con `margin-top/bottom: auto` en el primer y ultimo hijo,
  **no** con `justify-content: center`: con `center` el hero se recorta arriba cuando el
  contenido supera la altura de la pantalla.
- En escritorio (>=900px) `.login` es un grid de dos columnas: `panel` (el formulario,
  300px, `sticky`) a la izquierda y `hero` + `premios` a la derecha. El grid reparte el
  alto entre filas, asi que ahi el centrado por margenes automaticas se anula
  (`align-content: start` + `align-items: start` y `margin: 0` en el primer y ultimo hijo).
- La tarjeta del login es compacta: padding `1.1rem` (`1rem` en escritorio), la placa a
  `1.5rem` con `letter-spacing: 0.2em` y `text-indent` igual para compensar el espaciado
  final, y el OTP a `1.05rem`. El estilo de digitos espaciados va solo en `.login input.otp`,
  no en todo `input[inputmode='numeric']`: la cedula se lee normal.
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
