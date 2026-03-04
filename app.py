import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

# caja fuerte
load_dotenv()

app = Flask(__name__)

# SECCIÓN DE LLAVES

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

# Whats
WA_TOKEN = os.environ.get("WA_TOKEN")
WA_PHONE_ID = os.environ.get("WA_PHONE_ID")

# Instagram
IG_TOKEN = os.environ.get("IG_TOKEN")
IG_ID = os.environ.get("IG_ID")

# Sanati
NUMERO_DUENA = os.environ.get("NUMERO_DUENA")

# URLs de envío
URL_WA = f"https://graph.facebook.com/v17.0/{WA_PHONE_ID}/messages"
URL_IG = f"https://graph.instagram.com/v17.0/{IG_ID}/messages"

# Memoria
user_sessions = {}
mensajes_procesados = set() # 🌟 MEMORIA ANTI-DUPLICADOS (La libreta de folios)

# Menú
MENSAJE_BIENVENIDA = """
¡Hola! 💚 Bienvenido a Sanati. ¿Cómo puedo ayudarte hoy?

Escribe el número de la opción que buscas:

1️⃣ Sabores
2️⃣ Presentaciones
3️⃣ Envíos
4️⃣ Cómo comprar
5️⃣ Hacer pedido por este medio
6️⃣ Mayoreo / Negocios
7️⃣ Hablar con una persona
"""

# ENviar imagenes

def enviar_imagen(usuario_id, url_imagen, plataforma):
    if plataforma == "whatsapp":
        headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
        data = {
            "messaging_product": "whatsapp",
            "to": usuario_id,
            "type": "image",
            "image": {"link": url_imagen}
        }
        url_destino = URL_WA
    elif plataforma == "instagram":
        headers = {"Authorization": f"Bearer {IG_TOKEN}", "Content-Type": "application/json"}
        data = {
            "recipient": {"id": usuario_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {"url": url_imagen}
                }
            }
        }
        url_destino = URL_IG

    try:
        r = requests.post(url_destino, json=data, headers=headers)
        if r.status_code != 200:
            print(f"❌ Error enviando IMAGEN en {plataforma}: {r.text}")
        else:
            print(f"📸 Imagen enviada a {usuario_id} por {plataforma}")
    except Exception as e:
        print(f"❌ Error de red enviando IMAGEN: {e}")

# Logs (chismoso)

def enviar_whatsapp(telefono, texto):
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": telefono, "type": "text", "text": {"body": texto}}
    try:
        r = requests.post(URL_WA, json=data, headers=headers)
        if r.status_code != 200:
            print(f"❌ ERROR EXACTO DE META (WA): {r.text}")
        else:
            print(f"✅ Mensaje/Alerta enviada por WA a {telefono}")
    except Exception as e:
        print(f"❌ Error de red WA: {e}")

def enviar_instagram(user_id, texto):
    headers = {"Authorization": f"Bearer {IG_TOKEN}", "Content-Type": "application/json"}
    data = {"recipient": {"id": user_id}, "message": {"text": texto}}
    try:
        r = requests.post(URL_IG, json=data, headers=headers)
        if r.status_code != 200:
            print(f"❌ Error IG: {r.text}")
    except Exception as e:
        print(f"❌ Error enviando IG: {e}")

def responder(usuario_id, texto, plataforma):
    if plataforma == "whatsapp":
        enviar_whatsapp(usuario_id, texto)
    elif plataforma == "instagram":
        enviar_instagram(usuario_id, texto)

def notificar_duena(origen, cliente_id, mensaje, plataforma):
    icono = "🟢" if plataforma == "whatsapp" else "📸"
    texto_duena = (
        f"🚨 *AVISO SANATI ({origen})* 🚨\n\n"
        f"{icono} *Canal:* {plataforma.upper()}\n"
        f"👤 *Cliente ID:* {cliente_id}\n"
        f"📝 *Dijo:* {mensaje}\n\n"
        f"👉 ¡Atiende al cliente en su app!"
    )
    enviar_whatsapp(NUMERO_DUENA, texto_duena)


# Cerebro del bot :)

