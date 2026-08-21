"""Datos de referencia reales para ARCA/Aduana Argentina.

Todo lo que hay acá es dato público estable (normas ICC/OMC), no inventado:
  - INCOTERMS 2020: las 11 reglas oficiales publicadas por la ICC.
  - Capítulos del Sistema Armonizado (SA/HS): los 97 capítulos son un
    estándar internacional estable, base de la Nomenclatura Común Mercosur
    (NCM) — los primeros 2 dígitos de cualquier código NCM corresponden a
    uno de estos capítulos.
  - Categorías Monotributo: tabla de AFIP/ARCA vigente. Estos montos se
    actualizan semestralmente por RG — hay que revisar `vigencia` y
    actualizar cuando ARCA publique la nueva escala.
"""

INCOTERMS_2020 = [
    {"code": "EXW", "name": "Ex Works", "grupo": "E", "modo": "Cualquiera", "paga_flete": "Comprador", "paga_seguro": "Comprador", "transferencia_riesgo": "En fábrica/depósito del vendedor"},
    {"code": "FCA", "name": "Free Carrier", "grupo": "F", "modo": "Cualquiera", "paga_flete": "Comprador", "paga_seguro": "Comprador", "transferencia_riesgo": "Al entregar al transportista designado"},
    {"code": "FAS", "name": "Free Alongside Ship", "grupo": "F", "modo": "Marítimo/fluvial", "paga_flete": "Comprador", "paga_seguro": "Comprador", "transferencia_riesgo": "Al costado del buque en puerto de embarque"},
    {"code": "FOB", "name": "Free On Board", "grupo": "F", "modo": "Marítimo/fluvial", "paga_flete": "Comprador", "paga_seguro": "Comprador", "transferencia_riesgo": "Al cruzar la borda del buque"},
    {"code": "CFR", "name": "Cost and Freight", "grupo": "C", "modo": "Marítimo/fluvial", "paga_flete": "Vendedor", "paga_seguro": "Comprador", "transferencia_riesgo": "Al cruzar la borda del buque (origen)"},
    {"code": "CIF", "name": "Cost, Insurance and Freight", "grupo": "C", "modo": "Marítimo/fluvial", "paga_flete": "Vendedor", "paga_seguro": "Vendedor", "transferencia_riesgo": "Al cruzar la borda del buque (origen)"},
    {"code": "CPT", "name": "Carriage Paid To", "grupo": "C", "modo": "Cualquiera", "paga_flete": "Vendedor", "paga_seguro": "Comprador", "transferencia_riesgo": "Al entregar al primer transportista"},
    {"code": "CIP", "name": "Carriage and Insurance Paid To", "grupo": "C", "modo": "Cualquiera", "paga_flete": "Vendedor", "paga_seguro": "Vendedor", "transferencia_riesgo": "Al entregar al primer transportista"},
    {"code": "DAP", "name": "Delivered At Place", "grupo": "D", "modo": "Cualquiera", "paga_flete": "Vendedor", "paga_seguro": "Vendedor", "transferencia_riesgo": "En el lugar de destino convenido, sin descargar"},
    {"code": "DPU", "name": "Delivered At Place Unloaded", "grupo": "D", "modo": "Cualquiera", "paga_flete": "Vendedor", "paga_seguro": "Vendedor", "transferencia_riesgo": "En destino, descargado"},
    {"code": "DDP", "name": "Delivered Duty Paid", "grupo": "D", "modo": "Cualquiera", "paga_flete": "Vendedor", "paga_seguro": "Vendedor", "transferencia_riesgo": "En destino, con derechos de importación pagos"},
]

