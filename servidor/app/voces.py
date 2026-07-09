"""Servicio de voces (Módulo 5 del diseño): texto a voz con ElevenLabs.

El DJ escribe una línea de diálogo, elige la voz del personaje de un catálogo
y el audio se genera para reproducirse en la mesa. Aquí vive todo lo que habla
con ElevenLabs, aislado del resto del programa.

Sin clave de API el programa NO se rompe: entra en "modo demostración" y
genera un tono corto (un audio real, pero de relleno) para que toda la
experiencia —catálogo, asignar voces, narrar, historial— se pueda ver y probar
antes de contratar el servicio. Al poner la clave (variable de entorno
ELEVENLABS_API_KEY) las mismas pantallas producen voces reales sin tocar nada.
"""

import io
import math
import os
import struct
import wave

import httpx

# Catálogo inicial de voces sugeridas (voces prediseñadas y públicas de
# ElevenLabs). Es el punto de partida —como la paleta de terrenos del mapa—:
# el usuario crea sus propias voces en su sistema apuntando a una de estas o a
# cualquier otro identificador de voz suyo. Funcionan en español con el modelo
# multilingüe.
VOCES_SUGERIDAS: list[dict] = [
    {"voz_externa_id": "EXAVITQu4vr4xnSDxMaL", "nombre": "Bella", "descripcion": "Voz femenina cálida y serena", "genero": "femenina"},
    {"voz_externa_id": "21m00Tcm4TlvDq8ikWAM", "nombre": "Rachel", "descripcion": "Narradora femenina clara y neutral", "genero": "femenina"},
    {"voz_externa_id": "AZnzlk1XvdvUeBnXmlld", "nombre": "Domi", "descripcion": "Femenina firme y decidida", "genero": "femenina"},
    {"voz_externa_id": "ErXwobaYiN019PkySvjV", "nombre": "Antoni", "descripcion": "Masculina joven y amable", "genero": "masculina"},
    {"voz_externa_id": "pNInz6obpgDQGcFmaJgB", "nombre": "Adam", "descripcion": "Masculina grave, buena para narrar", "genero": "masculina"},
    {"voz_externa_id": "VR6AewLTigWG4xSOukaG", "nombre": "Arnold", "descripcion": "Masculina profunda y contundente, tono de guerrero", "genero": "masculina"},
    {"voz_externa_id": "TxGEqnHWrfWFTfGW9XjX", "nombre": "Josh", "descripcion": "Masculina joven y áspera", "genero": "masculina"},
    {"voz_externa_id": "yoZ06aMxZJJ28mfd3POQ", "nombre": "Sam", "descripcion": "Masculina neutra, versátil para monstruos y aldeanos", "genero": "masculina"},
]

# Modelo de ElevenLabs con soporte de español.
MODELO_TTS = "eleven_multilingual_v2"

# Límite prudente de caracteres por línea narrada (evita facturas sorpresa).
MAX_CARACTERES = 800


class ErrorDeVoz(Exception):
    """Algo falló al generar el audio; el mensaje va en español para la mesa."""


def clave_api() -> str | None:
    clave = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    return clave or None


def hay_api() -> bool:
    """¿Está configurada la clave de ElevenLabs? Si no, se usa el modo demostración."""
    return clave_api() is not None


def generar_audio(
    texto: str, voz_externa_id: str, ajustes: dict | None = None
) -> tuple[bytes, str, bool]:
    """Convierte texto en audio. Devuelve (bytes, tipo_mime, es_demostracion).

    Con clave configurada llama a ElevenLabs y devuelve voz real (MP3).
    Sin clave devuelve un tono de demostración (WAV) para que el flujo completo
    funcione igual. Si ElevenLabs falla, se lanza ErrorDeVoz con un mensaje claro.
    """
    texto = texto.strip()
    if not texto:
        raise ErrorDeVoz("No hay nada que narrar: escribe una línea de diálogo.")
    if len(texto) > MAX_CARACTERES:
        raise ErrorDeVoz(
            f"La línea es muy larga ({len(texto)} caracteres). "
            f"El máximo por narración es {MAX_CARACTERES}."
        )

    clave = clave_api()
    if clave is None:
        return _audio_demostracion(texto, voz_externa_id), "audio/wav", True

    return _audio_elevenlabs(texto, voz_externa_id, ajustes or {}, clave), "audio/mpeg", False


def _audio_elevenlabs(texto: str, voz_externa_id: str, ajustes: dict, clave: str) -> bytes:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voz_externa_id}"
    cuerpo = {
        "text": texto,
        "model_id": ajustes.get("modelo", MODELO_TTS),
        "voice_settings": {
            "stability": float(ajustes.get("estabilidad", 0.5)),
            "similarity_boost": float(ajustes.get("similitud", 0.75)),
        },
    }
    try:
        respuesta = httpx.post(
            url,
            headers={"xi-api-key": clave, "Content-Type": "application/json"},
            json=cuerpo,
            timeout=60.0,
        )
    except httpx.HTTPError:
        raise ErrorDeVoz(
            "No se pudo contactar con ElevenLabs. Revisa tu conexión a internet."
        )

    if respuesta.status_code == 401:
        raise ErrorDeVoz("ElevenLabs rechazó la clave de API (ELEVENLABS_API_KEY). Revísala.")
    if respuesta.status_code == 422:
        raise ErrorDeVoz(
            "ElevenLabs no reconoció esa voz. Comprueba el identificador de voz "
            "(voz_externa_id) del personaje."
        )
    if respuesta.status_code == 429:
        raise ErrorDeVoz("ElevenLabs está saturado o se agotó tu cuota. Intenta más tarde.")
    if respuesta.status_code >= 400:
        raise ErrorDeVoz(f"ElevenLabs devolvió un error ({respuesta.status_code}).")

    return respuesta.content


def _audio_demostracion(texto: str, semilla: str) -> bytes:
    """Genera un WAV corto de tono suave, sin depender de servicios externos.

    La frecuencia depende de la voz elegida (así se oyen distintas entre sí) y la
    duración crece con el largo del texto. Es un marcador de posición audible que
    deja probar toda la función antes de configurar ElevenLabs.
    """
    tasa = 16000  # muestras por segundo
    palabras = max(1, len(texto.split()))
    duracion = min(0.35 + palabras * 0.13, 5.0)  # segundos
    # Frecuencia base 220–520 Hz derivada de la voz para diferenciarlas.
    base = 220 + (abs(hash(semilla)) % 300)

    total = int(tasa * duracion)
    marco = io.BytesIO()
    with wave.open(marco, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)  # 16 bits
        w.setframerate(tasa)
        muestras = bytearray()
        for i in range(total):
            t = i / tasa
            # Vibrato leve para que suene como "una voz" y no un pitido plano.
            frecuencia = base + 12 * math.sin(2 * math.pi * 5 * t)
            envolvente = min(1.0, t * 8, (duracion - t) * 8)  # entrada/salida suave
            valor = 0.35 * envolvente * math.sin(2 * math.pi * frecuencia * t)
            muestras += struct.pack("<h", int(valor * 32767))
        w.writeframes(bytes(muestras))
    return marco.getvalue()