def cerebro_sanati(usuario_id, mensaje_usuario, plataforma):
    # Convertimos a minúsculas para que "HOLA" o "hola" funcionen igual
    mensaje_usuario = str(mensaje_usuario).strip().lower()
    session_key = f"{plataforma}_{usuario_id}"
    
    estado_actual = user_sessions.get(session_key, 'nuevo')
    print(f"⚙️ {plataforma.upper()} | User: {usuario_id} | Estado: {estado_actual} | Dice: {mensaje_usuario}")

    saludos = ['hola', 'buenas', 'buenos', 'menu', 'menú', 'info', 'empezar']

    # 1. MODO PAUSADO (HUMAN HANDOFF - Tiene prioridad absoluta)
    if estado_actual == 'pausado':
        # Si está pausado, solo despierta con un saludo o con el 0
        if mensaje_usuario == '0' or mensaje_usuario in saludos:
            user_sessions[session_key] = 'menu'
            responder(usuario_id, MENSAJE_BIENVENIDA, plataforma)
        return # Si dice otra cosa ("gracias", "ok"), sigue mudo
        
    # 2. INTERCEPCIÓN DE SALUDOS Y BOTÓN DE REGRESO GLOBAL (0)
    if estado_actual == 'nuevo' or mensaje_usuario in saludos or mensaje_usuario == '0':
        user_sessions[session_key] = 'menu'
        responder(usuario_id, MENSAJE_BIENVENIDA, plataforma)
        return

    # 3. NAVEGACIÓN DEL MENÚ (Solo llega aquí si no es 0 ni un saludo)
    if estado_actual == 'menu':
        if mensaje_usuario == '1':
            URL_FOTO_SABORES = "https://i.imgur.com/emCdIVl.jpeg"
            enviar_imagen(usuario_id, URL_FOTO_SABORES, plataforma)
            # 🌟 TEXTO ACTUALIZADO: Jícama Flamin hot, Emojis cambiados y nuevas instrucciones
            responder(usuario_id, "Aquí tienes nuestros sabores 🌶️🥒:\n\n🔸 Jícama: Limón, Adobada, Salsas negras, Jalapeño, Flamin hot\n🔸 Pepino: Limón, Flamin hot\n🔸 Coliflor: Adobada\n\n(0 para menú principal, 1 para hacer pedido)", plataforma)
            user_sessions[session_key] = 'viendo_sabores'
        
        elif mensaje_usuario == '2':
            responder(usuario_id, "Presentaciones:\n1️⃣ Individual (70g)\n2️⃣ Familiar (500g)\n\nElige una o manda 0 para volver.", plataforma)
            user_sessions[session_key] = 'presentaciones'

        elif mensaje_usuario == '3':
            # 🌟 TEXTO ACTUALIZADO DE ENVÍOS
            responder(usuario_id, "¡Claro! 😊\n\nHacemos envíos a toda la República 🚛 a partir de 15 piezas.\nCompártenos tu código postal y el estado, y con gusto te cotizamos el envío ✨📦", plataforma)
            user_sessions[session_key] = 'envios'

        elif mensaje_usuario == '4':
            responder(usuario_id, "Puedes checar nuestros puntos de venta en el perfil 🤍\nO compártenos tu ciudad y C.P. y te cotizamos venta directa ✨", plataforma)
            user_sessions[session_key] = 'waiting_back'
        
        elif mensaje_usuario == '5':
            URL_FOTO_HACER_PEDIDO = "https://i.imgur.com/3Ow64vk.jpeg"
            enviar_imagen(usuario_id, URL_FOTO_HACER_PEDIDO, plataforma)
            responder(usuario_id, "🙌 Para pedir, escribe en un solo mensaje:\n\n✅ Sabores y Cantidad\n✅ Presentación (Individual o Familiar)\n✅ Dirección de entrega completa (con CP y referencias)\n", plataforma)
            user_sessions[session_key] = 'tomando_pedido'

        elif mensaje_usuario == '6':
            # 🌟 TEXTO ACTUALIZADO DE MAYOREO
            responder(usuario_id, "¡Qué gusto que te interese el mayoreo! 👩🏻‍💻✨\nPara poder enviarte la información adecuada, compártenos por favor:\n\n• Ciudad\n• Tipo de negocio\n• Volumen estimado\n• número de WhatsApp\n\nCon eso te damos todos los detalles por WhatsApp 💚", plataforma)
            user_sessions[session_key] = 'mayoreo'

        elif mensaje_usuario == '7':
            # 🌟 TEXTO ACTUALIZADO DE HUMANO
            responder(usuario_id, "¡Gracias por tu mensaje! 🙌\nEn un momento alguien del equipo te atiende personalmente 💚", plataforma)
            notificar_duena("SOLICITUD HUMANO", usuario_id, "Quiere hablar con una persona", plataforma)
            user_sessions[session_key] = 'pausado'

        # 🚫 SI ESCRIBE ALGO QUE NO ES UN NÚMERO
        else:
            responder(usuario_id, "Perdón, no entendí esa opción 😅.\nPor favor escribe un número del 1 al 7 para navegar, o manda 0 para ver el menú principal.", plataforma)

    # 🌟 NUEVA LÓGICA: SI ESTÁ VIENDO LOS SABORES
    elif estado_actual == 'viendo_sabores':
        if mensaje_usuario == '1':
            # Funciona exactamente igual que si hubiera presionado 5 en el menú principal
            URL_FOTO_HACER_PEDIDO = "https://i.imgur.com/3Ow64vk.jpeg"
            enviar_imagen(usuario_id, URL_FOTO_HACER_PEDIDO, plataforma)
            responder(usuario_id, "🙌 Para pedir, escribe en un solo mensaje:\n\n✅ Sabores y Cantidad\n✅ Presentación (Individual o Familiar)\n✅ Dirección de entrega completa (con CP y referencias)\n", plataforma)
            user_sessions[session_key] = 'tomando_pedido'
        else:
            # Si escribe otra cosa, asumimos que está pasando sus datos y lo pausamos
            responder(usuario_id, "Perfecto, danos unos minutos 🙌\nEn breve te enviamos la información completa 🤩", plataforma)
            notificar_duena("DATOS/PEDIDO", usuario_id, mensaje_usuario, plataforma)
            user_sessions[session_key] = 'pausado'

    elif estado_actual == 'presentaciones':
        if mensaje_usuario == '1':
            responder(usuario_id, "🥡 *Individual (70g)*: Para el antojo. (0 para volver)", plataforma)
        elif mensaje_usuario == '2':
            responder(usuario_id, "📦 *Familiar (500g)*: Para compartir. (0 para volver)", plataforma)
        else:
            responder(usuario_id, "Opción no válida. 1, 2 o manda 0 para volver.", plataforma)

    elif estado_actual in ['envios', 'tomando_pedido', 'mayoreo', 'waiting_back']:
        # 🌟 TEXTO ACTUALIZADO DE AUTO-PAUSA AL RECIBIR DATOS DEL CLIENTE
        responder(usuario_id, "Perfecto, danos unos minutos 🙌\nEn breve te enviamos la información completa 🤩", plataforma)
        tipo_dato = estado_actual.upper().replace("_", " ")
        notificar_duena(tipo_dato, usuario_id, mensaje_usuario, plataforma)
        # Aquí el bot se pone en silencio automáticamente
        user_sessions[session_key] = 'pausado'

    else:
        user_sessions[session_key] = 'menu'
        responder(usuario_id, MENSAJE_BIENVENIDA, plataforma)