# Primeros 2 dígitos de todo código NCM = capítulo del Sistema Armonizado (SA/HS),
# estándar OMA de 97 capítulos. Fuente estable, no cambia por país.
HS_CHAPTERS = {
    "01": "Animales vivos", "02": "Carne y despojos comestibles",
    "03": "Pescados y crustáceos", "04": "Leche y productos lácteos; huevos; miel",
    "05": "Productos de origen animal n.e.p.", "06": "Plantas vivas y productos de floricultura",
    "07": "Hortalizas, plantas, raíces y tubérculos alimenticios",
    "08": "Frutas y frutos comestibles", "09": "Café, té, yerba mate y especias",
    "10": "Cereales", "11": "Productos de molinería; malta; almidones",
    "12": "Semillas y frutos oleaginosos; plantas industriales o medicinales",
    "13": "Gomas, resinas y demás jugos vegetales", "14": "Materias trenzables vegetales",
    "15": "Grasas y aceites animales o vegetales",
    "16": "Preparaciones de carne, pescado o crustáceos",
    "17": "Azúcares y artículos de confitería", "18": "Cacao y sus preparaciones",
    "19": "Preparaciones a base de cereales, harina o leche",
    "20": "Preparaciones de hortalizas, frutas u otros frutos",
    "21": "Preparaciones alimenticias diversas", "22": "Bebidas, líquidos alcohólicos y vinagre",
    "23": "Residuos de industrias alimentarias; alimento para animales",
    "24": "Tabaco y sucedáneos del tabaco elaborados",
    "25": "Sal; azufre; tierras y piedras; yeso, cal y cemento",
    "26": "Minerales metalíferos, escorias y cenizas",
    "27": "Combustibles minerales, aceites minerales y ceras",
    "28": "Productos químicos inorgánicos", "29": "Productos químicos orgánicos",
    "30": "Productos farmacéuticos", "31": "Abonos",
    "32": "Extractos curtientes o tintóreos; pinturas y barnices",
    "33": "Aceites esenciales y resinoides; perfumería y cosmética",
    "34": "Jabones, agentes de superficie, ceras artificiales",
    "35": "Materias albuminoideas; colas; enzimas",
    "36": "Pólvora y explosivos; artículos de pirotecnia",
    "37": "Productos fotográficos o cinematográficos",
    "38": "Productos diversos de las industrias químicas",
    "39": "Plástico y sus manufacturas", "40": "Caucho y sus manufacturas",
    "41": "Pieles (excepto peletería) y cueros", "42": "Manufacturas de cuero",
    "43": "Peletería y confecciones de peletería",
    "44": "Madera, carbón vegetal y manufacturas de madera",
    "45": "Corcho y sus manufacturas", "46": "Manufacturas de espartería o cestería",
    "47": "Pasta de madera; papel o cartón para reciclar",
    "48": "Papel y cartón; manufacturas de pasta de celulosa",
    "49": "Productos editoriales, de la prensa e industrias gráficas",
    "50": "Seda", "51": "Lana y pelo", "52": "Algodón",
    "53": "Las demás fibras textiles vegetales", "54": "Filamentos sintéticos o artificiales",
    "55": "Fibras sintéticas o artificiales discontinuas",
    "56": "Guata, fieltro y telas sin tejer; hilados especiales",
    "57": "Alfombras y demás revestimientos textiles para el suelo",
    "58": "Tejidos especiales; superficies textiles con mechón insertado",
    "59": "Telas impregnadas, recubiertas o revestidas",
    "60": "Tejidos de punto", "61": "Prendas de vestir de punto",
    "62": "Prendas de vestir, excepto de punto",
    "63": "Los demás artículos textiles confeccionados",
    "64": "Calzado, polainas y artículos análogos",
    "65": "Artículos de sombrerería y sus partes",
    "66": "Paraguas, sombrillas, bastones", "67": "Plumas y plumón preparados",
    "68": "Manufacturas de piedra, yeso, cemento, amianto, mica",
    "69": "Productos cerámicos", "70": "Vidrio y sus manufacturas",
    "71": "Perlas finas, piedras preciosas, metales preciosos",
    "72": "Fundición, hierro y acero", "73": "Manufacturas de fundición, hierro o acero",
    "74": "Cobre y sus manufacturas", "75": "Níquel y sus manufacturas",
    "76": "Aluminio y sus manufacturas", "78": "Plomo y sus manufacturas",
    "79": "Cinc y sus manufacturas", "80": "Estaño y sus manufacturas",
    "81": "Los demás metales comunes; cermets",
    "82": "Herramientas y útiles de metal común",
    "83": "Manufacturas diversas de metal común",
    "84": "Reactores nucleares, calderas, máquinas y aparatos mecánicos",
    "85": "Máquinas y aparatos eléctricos; equipos de grabación y sonido",
    "86": "Vehículos y material para vías férreas",
    "87": "Vehículos automóviles, tractores, velocípedos",
    "88": "Aeronaves y sus partes", "89": "Barcos y demás artefactos flotantes",
    "90": "Instrumentos y aparatos de óptica, medida, médicos",
    "91": "Aparatos de relojería", "92": "Instrumentos musicales",
    "93": "Armas y municiones", "94": "Muebles; artículos de cama; aparatos de alumbrado",
    "95": "Juguetes, juegos y artículos para deporte",
    "96": "Manufacturas diversas", "97": "Objetos de arte, colección o antigüedad",
}

# Escala Monotributo — ARCA/AFIP. VIGENCIA: revisar RG de actualización semestral
# (enero y julio). Última actualización cargada acá: RG vigente 2do semestre 2024.
MONOTRIBUTO_CATEGORIAS = {
    "vigencia": "2do semestre 2024 (verificar RG ARCA vigente antes de usar en producción)",
    "categorias": [
        {"categoria": "A", "facturacion_max_anual": 6_450_000, "cuota_servicios": 15_845, "cuota_bienes": 15_845},
        {"categoria": "B", "facturacion_max_anual": 9_450_000, "cuota_servicios": 18_082, "cuota_bienes": 18_082},
        {"categoria": "C", "facturacion_max_anual": 13_250_000, "cuota_servicios": 20_609, "cuota_bienes": 19_931},
        {"categoria": "D", "facturacion_max_anual": 16_450_000, "cuota_servicios": 26_140, "cuota_bienes": 24_602},
        {"categoria": "E", "facturacion_max_anual": 19_350_000, "cuota_servicios": 30_936, "cuota_bienes": 28_638},
        {"categoria": "F", "facturacion_max_anual": 24_200_000, "cuota_servicios": 37_902, "cuota_bienes": 34_495},
        {"categoria": "G", "facturacion_max_anual": 29_050_000, "cuota_servicios": 44_887, "cuota_bienes": 40_351},
        {"categoria": "H", "facturacion_max_anual": 44_950_000, "cuota_servicios": 68_887, "cuota_bienes": 61_920},
        {"categoria": "I", "facturacion_max_anual": 50_400_000, "cuota_servicios": None, "cuota_bienes": 70_222},
        {"categoria": "J", "facturacion_max_anual": 57_800_000, "cuota_servicios": None, "cuota_bienes": 80_764},
        {"categoria": "K", "facturacion_max_anual": 69_800_000, "cuota_servicios": None, "cuota_bienes": 97_446},
    ],
}
