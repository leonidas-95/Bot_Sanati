import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

# Abrimos la caja fuerte invisible
load_dotenv()

app = Flask(__name__)

# =====================================================
# 🔐 SECCIÓN DE LLAVES SEGURAS (Desde el .env)
# =====================================================
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

# --- WHATSAPP ---
WA_TOKEN = os.environ.get("WA_TOKEN")
WA_PHONE_ID = os.environ.get("WA_PHONE_ID")

# --- INSTAGRAM ---
IG_TOKEN = os.environ.get("IG_TOKEN")
IG_ID = os.environ.get("IG_ID")

# --- SANATI ---
NUMERO_DUENA = os.environ.get("NUMERO_DUENA")

# URLs de envío
URL_WA = f"https://graph.facebook.com/v17.0/{WA_PHONE_ID}/messages"
URL_IG = f"https://graph.instagram.com/v17.0/{IG_ID}/messages"

# Memoria
user_sessions = {}

# --- TEXTOS DEL MENÚ ---
MENSAJE_BIENVENIDA = """
¡Hola! 👋 Soy el asistente virtual de Sanati 🌱

Escribe el número de la opción que buscas:

1️⃣ Sabores
2️⃣ Presentaciones
3️⃣ Envíos
4️⃣ Cómo comprar
5️⃣ Hacer pedido por este medio
6️⃣ Mayoreo / Negocios
7️⃣ Hablar con una persona
"""

# =====================================================
# 📸 FUNCIÓN: ENVIAR IMÁGENES
# =====================================================
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

# =====================================================
# FUNCIONES DE ENVÍO DE TEXTO Y LOGS (CHISMOSO)
# =====================================================
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

# =====================================================
# 🧠 CEREBRO (MENÚ ESTRICTO SIN IA)
# =====================================================
def cerebro_sanati(usuario_id, mensaje_usuario, plataforma):
    # Convertimos a minúsculas para que "HOLA" o "hola" funcionen igual
    mensaje_usuario = str(mensaje_usuario).strip().lower()
    session_key = f"{plataforma}_{usuario_id}"
    
    estado_actual = user_sessions.get(session_key, 'nuevo')
    print(f"⚙️ {plataforma.upper()} | User: {usuario_id} | Estado: {estado_actual} | Dice: {mensaje_usuario}")

    # 1. MODO PAUSADO (HUMAN HANDOFF - Tiene prioridad absoluta)
    if estado_actual == 'pausado':
        if mensaje_usuario == '0':
            user_sessions[session_key] = 'menu'
            responder(usuario_id, MENSAJE_BIENVENIDA, plataforma)
        return # Si está pausado y dice otra cosa, salimos sin hacer ruido
        
    # 2. INTERCEPCIÓN DE SALUDOS Y BOTÓN DE REGRESO GLOBAL (0)
    saludos = ['hola', 'buenas', 'buenos', 'menu', 'menú', 'info', 'empezar']
    if estado_actual == 'nuevo' or mensaje_usuario in saludos or mensaje_usuario == '0':
        user_sessions[session_key] = 'menu'
        responder(usuario_id, MENSAJE_BIENVENIDA, plataforma)
        return

    # 3. NAVEGACIÓN DEL MENÚ (Solo llega aquí si no es 0 ni un saludo)
    if estado_actual == 'menu':
        if mensaje_usuario == '1':
            URL_FOTO_SABORES = "https://i.imgur.com/emCdIVl.jpeg"
            enviar_imagen(usuario_id, URL_FOTO_SABORES, plataforma)
            responder(usuario_id, "Aquí tienes nuestros sabores 🌶️🥕:\n\n🔸 Jícama: Limón, Adobada, Salsas negras, Jalapeño\n🔸 Pepino: Limón, Flamin hot\n🔸 Coliflor: Adobada\n\n(0 para volver)", plataforma)
            user_sessions[session_key] = 'waiting_back'
        
        elif mensaje_usuario == '2':
            responder(usuario_id, "Presentaciones:\n1️⃣ Individual (70g)\n2️⃣ Familiar (500g)\n\nElige una o manda 0 para volver.", plataforma)
            user_sessions[session_key] = 'presentaciones'

        elif mensaje_usuario == '3':
            responder(usuario_id, "Envíos 🚚 a partir de 15 piezas.\nEscribe tu Ciudad y CP:", plataforma)
            user_sessions[session_key] = 'envios'

        elif mensaje_usuario == '4':
            responder(usuario_id, "¿Cuál es tu Ciudad y CP para cotizar?", plataforma)
            user_sessions[session_key] = 'waiting_back'
        
        elif mensaje_usuario == '5':
            responder(usuario_id, "🙌 Para pedir, escribe en un mensaje:\n- Sabores y Cantidad\n- Presentación\n- Dirección de entrega", plataforma)
            user_sessions[session_key] = 'tomando_pedido'

        elif mensaje_usuario == '6':
            responder(usuario_id, "Mayoreo 🏪\nEscribe:\n- Ciudad\n- Tipo de negocio\n- Volumen estimado", plataforma)
            user_sessions[session_key] = 'mayoreo'

        elif mensaje_usuario == '7':
            responder(usuario_id, "Claro 😊 Ya le avisé a un humano. Te atenderán en breve.\n\n🤫 *(Bot en pausa. Para regresar al menú automático en cualquier momento, escribe 0)*", plataforma)
            notificar_duena("SOLICITUD HUMANO", usuario_id, "Quiere hablar con una persona", plataforma)
            user_sessions[session_key] = 'pausado'

        # 🚫 SI ESCRIBE ALGO QUE NO ES UN NÚMERO
        else:
            responder(usuario_id, "Ups, no entendí esa opción 😅.\nPor favor escribe un número del 1 al 7 para navegar, o manda 0 para ver el menú principal.", plataforma)

    elif estado_actual == 'presentaciones':
        if mensaje_usuario == '1':
            responder(usuario_id, "🥡 *Individual (70g)*: Para el antojo. (0 para volver)", plataforma)
        elif mensaje_usuario == '2':
            responder(usuario_id, "📦 *Familiar (500g)*: Para compartir. (0 para volver)", plataforma)
        else:
            responder(usuario_id, "Opción no válida. 1, 2 o manda 0 para volver.", plataforma)

    elif estado_actual in ['envios', 'tomando_pedido', 'mayoreo', 'waiting_back']:
        responder(usuario_id, "¡Gracias! Datos recibidos 📝. Te contactaremos pronto. (Escribe 0 para volver al menú)", plataforma)
        tipo_dato = estado_actual.upper().replace("_", " ")
        notificar_duena(tipo_dato, usuario_id, mensaje_usuario, plataforma)
        user_sessions[session_key] = 'menu'

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
                    if "message" in event and "text" in event["message"]:
                        sender_id = event["sender"]["id"]
                        texto = event["message"]["text"]
                        cerebro_sanati(sender_id, texto, "instagram")
            return jsonify({"status": "ok"}), 200

        elif body.get("object") == "whatsapp_business_account":
            for entry in body["entry"]:
                for change in entry["changes"]:
                    value = change["value"]
                    if "messages" in value:
                        mensaje = value["messages"][0]
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