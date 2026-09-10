"""Envío de correo a través de Resend.

Se usa la API HTTP directamente en vez del SDK: es una sola petición y así el
backend no suma otra dependencia que mantener.

Si `RESEND_API_KEY` está vacía, no se envía nada y se registra en el log lo
que se habría mandado. Eso deja el sistema funcionando en desarrollo y en un
despliegue recién levantado, sin fallar por una credencial que todavía no
existe.
"""

import base64
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date

from app.core.config import settings

logger = logging.getLogger("adecla.correo")

API = "https://api.resend.com/emails"
TIEMPO_LIMITE = 15


class CorreoError(RuntimeError):
    pass


@dataclass
class Adjunto:
    nombre: str
    contenido: bytes
    tipo: str = "application/pdf"


@dataclass
class Mensaje:
    para: str
    asunto: str
    html: str
    # Resend acepta hasta 40 MB por correo contando todo; una proforma pesa
    # unos 80 KB, así que no hay que trocear nada.
    adjuntos: list[Adjunto] = field(default_factory=list)


# --------------------------------------------------------------------------
# Plantilla
# --------------------------------------------------------------------------

# Los correos se ven en clientes que ignoran hojas de estilo externas y buena
# parte de CSS moderno, así que va todo en línea y con tablas. La paleta es la
# misma del sistema; las tipografías caen a las del sistema operativo porque
# Fraunces no se puede cargar de forma fiable en un correo.
PLANTILLA = """\
<!doctype html>
<html lang="es">
<body style="margin:0;padding:0;background:#fcfcf7;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#fcfcf7;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border:1px solid #e9e9e9;border-radius:14px;">
        <tr><td style="padding:28px 32px 0;">
          <img src="{logo}" alt="ADECLA" width="150" style="display:block;border:0;">
        </td></tr>
        <tr><td style="padding:24px 32px 8px;">
          <h1 style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:24px;line-height:1.2;color:#233738;font-weight:600;">{titulo}</h1>
        </td></tr>
        <tr><td style="padding:0 32px 8px;font-family:Helvetica,Arial,sans-serif;font-size:15px;line-height:1.6;color:#233738;">
          {cuerpo}
        </td></tr>
        {boton}
        <tr><td style="padding:24px 32px 28px;border-top:1px solid #e9e9e9;font-family:Helvetica,Arial,sans-serif;font-size:12px;line-height:1.5;color:#5b6b6c;">
          Asociación de Desarrolladores y Constructores de la Altagracia<br>
          Punta Cana, República Dominicana
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""

BOTON = """\
        <tr><td style="padding:16px 32px 8px;">
          <a href="{url}" style="display:inline-block;background:#00776d;color:#fcfcf7;text-decoration:none;padding:12px 22px;border-radius:8px;font-family:Helvetica,Arial,sans-serif;font-size:15px;font-weight:600;">{texto}</a>
        </td></tr>