# =====================================================
# RUTAS FLASK
# =====================================================
@app.route("/webhook", methods=["GET"])
def verificar_token():
    token = request.args.get("hub.verify_token")
    if token == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Error Token", 403

@app.route("/webhook", methods=["POST"])
def recibir_eventos():
    try:
        body = request.json
        if body.get("object") == "instagram":
            for entry in body["entry"]:
                for event in entry.get("messaging", []):
                    # 🛑 Ignorar mensajes de la cuenta propia (eco) para evitar bucles
                    if "message" in event and event["message"].get("is_echo"):
                        continue
                        
                    if "message" in event and "text" in event["message"]:
                        # 🌟 FILTRO ANTI-DUPLICADOS INSTAGRAM
                        msg_id = event["message"].get("mid")
                        if msg_id in mensajes_procesados:
                            continue # Ya lo vimos, lo ignoramos
                        if msg_id:
                            mensajes_procesados.add(msg_id)
                            
                        sender_id = str(event["sender"]["id"])
                        
                        # Doble candado para ignorar a la dueña
                        if sender_id == str(IG_ID):
                            continue
                            
                        texto = event["message"]["text"]
                        cerebro_sanati(sender_id, texto, "instagram")
            return jsonify({"status": "ok"}), 200

        elif body.get("object") == "whatsapp_business_account":
            for entry in body["entry"]:
                for change in entry["changes"]:
                    value = change["value"]
                    if "messages" in value:
                        mensaje = value["messages"][0]
                        
                        # 🌟 FILTRO ANTI-DUPLICADOS WHATSAPP
                        msg_id = mensaje.get("id")
                        if msg_id in mensajes_procesados:
                            continue # Ya lo vimos, lo ignoramos
                        if msg_id:
                            mensajes_procesados.add(msg_id)
                            
                        telefono = mensaje["from"]
                        if telefono.startswith("521") and len(telefono) == 13:
                            telefono = telefono.replace("521", "52", 1)
                        if "1555" in telefono: return jsonify({"status": "ignored"}), 200
                        if "text" in mensaje:
                            texto = mensaje["text"]["body"]
                            cerebro_sanati(telefono, texto, "whatsapp")
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"status": "unknown"}), 200
    except Exception as e:
        print(f"⚠️ Error general webhook: {e}")
        return jsonify({"status": "error"}), 200

if __name__ == "__main__":
    app.run(port=8000, debug=True)