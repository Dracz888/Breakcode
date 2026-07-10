"""Mesa de sonido: ambientes y música de fondo para la mesa (Módulo 5.7).

El DJ pone atmósferas de fondo —taberna, batalla, bosque, lluvia, olas…— que
suenan en bucle mientras se juega. Como con las voces, todo funciona al instante
sin descargar nada: cada ambiente integrado se **sintetiza** aquí en el servidor
(ruido filtrado, retumbos, chispas, tintineos), así no hacen falta archivos de
audio ni licencias para empezar. Cuando el DJ tenga grabaciones reales, puede
subirlas y usarlas igual desde la misma mesa de sonido.

Los ambientes integrados se generan una sola vez y se guardan en memoria.
"""

import array
import io
import math
import random
import wave

TASA = 22050  # muestras por segundo (suficiente para atmósferas, mitad de peso)


# Catálogo de ambientes integrados. Cada uno se sintetiza bajo demanda.
# 'bucle' indica si suena en repetición continua (atmósfera) o una sola vez
# (efecto puntual, como el choque de armas).
AMBIENTES_INTEGRADOS: list[dict] = [
    {"clave": "bosque", "nombre": "Bosque", "categoria": "Naturaleza", "icono": "🌲", "descripcion": "Viento entre los árboles y pájaros lejanos", "bucle": True},
    {"clave": "lluvia", "nombre": "Lluvia", "categoria": "Naturaleza", "icono": "🌧️", "descripcion": "Lluvia constante y menuda", "bucle": True},
    {"clave": "viento", "nombre": "Viento", "categoria": "Naturaleza", "icono": "🌬️", "descripcion": "Ventisca abierta con ráfagas", "bucle": True},
    {"clave": "cueva", "nombre": "Cueva", "categoria": "Naturaleza", "icono": "🕳️", "descripcion": "Goteo con eco en la oscuridad", "bucle": True},
    {"clave": "rio", "nombre": "Río", "categoria": "Agua", "icono": "🏞️", "descripcion": "Agua corriendo sobre las piedras", "bucle": True},
    {"clave": "mar", "nombre": "Mar", "categoria": "Agua", "icono": "🌊", "descripcion": "Olas rompiendo, subida y bajada", "bucle": True},
    {"clave": "fuego", "nombre": "Fogata", "categoria": "Hogar", "icono": "🔥", "descripcion": "Crepitar de una hoguera", "bucle": True},
    {"clave": "taberna", "nombre": "Taberna", "categoria": "Social", "icono": "🍺", "descripcion": "Murmullo de gente, jarras y fuego", "bucle": True},
    {"clave": "fiesta", "nombre": "Fiesta", "categoria": "Social", "icono": "🎉", "descripcion": "Bullicio animado y palmas", "bucle": True},
    {"clave": "guerra", "nombre": "Fragor de batalla", "categoria": "Combate", "icono": "⚔️", "descripcion": "Retumbar, gritos lejanos y choques", "bucle": True},
    {"clave": "tambores", "nombre": "Tambores de guerra", "categoria": "Combate", "icono": "🥁", "descripcion": "Percusión marcial en marcha", "bucle": True},
    {"clave": "choque_armas", "nombre": "Choque de armas", "categoria": "Combate", "icono": "🗡️", "descripcion": "Espadas que chocan (efecto puntual)", "bucle": False},
]

_CLAVES = {a["clave"] for a in AMBIENTES_INTEGRADOS}
_cache: dict[str, bytes] = {}


def existe(clave: str) -> bool:
    return clave in _CLAVES


def audio_integrado(clave: str) -> bytes:
    """Devuelve el WAV del ambiente integrado, generándolo la primera vez."""
    if clave not in _cache:
        _cache[clave] = _GENERADORES[clave]()
    return _cache[clave]


# ---------- Utilidades de síntesis ----------

def _empaquetar(muestras: list[float]) -> bytes:
    """Normaliza a un volumen seguro y arma un WAV mono de 16 bits."""
    pico = max((abs(m) for m in muestras), default=1.0) or 1.0
    escala = 0.9 / pico
    datos = array.array("h", (int(m * escala * 32767) for m in muestras))
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TASA)
        w.writeframes(datos.tobytes())
    return buffer.getvalue()


def _en_bucle(muestras: list[float], fundido_seg: float = 0.4) -> list[float]:
    """Hace la unión final→inicio imperceptible para que el bucle no dé saltos."""
    n = len(muestras)
    f = int(fundido_seg * TASA)
    if f * 2 >= n:
        return muestras
    salida = muestras[: n - f]
    for i in range(f):
        a = i / f
        salida[i] = muestras[i] * a + muestras[n - f + i] * (1 - a)
    return salida


