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

**1 punto base = 1 litro** (mientras la regla vigente este a 1.00 pt/L) y el **nivel del mes
multiplica** esos puntos (x1.00 Arranque, x1.25 Plata, x1.50 Oro, x2.00 Diamante). El nivel
efectivo es el mayor entre el del mes anterior y el del mes en curso, asi que el cliente lo
conserva al empezar el mes y lo pierde si deja de tanquear. El costo de cada premio se lee en
puntos, sin equivalencia en litros.

## Firma

**Medidor de avance.** El avance hacia cada recompensa es una barra plana (puntos actuales /
costo), a proposito igual a la `.barra` de Reportes del panel: nada de segmentos ni sombra
interior desde 2026-10-20, por orden del dueno. Completan la firma:

1. `.medidor` — pista 8px, radio 4px, fondo `--surface-track`, `overflow: hidden`.
2. `.nivel` — relleno degradado `linear-gradient(90deg, --menta, --lima)`, ancho = avance,
   transicion de 0.4s (anulada en `prefers-reduced-motion: reduce`).
3. `.premio-estado` — "Te faltan N pts" / "Listo para canjear" (este ultimo en pastilla menta).
4. `.premio-costo` — numeral en Barlow Condensed tabular, como lectura de odometro, con la
   unidad en la pildora azul `.premio-costo-u` (`--azul-hondo` con `--menta-claro`).
5. `.premio-litros` — **eliminado (2026-10-21)**: la equivalencia "Equivale a N L de glp"
   ya no se muestra en ninguna tarjeta. El costo en puntos se lee solo en `.premio-costo`.
   No reintroducirlo: el pie de la tarjeta es para el estado y el canje.
6. `.premio-media` — miniatura de referencia a la izquierda de cada tarjeta (imagen
   `recompensa.imagen`); si no hay imagen, un bloque de rayas diagonales en
   `--surface-track`. Nunca dejar el hueco vacio.
7. `.placa-chip` — la placa del cliente escrita sobre menta placa, en la cabecera.
8. En el catalogo de recompensas (`main.vista--recompensas`) la **imagen es el fondo**
   de la tarjeta: todo el texto se invierte a blanco y el pie (estado + medidor) se
   apoya sobre un velo oscuro, no sobre papel. Ver "Color".
9. **Ticket de codigo** (2026-10-22, reemplaza al QR): `.codigo-caja` es una tarjeta con el
   codigo de 8 caracteres en `--display` (`.codigo-valor`, tabular, `7K3M-92XQ`), etiqueta
   `.codigo-etiqueta`, premio en `.codigo-premio` y acciones `.codigo-acciones` (Copiar /
   Compartir, `.codigo-accion`, la principal `--fuerte` sobre `--lima`). `.codigo-caja--nuevo`
   lleva halo `--menta-claro` para el codigo recien canjeado. En "Mis codigos" cada fila usa
   `.codigo-fila` + `.codigo-mini`. No hay imagen ni verificacion: el codigo es todo el ticket.
10. **Panel de nivel** (`components/NivelPanel.jsx`): `.nivel-panel` (tarjeta de papel),
    `.nivel-chip` (nombre del nivel en pastilla azul noche), la escalera `.escalera` con
    `.peldano` (actual con borde izquierdo menta y fondo `--menta-claro`; nombre, litros y
    multiplicador en `--display` tabular) y el pie `.nivel-pie` + `.nivel-nota` con los litros
    del mes, lo que falta para el siguiente nivel y la nota de mantenimiento. El avance usa el
    mismo `.medidor` de la firma.

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
- `.premio-card--menta` — las tarjetas de muestra del inicio, sobre body blanco: panel
  `--menta-claro` con hairline `#b9f0dc` y `--sombra-card`, tinta normal. El nombre
  "menta" es historico (vino de cuando el panel era verde); hoy es literal: es
  el unico color de superficie claro que queda en la PWA.
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

**Paleta nueva (2026-10-21)**: la PWA adopto la paleta entregada por el dueno en
`pwa/public/paleta.txt` — `#082770` azul noche, `#073edb` azul electrico, `#3af3b0` menta y
`#5bf300` lima. Los tokens se renombraron para que el nombre no mienta: `--verde` paso a
`--menta`, `--naranja` a `--lima`, `--verde-hondo`/`--naranja-hondo` a `--azul-hondo`,
`--verde-claro` a `--menta-claro` y `--naranja-claro` a `--azul-claro`. El panel de
administracion conserva su propia paleta (ver "Tokens").