"""


def armar_html(titulo: str, cuerpo: str, boton: tuple[str, str] | None = None) -> str:
    return PLANTILLA.format(
        logo=f"{settings.FRONTEND_URL.rstrip('/')}/images/adecla-logo.png",
        titulo=titulo,
        cuerpo=cuerpo,
        boton=BOTON.format(url=boton[0], texto=boton[1]) if boton else "",
    )


# --------------------------------------------------------------------------
# Envío
# --------------------------------------------------------------------------


def enviar(mensaje: Mensaje) -> bool:
    """Devuelve True si Resend aceptó el correo.

    Nunca lanza por falta de configuración: un recordatorio que no sale no
    debe tumbar la operación que lo disparó, como aprobar un documento.
    """
    if not settings.correo_configurado:
        logger.info(
            "Correo no enviado (RESEND_API_KEY sin configurar). Para: %s · Asunto: %s%s",
            mensaje.para,
            mensaje.asunto,
            f" · adjuntos: {[a.nombre for a in mensaje.adjuntos]}" if mensaje.adjuntos else "",
        )
        return False

    cuerpo = json.dumps(
        {
            "from": settings.EMAIL_FROM,
            "to": [mensaje.para],
            "subject": mensaje.asunto,
            "html": mensaje.html,
            **({"reply_to": [settings.EMAIL_REPLY_TO]} if settings.EMAIL_REPLY_TO else {}),
            **(
                {
                    "attachments": [
                        {
                            "filename": a.nombre,
                            "content": base64.b64encode(a.contenido).decode("ascii"),
                            "content_type": a.tipo,
                        }
                        for a in mensaje.adjuntos
                    ]
                }
                if mensaje.adjuntos
                else {}
            ),
        }
    ).encode("utf-8")

    peticion = urllib.request.Request(
        API,
        data=cuerpo,
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(peticion, timeout=TIEMPO_LIMITE) as respuesta:
            logger.info("Correo enviado a %s · %s", mensaje.para, mensaje.asunto)
            return respuesta.status < 300
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", "replace")[:300]
        logger.warning("Resend rechazó el correo a %s: %s %s", mensaje.para, exc.code, detalle)
        return False
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("No se pudo contactar con Resend: %s", exc)
        return False


# --------------------------------------------------------------------------
# Correos del sistema
# --------------------------------------------------------------------------


def recordatorio_vencimiento(
    *,
    para: str,
    empresa: str,
    vence: date | None,
    dias: int | None,
    monto: str | None,
    proforma: tuple[str, bytes] | None = None,
    nota: str | None = None,
) -> Mensaje:
    portal = settings.FRONTEND_URL.rstrip("/")

    if dias is not None and dias < 0:
        titulo = "Tu afiliación venció"
        apertura = (
            f"La afiliación de <strong>{empresa}</strong> venció hace {abs(dias)} días."
        )
    elif dias is not None:
        titulo = "Tu afiliación está por vencer"
        apertura = (
            f"La afiliación de <strong>{empresa}</strong> vence en {dias} días"
            f"{f', el {vence:%d/%m/%Y}' if vence else ''}."
        )
    else:
        titulo = "Renovación de tu afiliación"
        apertura = f"Te escribimos sobre la afiliación de <strong>{empresa}</strong>."

    cuota = (
        f"<p style='margin:0 0 12px;'>La cuota de este período es de <strong>{monto}</strong>.</p>"
        if monto
        else ""
    )

    cuerpo = (
        f"<p style='margin:0 0 12px;'>{apertura}</p>"
        f"{cuota}"
        "<p style='margin:0 0 12px;'>Desde el portal puedes descargar la proforma, subir el "
        "soporte de pago y revisar el estado de tus documentos.</p>"
    )

    # Nota que escribe el staff para este envío concreto: acuerdos de pago,
    # aclaraciones, lo que haga falta. Va destacada para que no se pierda.
    if nota:
        cuerpo += (
            "<p style='margin:0 0 12px;padding:12px 14px;background:#eef5f4;"
            f"border-radius:8px;'>{nota}</p>"
        )

    if proforma:
        cuerpo += (
            f"<p style='margin:0 0 12px;'>Va adjunta la proforma "
            f"<strong>{proforma[0]}</strong>, con los datos de la cuenta.</p>"
        )

    return Mensaje(
        para=para,
        asunto=f"{titulo} · {empresa}",
        html=armar_html(titulo, cuerpo, (f"{portal}/portal", "Entrar al portal")),
        adjuntos=[Adjunto(f"{proforma[0]}.pdf", proforma[1])] if proforma else [],
    )


def proforma_emitida(
    *,
    para: str,
    empresa: str,
    numero: str,
    monto: str,
    concepto: str,
    pdf: bytes | None = None,
) -> Mensaje:
    portal = settings.FRONTEND_URL.rstrip("/")
    titulo = "Tu proforma de pago"
    cuerpo = (
        f"<p style='margin:0 0 12px;'>Emitimos la proforma <strong>{numero}</strong> a nombre de "
        f"{empresa} por {concepto.lower()}.</p>"
        f"<p style='margin:0 0 12px;'>Monto a pagar: <strong>{monto}</strong>.</p>"
        "<p style='margin:0 0 12px;'>Ya está disponible en tu portal y va adjunta en PDF, "
        "con los datos de la cuenta para la transferencia.</p>"
        "<p style='margin:0 0 12px;'>Cuando pagues, sube el comprobante desde el portal: "
        "la opción de subir el soporte de pago se habilita con esta proforma.</p>"
    )
    return Mensaje(
        para=para,
        asunto=f"Proforma {numero} · {empresa}",
        html=armar_html(titulo, cuerpo, (f"{portal}/portal/pagos", "Ver mis proformas")),
        adjuntos=[Adjunto(f"{numero}.pdf", pdf)] if pdf else [],
    )


def documento_revisado(
    *, para: str, empresa: str, documento: str, aprobado: bool, motivo: str | None
) -> Mensaje:
    portal = settings.FRONTEND_URL.rstrip("/")

    if aprobado:
        titulo = "Documento aprobado"
        cuerpo = (
            f"<p style='margin:0 0 12px;'>Revisamos <strong>{documento}</strong> de "
            f"{empresa} y quedó aprobado.</p>"
            "<p style='margin:0 0 12px;'>No tienes que hacer nada más con este documento.</p>"
        )
    else:
        titulo = "Documento rechazado"
        cuerpo = (
            f"<p style='margin:0 0 12px;'>Revisamos <strong>{documento}</strong> de "
            f"{empresa} y no lo pudimos aprobar.</p>"
            f"<p style='margin:0 0 12px;padding:12px 14px;background:#f7e9e6;border-radius:8px;'>"
            f"<strong>Motivo:</strong> {motivo or 'sin especificar'}</p>"
            "<p style='margin:0 0 12px;'>Vuelve a subirlo corrigiendo lo indicado y lo revisamos "
            "en un plazo de 3 días laborables.</p>"
        )

    return Mensaje(
        para=para,
        asunto=f"{titulo} · {documento}",
        html=armar_html(titulo, cuerpo, (f"{portal}/portal/documentos", "Ver mis documentos")),
    )


def pago_registrado(
    *, para: str, empresa: str, monto: str, periodo: int | None, proforma: str | None
) -> Mensaje:
    portal = settings.FRONTEND_URL.rstrip("/")
    titulo = "Recibimos tu pago"
    cuerpo = (
        f"<p style='margin:0 0 12px;'>Registramos un pago de <strong>{monto}</strong> a nombre de "
        f"{empresa}{f' por la cuota {periodo}' if periodo else ''}.</p>"
        + (
            f"<p style='margin:0 0 12px;'>Tu proforma es la <strong>{proforma}</strong> y ya puedes "
            "descargarla desde el portal.</p>"
            if proforma
            else ""
        )
    )
    return Mensaje(
        para=para,
        asunto=f"{titulo} · {empresa}",
        html=armar_html(titulo, cuerpo, (f"{portal}/portal/pagos", "Ver mis pagos")),
    )