def _ruido_grave(n: int, corte: float, rng: random.Random) -> list[float]:
    """Ruido pasado por un filtro suave: cuanto menor el corte, más grave/apagado."""
    y = 0.0
    salida = [0.0] * n
    for i in range(n):
        y += corte * (rng.uniform(-1, 1) - y)
        salida[i] = y
    return salida


def _golpe(destino: list[float], inicio: int, dur: float, frecuencias, decaimiento: float, ganancia: float, rng: random.Random) -> None:
    """Superpone un transitorio (tintineo, chispa, retumbo) con caída exponencial."""
    n = int(dur * TASA)
    for i in range(n):
        pos = inicio + i
        if pos >= len(destino):
            break
        t = i / TASA
        env = math.exp(-t * decaimiento)
        s = sum(math.sin(2 * math.pi * fr * t) for fr in frecuencias) / len(frecuencias)
        s += rng.uniform(-1, 1) * math.exp(-t * decaimiento * 3) * 0.4  # ataque ruidoso
        destino[pos] += s * env * ganancia


# ---------- Generadores por ambiente ----------

def _gen_rio() -> bytes:
    rng = random.Random("rio")
    n = int(10 * TASA)
    grave = _ruido_grave(n, 0.16, rng)
    brillo = _ruido_grave(n, 0.55, random.Random("rio2"))
    mezcla = [grave[i] + 0.25 * brillo[i] for i in range(n)]
    return _empaquetar(_en_bucle(mezcla))


def _gen_mar() -> bytes:
    rng = random.Random("mar")
    n = int(11 * TASA)
    base = _ruido_grave(n, 0.12, rng)
    salida = [0.0] * n
    periodo = 5.5  # segundos por ola
    for i in range(n):
        t = i / TASA
        ola = 0.5 + 0.5 * math.sin(2 * math.pi * t / periodo - math.pi / 2)
        salida[i] = base[i] * (0.15 + 0.85 * ola**2)
    return _empaquetar(_en_bucle(salida, 1.0))


def _gen_lluvia() -> bytes:
    rng = random.Random("lluvia")
    n = int(9 * TASA)
    base = _ruido_grave(n, 0.45, rng)
    salida = [0.6 * v for v in base]
    for _ in range(int(9 * 40)):  # gotas dispersas
        _golpe(salida, rng.randrange(n), 0.02, [rng.uniform(2000, 5000)], 120, 0.3, rng)
    return _empaquetar(_en_bucle(salida))


def _gen_viento() -> bytes:
    rng = random.Random("viento")
    n = int(11 * TASA)
    base = _ruido_grave(n, 0.09, rng)
    salida = [0.0] * n
    for i in range(n):
        t = i / TASA
        rafaga = 0.5 + 0.5 * math.sin(2 * math.pi * t / 4.0) * math.sin(2 * math.pi * t / 7.3)
        salida[i] = base[i] * (0.3 + 0.7 * rafaga)
    return _empaquetar(_en_bucle(salida, 1.0))


def _gen_bosque() -> bytes:
    rng = random.Random("bosque")
    n = int(12 * TASA)
    salida = [0.4 * v for v in _ruido_grave(n, 0.08, rng)]  # brisa de fondo
    for _ in range(14):  # cantos de pájaro
        inicio = rng.randrange(n)
        dur = rng.uniform(0.12, 0.3)
        base = rng.uniform(1800, 3600)
        m = int(dur * TASA)
        for i in range(m):
            pos = inicio + i
            if pos >= n:
                break
            t = i / TASA
            env = math.sin(math.pi * i / m) ** 2
            trino = base + 400 * math.sin(2 * math.pi * 18 * t)
            salida[pos] += 0.3 * env * math.sin(2 * math.pi * trino * t)
    return _empaquetar(_en_bucle(salida))


def _gen_cueva() -> bytes:
    rng = random.Random("cueva")
    n = int(12 * TASA)
    salida = [0.15 * v for v in _ruido_grave(n, 0.05, rng)]  # rumor grave
    for _ in range(10):  # goteos con eco
        inicio = rng.randrange(n)
        for eco, gan in [(0, 0.6), (int(0.28 * TASA), 0.3), (int(0.55 * TASA), 0.15)]:
            _golpe(salida, inicio + eco, 0.12, [820, 1230], 30, gan, rng)
    return _empaquetar(_en_bucle(salida))


def _gen_fuego() -> bytes:
    rng = random.Random("fuego")
    n = int(9 * TASA)
    salida = [0.4 * v for v in _ruido_grave(n, 0.10, rng)]  # rugido grave
    for _ in range(int(9 * 55)):  # chasquidos y chispas
        _golpe(salida, rng.randrange(n), 0.03, [rng.uniform(400, 2500)], 90, rng.uniform(0.15, 0.5), rng)
    return _empaquetar(_en_bucle(salida))