- Azul marca `--marca #073edb` — **superficies de marca**: barra de navegacion, cabecera,
  tarjeta de socio, pestana activa del menu inferior, paso numerado. Con tinta
  **blanca** encima (`--tinta-sobre-marca #ffffff`, 7.72:1): sobre azul ya no se usa tinta
  oscura.
- Azul noche `--azul-hondo #082770` — **texto sobre superficie clara** y fondo de las
  pastillas de puntos (`.premio-costo-u`, `.sidebar-puntos`). Sobre papel 13.69:1.
- Menta `--menta #3af3b0` — acento: franja de la barra (`.navbar::after`), franja
  tricolor de los tabs, chip de placa, foco (`--anillo-focus`) y textos de estado.
- Lima `--lima #5bf300` — **solo accion**: boton "Canjear", boton del login y tramo final
  del degradado del medidor (`--menta` → `--lima`). Con tinta `--placa-tinta` da 9.30:1.
- Sobre `--marca` la tinta es **blanca**: 7.72:1 sobre #073edb y 13.69:1 sobre #082770.
  Nunca `--azul-hondo` sobre azul.
- Fondo del body **blanco** (`--fondo #ffffff`). Con el fondo blanco el hairline `--linea`
  dejo de alcanzar para separar: las filas `.lista li` llevan `--sombra-card` y las pastillas
  neutras usan `--surface-track` en vez de `--fondo`. No quitar esas piezas "porque el borde
  ya basta": sobre blanco vuelven a fundirse.
- **Sobre foto** (`main.vista--recompensas`) el texto de la tarjeta va **en blanco**
  (`#fff`) con el halo `--halo` (`0 1px 2px rgba(0,0,0,.7), 0 0 18px rgba(0,0,0,.5)`):
  nombre, costo, descripcion y estado ("Te faltan N pts"). Las pastillas
  `.premio-costo-u` y `.premio-estado.listo` usan el velo translucido `rgba(8,20,11,.8)` con
  borde interior `rgba(255,255,255,.3)` y texto blanco. El boton "Canjear" conserva la
  tinta oscura (`--placa-tinta` 9.30:1 sobre `--lima`).
- Contraste **sobre foto** (medido sobre las cuatro fotos del catalogo, blanco contra el
  velo): el peor caso del header pasa de 2.54:1 a **6.27:1** y el del pie de 3.68:1 a
  **14.24:1**. Con la paleta nueva el degradado de la tarjeta es azul noche
  (`linear-gradient(145deg, #082770, #0a3378)`) en vez de verde: en la tarjeta renderizada
  la mediana del header da **15.62:1** y la del pie **17.49:1**. Si se toca el velo o el
  halo, volver a medir: el blanco sobre foto clara cae por debajo de 4.5:1 en cuanto se
  aligera el degrade.
- Pastilla de placa `--placa #3af3b0` sobre `--placa-tinta #082770` (9.53:1) — **solo la
  placa del vehiculo y los acentos de marca**: `.placa-chip`, la cornisa del formulario, el
  input de placa y la placa de OTP. Los puntos ya no van en amarillo: `.saldo-mini` y
  `.premio-costo-u` son pastillas `--azul-hondo` con numero `--menta-claro` (12.44:1).
- Texto `--tinta #082770`; secundario `--muted #52658a` (5.85:1 sobre papel, 5.32:1 sobre
  `--menta-claro`).
- El color significa; no se usa para decorar.

Contraste medido (2026-10-21, Chrome headless sobre la PWA desplegada): blanco sobre
`--marca` 7.72:1, `--tinta` sobre papel 13.69:1, `--azul-hondo` sobre `--menta-claro`
12.44:1, `--muted` sobre papel 5.85:1, `--placa-tinta` sobre `--placa` 9.53:1, tinta sobre
boton lima 9.30:1, `--peligro` sobre `--peligro-fondo` 4.76:1. El hero del login usa
`--tinta` y `--muted` sobre blanco; el degradado viejo del hero ya no aplica.

**Alcance de la paleta**: solo la PWA. `panel/src/styles.css` sigue con `--green #5fbd44` y
`--orange #ff9842`; si se unifican, hacerlo a proposito y en un solo cambio. El
`theme-color` de `pwa/index.html` y el `theme_color`/`background_color` de
`pwa/public/manifest.webmanifest` van en `#073edb` (antes `#ff9842`): si cambia `--marca`,
cambiarlos tambien.

## Componentes clave

