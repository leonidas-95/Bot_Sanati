import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests
import redis

# caja fuerte
load_dotenv()

app = Flask(__name__)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

#Whats
WA_TOKEN = os.environ.get("WA_TOKEN")
WA_PHONE_ID = os.environ.get("WA_PHONE_ID")

#Instagram
IG_TOKEN = os.environ.get("IG_TOKEN")
IG_ID = os.environ.get("IG_ID")

# Messenger
FB_TOKEN = os.environ.get("FB_TOKEN")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")

# Sanati
NUMERO_DUENA = os.environ.get("NUMERO_DUENA")

# URLs de envío
URL_WA = f"https://graph.facebook.com/v17.0/{WA_PHONE_ID}/messages"
URL_IG = f"https://graph.instagram.com/v17.0/{IG_ID}/messages"
URL_FB = f"https://graph.facebook.com/v17.0/{FB_PAGE_ID}/messages" # NUEVO

#Conexión a Redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

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

Más información en nuestro WhatsApp o correo del perfil 💛✨

Y de pasada... danos follow 👀
"""

# Enviar imagenes
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
    elif plataforma in ["instagram", "messenger"]: 
        token_usar = IG_TOKEN if plataforma == "instagram" else FB_TOKEN
        headers = {"Authorization": f"Bearer {token_usar}", "Content-Type": "application/json"}
        data = {
            "recipient": {"id": usuario_id},
            "message": {
                "attachment": {
                    "type": "image",
                    "payload": {"url": url_imagen}
                }
            }
        }
        url_destino = URL_IG if plataforma == "instagram" else URL_FB

    try:
        r = requests.post(url_destino, json=data, headers=headers)
        if r.status_code != 200:
            print(f"Error enviando imagen en {plataforma}: {r.text}")
        else:
            print(f"Imagen enviada a {usuario_id} por {plataforma}")
    except Exception as e:
        print(f"Error de red enviando imagen: {e}")

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

def enviar_messenger(user_id, texto):
    headers = {"Authorization": f"Bearer {FB_TOKEN}", "Content-Type": "application/json"}
    data = {"recipient": {"id": user_id}, "message": {"text": texto}}
    try:
        r = requests.post(URL_FB, json=data, headers=headers)
        if r.status_code != 200:
            print(f"❌ Error FB Messenger: {r.text}")
    except Exception as e:
        print(f"❌ Error enviando FB Messenger: {e}")

def responder(usuario_id, texto, plataforma):
    if plataforma == "whatsapp":
        enviar_whatsapp(usuario_id, texto)
    elif plataforma == "instagram":
        enviar_instagram(usuario_id, texto)
    elif plataforma == "messenger": # NUEVO
        enviar_messenger(usuario_id, texto)


def notificar_duena(origen, cliente_id, mensaje, plataforma):
    
    mensaje_corto = str(mensaje)[:60] + "..." if len(str(mensaje)) > 60 else str(mensaje)
    
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    data = {
        "messaging_product": "whatsapp",
        "to": NUMERO_DUENA,
        "type": "template",
        "template": {
            "name": "alerta_sanati", 
            "language": { "code": "es_MX" },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        { "type": "text", "text": str(plataforma).upper() }, 
                        { "type": "text", "text": str(cliente_id) },        
                        { "type": "text", "text": mensaje_corto }            
                    ]
                }
            ]
        }
    }
    try:
        r = requests.post(URL_WA, json=data, headers=headers)
        if r.status_code != 200:
            print(f"Error enviando plantilla a la dueña: {r.text}")
        else:
            print(f"Alerta segura enviada a la dueña")
    except Exception as e:
        print(f"Error de red en alerta: {e}")

# Cerebro del bot :)
def cerebro_sanati(usuario_id, mensaje_usuario, plataforma):
    mensaje_usuario = str(mensaje_usuario).strip().lower()
    
    if str(usuario_id) == str(NUMERO_DUENA) and mensaje_usuario.startswith("/reanudar"):
        partes = mensaje_usuario.split(" ")
        if len(partes) == 2:
            cliente_pausado = partes[1]
            key_borrar = f"whatsapp_{cliente_pausado}"
            redis_client.delete(key_borrar)
            responder(NUMERO_DUENA, f"✅ Bot reactivado para el cliente {cliente_pausado}", "whatsapp")
        else:
            responder(NUMERO_DUENA, "❌ Formato incorrecto. Usa: /reanudar 52xxxxxxxxxx", "whatsapp")
        return 

    session_key = f"{plataforma}_{usuario_id}"
    estado_actual = redis_client.get(session_key) or 'nuevo'
    
    print(f"⚙️ {plataforma.upper()} | User: {usuario_id} | Estado: {estado_actual} | Dice: {mensaje_usuario}")

    palabras_clave = [
        'hola', 'buenas', 'buenos', 'info', 'empezar', 'precio', 'precios', 'comprar', 'información', 'informacion',
        'ayuda', 'duda', 'catalogo', 'catálogo', 'costo', 'sabores'
    ]
    
    contiene_saludo = any(palabra in mensaje_usuario for palabra in palabras_clave)

    # Human handoff
    if estado_actual == 'pausado':
        if mensaje_usuario == '0' or mensaje_usuario == 'menu' or mensaje_usuario == 'menú':
            redis_client.set(session_key, 'menu', ex=86400)
            responder(usuario_id, MENSAJE_BIENVENIDA, plataforma)
        return 
   
    palabras_cortesia = ['gracias', 'ok', 'vale', 'perfecto', 'listo', 'bye', 'adiós', 'adios', 'va', 'vaa', 'muchas gracias', 'vaaa']
    if estado_actual == 'nuevo' and not contiene_saludo:
        if any(palabra in mensaje_usuario for palabra in palabras_cortesia) and len(mensaje_usuario) < 45:
            print("Bot silencioso: El cliente solo dijo gracias/ok.")
            return 
        
    if estado_actual == 'nuevo' or contiene_saludo or mensaje_usuario == '0':
        redis_client.set(session_key, 'menu', ex=86400)
        responder(usuario_id, MENSAJE_BIENVENIDA, plataforma)
        return

    if estado_actual == 'menu':
        if mensaje_usuario == '1':
            URL_FOTO_SABORES = "https://i.imgur.com/emCdIVl.jpeg"
            enviar_imagen(usuario_id, URL_FOTO_SABORES, plataforma)
            responder(usuario_id, "Aquí tienes nuestros sabores 🌶️🥒:\n\n🔸 Jícama: Limón, Adobada, Salsas negras, Jalapeño, Flamin hot\n🔸 Pepino: Limón, Flamin hot\n🔸 Coliflor: Adobada\n\n(0 para menú principal, 1 para hacer pedido)", plataforma)
            redis_client.set(session_key, 'viendo_sabores', ex=86400)
        
        elif mensaje_usuario == '2':
            responder(usuario_id, "Presentaciones:\n1️⃣ Individual (70g)\n2️⃣ Familiar (500g)\n\nElige una o manda 0 para volver.", plataforma)
            redis_client.set(session_key, 'presentaciones', ex=86400)

        elif mensaje_usuario == '3':
            responder(usuario_id, "¡Claro! 😊\n\nHacemos envíos a toda la República 🚛 a partir de 15 piezas.\nCompártenos tu código postal y el estado, y con gusto te cotizamos el envío ✨📦", plataforma)
            redis_client.set(session_key, 'envios', ex=86400)

        elif mensaje_usuario == '4':
            responder(usuario_id, "Puedes checar nuestros puntos de venta en el perfil 🤍\nO compártenos tu ciudad y C.P. y te cotizamos venta directa ✨", plataforma)
            redis_client.set(session_key, 'waiting_back', ex=86400)
        
        elif mensaje_usuario == '5':
            URL_FOTO_HACER_PEDIDO = "https://i.imgur.com/3Ow64vk.jpeg"
            enviar_imagen(usuario_id, URL_FOTO_HACER_PEDIDO, plataforma)
            responder(usuario_id, "🙌 Para pedir, escribe en un solo mensaje:\n\n✅ Sabores y Cantidad\n✅ Presentación (Individual o Familiar)\n✅ Dirección de entrega completa (con CP y referencias)\n", plataforma)
            redis_client.set(session_key, 'tomando_pedido', ex=86400)

        elif mensaje_usuario == '6':
            responder(usuario_id, "¡Qué gusto que te interese el mayoreo! 🏪✨\nPara poder enviarte la información adecuada, compártenos por favor:\n\n• Ciudad\n• Tipo de negocio\n• Volumen estimado\n• número de WhatsApp\n\nCon eso te damos todos los detalles por WhatsApp 💚", plataforma)
            redis_client.set(session_key, 'mayoreo', ex=86400)

        else:
            responder(usuario_id, "Perdón, no entendí esa opción 😅.\nPor favor escribe un número del 1 al 6 para navegar, o manda 0 para ver el menú principal.", plataforma)

    elif estado_actual == 'viendo_sabores':
        if mensaje_usuario == '1':
            URL_FOTO_HACER_PEDIDO = "https://i.imgur.com/3Ow64vk.jpeg"
            enviar_imagen(usuario_id, URL_FOTO_HACER_PEDIDO, plataforma)
            responder(usuario_id, "🙌 Para pedir, escribe en un solo mensaje:\n\n✅ Sabores y Cantidad\n✅ Presentación (Individual o Familiar)\n✅ Dirección de entrega completa (con CP y referencias)\n", plataforma)
            redis_client.set(session_key, 'tomando_pedido', ex=86400)
        else:
            responder(usuario_id, "Perfecto, danos unos minutos 🙌\nEn breve te enviamos la información completa 🤩", plataforma)
            notificar_duena("DATOS/PEDIDO", usuario_id, mensaje_usuario, plataforma)
            redis_client.set(session_key, 'pausado', ex=7200)

    elif estado_actual == 'presentaciones':
        if mensaje_usuario == '1':
            responder(usuario_id, "🥡 *Individual (70g)*: Para el antojo. (0 para volver)", plataforma)
        elif mensaje_usuario == '2':
            responder(usuario_id, "📦 *Familiar (500g)*: Para compartir. (0 para volver)", plataforma)
        else:
            responder(usuario_id, "Opción no válida. 1, 2 o manda 0 para volver.", plataforma)

    elif estado_actual in ['envios', 'tomando_pedido', 'mayoreo', 'waiting_back']:
        responder(usuario_id, "Perfecto, danos unos minutos 🙌\nEn breve te enviamos la información completa 🤩", plataforma)
        tipo_dato = estado_actual.upper().replace("_", " ")
        notificar_duena(tipo_dato, usuario_id, mensaje_usuario, plataforma)
        redis_client.set(session_key, 'pausado', ex=7200)

    else:
        redis_client.set(session_key, 'menu', ex=86400)
        responder(usuario_id, MENSAJE_BIENVENIDA, plataforma)

# Rutas Flask
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
        print(f"📦 LLEGÓ ALGO A RENDER: {body}")
        
        #Instagram
        if body.get("object") == "instagram":
            for entry in body["entry"]:
                for event in entry.get("messaging", []):
                    if "message" in event:
                        es_eco = event["message"].get("is_echo", False)
                        sender_id = str(event.get("sender", {}).get("id", ""))
                        
                        if es_eco or sender_id == str(IG_ID):
                            texto_duena = event["message"].get("text", "")
                            if texto_duena:
                                texto_duena_lower = texto_duena.lower()
                                cliente_id = str(event.get("recipient", {}).get("id", ""))
                                
                                if "hola buen día" in texto_duena_lower or "hola buen dia" in texto_duena_lower:
                                    redis_client.set(f"instagram_{cliente_id}", 'pausado', ex=7200)
                                    print(f"BOT IG APAGADO PARA {cliente_id}")
                                
                                elif "quedo a tus órdenes" in texto_duena_lower and cliente_id:
                                    redis_client.delete(f"instagram_{cliente_id}") 
                                    print(f"BOT IG ENCENDIDO PARA {cliente_id}")
                            continue 
                            
                        if "text" in event["message"]:
                            msg_id = event["message"].get("mid")
                            if msg_id:
                                if redis_client.get(f"msg_{msg_id}"): continue
                                redis_client.set(f"msg_{msg_id}", "1", ex=3600)
                                
                            texto = event["message"]["text"]
                            cerebro_sanati(sender_id, texto, "instagram")
            return jsonify({"status": "ok"}), 200
            
        #Messenger
        elif body.get("object") == "page":
            for entry in body["entry"]:
                for event in entry.get("messaging", []):
                    if "message" in event:
                        es_eco = event["message"].get("is_echo", False)
                        sender_id = str(event.get("sender", {}).get("id", ""))
                        
                        if es_eco or sender_id == str(FB_PAGE_ID):
                            texto_duena = event["message"].get("text", "")
                            if texto_duena:
                                texto_duena_lower = texto_duena.lower()
                                cliente_id = str(event.get("recipient", {}).get("id", ""))
                                
                                if "hola buen día" in texto_duena_lower or "hola buen dia" in texto_duena_lower:
                                    redis_client.set(f"messenger_{cliente_id}", 'pausado', ex=7200)
                                    print(f"BOT FB APAGADO PARA {cliente_id}")
                                
                                elif "quedo a tus órdenes" in texto_duena_lower and cliente_id:
                                    redis_client.delete(f"messenger_{cliente_id}") 
                                    print(f"BOT FB ENCENDIDO PARA {cliente_id}")
                            continue 
                            
                        if "text" in event["message"]:
                            msg_id = event["message"].get("mid")
                            if msg_id:
                                if redis_client.get(f"msg_{msg_id}"): continue
                                redis_client.set(f"msg_{msg_id}", "1", ex=3600)
                                
                            texto = event["message"]["text"]
                            cerebro_sanati(sender_id, texto, "messenger")
            return jsonify({"status": "ok"}), 200

        #Whatsapp
        elif body.get("object") == "whatsapp_business_account":
            for entry in body["entry"]:
                for change in entry["changes"]:
                    value = change["value"]
                    if "messages" in value:
                        mensaje = value["messages"][0]
                        
                        msg_id = mensaje.get("id")
                        if msg_id:
                            if redis_client.get(f"msg_{msg_id}"): continue
                            redis_client.set(f"msg_{msg_id}", "1", ex=3600)
                            
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