def _gen_taberna() -> bytes:
    rng = random.Random("taberna")
    n = int(12 * TASA)
    grave = _ruido_grave(n, 0.30, rng)
    muy_grave = _ruido_grave(n, 0.05, random.Random("tab2"))
    salida = [0.0] * n
    for i in range(n):
        t = i / TASA
        vaiven = 0.6 + 0.4 * math.sin(2 * math.pi * t / 3.1) * math.sin(2 * math.pi * t / 5.7)
        murmullo = (grave[i] - 0.7 * muy_grave[i]) * vaiven  # voz de multitud
        salida[i] = 0.6 * murmullo
    for _ in range(20):  # tintineo de jarras
        _golpe(salida, rng.randrange(n), 0.15, [2100, 3200, 4300], 22, 0.35, rng)
    for _ in range(int(12 * 20)):  # fuego tenue del hogar
        _golpe(salida, rng.randrange(n), 0.03, [rng.uniform(500, 1800)], 90, 0.15, rng)
    return _empaquetar(_en_bucle(salida))


def _gen_fiesta() -> bytes:
    rng = random.Random("fiesta")
    n = int(12 * TASA)
    grave = _ruido_grave(n, 0.35, rng)
    salida = [0.5 * grave[i] for i in range(n)]  # bullicio brillante
    compas = 0.5  # segundos por palma
    t_palma = 0.0
    while t_palma < 12:  # palmas rítmicas
        _golpe(salida, int(t_palma * TASA), 0.05, [1500, 2500, 3500], 45, 0.4, rng)
        t_palma += compas
    for _ in range(30):  # risas/vítores dispersos
        _golpe(salida, rng.randrange(n), 0.4, [700, 1100], 6, 0.3, rng)
    return _empaquetar(_en_bucle(salida))


def _gen_guerra() -> bytes:
    rng = random.Random("guerra")
    n = int(12 * TASA)
    salida = [0.35 * v for v in _ruido_grave(n, 0.06, rng)]  # fragor de fondo
    for _ in range(18):  # retumbos lejanos (impactos, catapultas)
        _golpe(salida, rng.randrange(n), 0.7, [55, 80, 110], 6, 0.7, rng)
    for _ in range(24):  # choques metálicos
        _golpe(salida, rng.randrange(n), 0.25, [1400, 2100, 2900, 3600], 20, 0.4, rng)
    for _ in range(12):  # gritos de multitud
        _golpe(salida, rng.randrange(n), 0.6, [500, 900, 1300], 5, 0.3, rng)
    return _empaquetar(_en_bucle(salida))


def _gen_tambores() -> bytes:
    rng = random.Random("tambores")
    compas = 0.5  # negra
    pasos = 16   # 8 segundos, bucle exacto (sin fundido, es rítmico)
    n = int(pasos * compas * TASA)
    salida = [0.25 * v for v in _ruido_grave(n, 0.05, random.Random("tam2"))]
    patron = [1.0, 0.0, 0.55, 0.0, 0.8, 0.0, 0.55, 0.35]
    for paso in range(pasos):
        fuerza = patron[paso % len(patron)]
        if fuerza <= 0:
            continue
        inicio = int(paso * compas * TASA)
        _golpe(salida, inicio, 0.35, [70, 105], 12, 0.9 * fuerza, rng)  # tambor grave
        if fuerza >= 0.8:
            _golpe(salida, inicio, 0.12, [180, 240], 30, 0.4, rng)      # acento agudo
    return _empaquetar(salida)  # ya cierra el compás: loopea limpio


def _gen_choque_armas() -> bytes:
    rng = random.Random("choque")
    n = int(1.4 * TASA)
    salida = [0.0] * n
    for inicio, base in [(0, 1300), (int(0.35 * TASA), 1700), (int(0.7 * TASA), 1100)]:
        _golpe(salida, inicio, 0.6, [base, base * 1.6, base * 2.1, base * 2.7, base * 3.4], 16, 0.9, rng)
    return _empaquetar(salida)


_GENERADORES = {
    "rio": _gen_rio,
    "mar": _gen_mar,
    "lluvia": _gen_lluvia,
    "viento": _gen_viento,
    "bosque": _gen_bosque,
    "cueva": _gen_cueva,
    "fuego": _gen_fuego,
    "taberna": _gen_taberna,
    "fiesta": _gen_fiesta,
    "guerra": _gen_guerra,
    "tambores": _gen_tambores,
    "choque_armas": _gen_choque_armas,
}
