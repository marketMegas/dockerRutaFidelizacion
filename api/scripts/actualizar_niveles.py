"""Actualiza los umbrales de litros de los niveles del catalogo vigente."""

from app.services import catalogo

ESCALA = {
    "arranque": (1.0, "De 1 a 99 litros en el mes: 1 punto por litro."),
    "plata": (100.0, "De 100 a 249 litros en el mes: 1.25 puntos por litro."),
    "oro": (250.0, "De 250 a 499 litros en el mes: 1.5 puntos por litro."),
    "diamante": (500.0, "Desde 500 litros en el mes: 2 puntos por litro."),
}


def main() -> None:
    datos = catalogo.leer()
    niveles = []
    cambios = []

    for nivel in datos["niveles"]:
        nuevo = dict(nivel)
        objetivo = ESCALA.get(nivel["clave"])
        if objetivo is None:
            niveles.append(nuevo)
            continue
        minimo, descripcion = objetivo
        if float(nuevo["minimo"]) != minimo:
            cambios.append(f"{nuevo['clave']}: {nuevo['minimo']:g} L -> {minimo:g} L")
        elif nuevo.get("descripcion") != descripcion:
            cambios.append(f"{nuevo['clave']}: descripcion actualizada")
        nuevo["minimo"] = minimo
        nuevo["descripcion"] = descripcion
        niveles.append(nuevo)

    faltantes = sorted(clave for clave in ESCALA if all(n["clave"] != clave for n in niveles))
    if faltantes:
        raise SystemExit(f"Faltan niveles en el catalogo: {', '.join(faltantes)}")

    if not cambios:
        print("Los niveles ya tienen los umbrales vigentes.")
        return

    guardado = catalogo.guardar(
        {"version": datos["version"], "niveles": niveles, "premios": datos["premios"]},
        version_esperada=datos["version"],
    )
    print("Niveles actualizados:")
    for cambio in cambios:
        print(f"  - {cambio}")
    print(f"Version del catalogo: {guardado['version']}")


if __name__ == "__main__":
    main()