- `pwa/src/App.jsx` — pie de pagina `<footer className="pie-app">` con la marca
  "Fidelización PUNTOS G-MAX" (`.pie-app-marca`, Barlow Condensed 700, `--azul-hondo`
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
  `--menta` en `.navbar::after`, la pestana activa es una pastilla blanca
  (`--papel` + `--tinta`) y el foco de los controles sobre azul va en
  `--tinta-sobre-marca`, no en `--menta`.
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
- `pwa/src/components/RecompensaCard.jsx` — tarjeta de premio. Props: `recompensa`,
  `puntos`, `onCanjear`, `canjeando`, `mostrarProgreso`, `sobreMenta`. Usa
  `recompensa.codigos_disponibles` para el estado agotado (el catalogo ya no tiene `stock`).
  Lee `recompensa.imagen`; si la URL falla (`onError`) vuelve al bloque de rayas.
  Se usa en `views/Canjes.jsx` (con progreso y boton) y en `views/Login.jsx`
  (sin progreso, con `sobreMenta=true` — la prop se llama asi por historia, hoy pinta el
  panel tenue `.premio-card--menta` sobre el body blanco del inicio).
- `pwa/src/components/CodigoCaja.jsx` — recuadro del codigo entregado. Muestra
  `.codigo-valor` en `--display` (8 caracteres con guion), boton Copiar (`navigator.clipboard`
  con fallback a textarea + `execCommand`) y Compartir (`navigator.share`, si no existe copia
  y avisa). El aviso de copiado va en `.codigo-aviso` con `role="status"`.
- `pwa/src/components/NivelPanel.jsx` — escalera de niveles y avance del mes (ver firma 10).
  Recibe `cliente` con `nivel`, `multiplicador`, `consumos` y `niveles` (la escalera completa
  viene en `GET /clientes/me`).
- `.saldo` — tarjeta de socio: degradado menta claro (`#eefcf7` → `#d6f9ec` → `#b5f2df`),
  hairline `#b9f0dc`, numero en `--azul-hondo` con relieve claro y `.saldo::after` como chip
  de contacto (40x29, arriba a la izquierda). Sin textura de rejilla: la rejilla de
  `.saldo::before` se elimino por pedido del dueno (2026-10-21), el numero se lee sobre el
  degradado limpio. El saldo ya **no** usa el azul de marca; el azul queda en la barra,
  la cabecera y las pestanas.
- `.navbar` — sticky sobre `--marca` con la franja menta en `.navbar::after`; `.saldo-mini`
  es una pildora menta (`--placa` + `--placa-tinta`, sombras interiores), no numero suelto.
  La clase `.cabecera` ya no existe (la reemplazo el navbar): no reintroducirla.
- `.tabs` — fija abajo, regla tricolor lima-menta-azul en `.tabs::before`; pestana
  activa en pastilla `--marca` con tinta blanca.
- `.lista li:has(.pos)` / `:has(.neg)` — acento lateral de 3px segun el signo del
  movimiento; `.delta` en pastilla tintada. Donde `:has()` no existe, el acento
  simplemente no aparece y la fila sigue siendo legible.
- `.datos .lista-info::after` — guion punteado entre etiqueta y valor, lectura de estado
  de cuenta.
- Estados obligatorios: cargando (`.esqueleto` con `.premio-media` + `.premio-cuerpo`,
  pulso 1.4s), vacio (`.vacio`, y `li.muted` con borde punteado), agotado
  (`--agotado`), boton `disabled` cuando no alcanza o no quedan codigos.
- `panel/src/views/Clientes.jsx` — tabla con la columna **Nivel** (`GET /admin/clientes` devuelve
  `nivel` y `consumo_mes`): `.nivel-celda` con `.nivel-tag` (pastilla `#eef7ea` / `--green-3`)
  y el multiplicador en `.muted`; el detalle repite el nivel en el encabezado.
- `panel/src/views/Catalogo.jsx` — reemplaza a `Recompensas.jsx` (borrado). Tabla con
  miniatura `220x147` (`.miniatura`, 3:2, `object-fit: cover`; en movil la tabla se vuelve
  tarjeta y la miniatura ocupa el ancho completo con 160px de alto), contadores de codigos
  disponibles/entregados, creacion y edicion inline. La columna `imagen` es una URL publica
  que se pega en el panel; el backend no almacena archivos. La edicion del pool abre una
  fila `colspan` con `.campo-codigos`: `.contador-codigos`, `.area-codigos` (monospace, un
  codigo por linea), `.fila-codigos`/`.campo-generar` para generar codigos y `.sin-guardar`
  cuando hay cambios sin guardar. Guardar envia **todo** el catalogo (incluidos los codigos):
  si se omite el pool, se vacia.
- `panel/src/views/Niveles.jsx` — tabla Nivel / Litros en el mes / Multiplicador / Descripcion
  con edicion inline (mismo patron `.celda-edicion`). Guarda niveles y premios juntos con
  `PUT /admin/catalogo` para no perder el pool de codigos.
- **La edicion del panel se despliega como un panel, no como inputs en las columnas.**
  La fila de edicion es una unica celda `colspan` (`.celda-edicion`) con el formulario en
  rejilla (`.form-edicion`, `repeat(auto-fit, minmax(200px, 1fr))`, campos con `<label>`,
  preview 84x56 de la imagen y botones `Guardar`/`Cancelar` alineados a la derecha).
  Motivo (2026-10-21): con un input por columna la tabla crecia de 1110px a 1515px y los
  botones quedaban fuera de la ventana; los inputs no pueden encogerse porque
  `table-layout: auto` usa su ancho intrinseco. Aplica a `Catalogo.jsx`, `Niveles.jsx` y
  `Reglas.jsx` (mismo patron inline). No volver a meter los inputs en las columnas.
- `.codigo-panel` — el codigo entregado en la bitacora read-only de `Reportes.jsx`
  (monospace, `letter-spacing`, `white-space: nowrap`).

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
--tinta-sobre-marca                            texto sobre --marca (blanca)
--azul-hondo                                   texto/fondo sobre superficie clara (--tinta)
--menta --lima                                 acento y accion
--placa --placa-tinta                          el numero que importa
--peligro --peligro-fondo --peligro-linea      errores
--menta-claro --azul-claro                     fondos de pastilla, chip y aviso
--surface-track                                pista del medidor, esqueletos, controles deshabilitados
--space-1..5                                   escala de espaciado (base 0.25rem)
--radius-ctrl --radius-card --radius-panel     radios
--sombra-card --sombra-nav --grad-socio        elevacion y superficie de socio
--anillo-focus                                 halo de foco en campos
--display                                      Barlow Condensed
```

Valores vigentes: `--marca #073edb`, `--tinta-sobre-marca #ffffff`, `--azul-hondo #082770`,
`--tinta #082770`, `--muted #52658a`, `--linea #d8e0f2`, `--menta #3af3b0`,
`--lima #5bf300`, `--placa #3af3b0`, `--placa-tinta #082770`, `--menta-claro #e3f9f1`,
`--azul-claro #e9eefc`, `--surface-track #e9edf8`, `--grad-socio` azul, `--anillo-focus
rgba(91,243,0,.35)`.

El panel de administracion (`panel/src/styles.css`) conserva su propia paleta y tipos:
`--green #5fbd44`, `--orange #ff9842`, IBM Plex Sans para el cuerpo y Space Grotesk para
titulos y numeros, con tokens `--bg`, `--panel`, `--line`, `--shadow`. No esta
sincronizado con esta PWA: si se unifican, hacerlo a proposito y en un solo cambio.

Los nombres `--surface-card`, `--line-card` y `--depth-card` que aparecian en versiones
anteriores de este documento no existen en ninguno de los dos hojas de estilo. Solo
`--surface-track` es real, y esta en la PWA.

## Verificacion

`ruff check .` + `pytest` en `api/` (80 tests); `docker compose up -d --build api panel pwa`
(la migracion nueva se aplica sola al reiniciar el api); `.\dev.ps1 health` (5x200);
`.\dev.ps1 e2e` (venta, niveles y multiplicador). Verificar clases nuevas en el bundle servido
en `http://127.0.0.1:5140/`. Para el canje: pedir OTP, `POST /canjes {premio_clave}`, comprobar
el codigo en `GET /canjes/mis` y que `codigos_disponibles` baje en `GET /catalogo`; el panel lo
lista en Reportes (solo lectura).

Para revisar solo estilos sin tocar el stack: `npx vite build` en `pwa/` y
`docker cp pwa/dist/. fidelizacion-glp-pwa-1:/usr/share/nginx/html/`. El contenedor
queda sirviendo el bundle del host; `docker compose build pwa` lo revierte. `docker cp`
acumula hashes viejos en `assets/`: confirmar en el navegador que `index.html` apunta al
CSS nuevo, y si el `fetch` del documento sigue devolviendo el degradado anterior, el
serviceworker `fid-glp-v26` esta sirviendo cache — desregistrarlo y vaciar `caches` antes
de recargar con `ignoreCache`. La sesion de prueba se monta contra
`http://127.0.0.1:8002/fid-api` con `POST /auth/otp/request` (leer `debug_codigo`) y
`POST /auth/otp/verify`, guardando el token en `localStorage.fid_cliente_token`.
