import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
PORT = os.getenv("PORT", 5000)

# https://chat-server-6y5c.onrender.com/webhook

WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
PHONE_NUMBER_ID = os.getenv("606444145880553")
ACCESS_TOKEN = "EAAJJvHiFZCysBO3ZBhknHrJuoDOcAZCz1raYTCnKJZAhWxCr4ZB39xIeNaP5xyTrZCfp4ai775N0h4WGUrXguFwIgydDBBuMhEq9PCOx4UUTlkyJ4ianxXSgJRkkiUpKcomWWVOIStADi9yICBp0lG3KcNlgLMiKuctDr2h3MP1WOmSkX4CA8X0nWdUGkcxG7vnwZDZD"

received_messages = []
known_numbers = set()

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello, World!"})

@app.route('/send-message', methods=['POST'])
def send_message():
    data = request.json
    to = data.get('to')
    message = data.get('message')
    image_url = data.get('imageUrl')
    document_url = data.get('documentUrl')

    if not any([message, image_url, document_url]):
        return jsonify({"success": False, "error": "Message, image, or document is required."}), 400

    payload = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": to}
    
    if image_url:
        payload.update({"type": "image", "image": {"link": image_url}})
    elif document_url:
        payload.update({"type": "document", "document": {"link": document_url}})
    else:
        payload.update({"type": "text", "text": {"body": message}})
    
    try:
        response = requests.post(
            f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages",
            json=payload,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
        )
        
        new_message = {"to": to, "text": message, "imageUrl": image_url, "documentUrl": document_url, "timestamp": int(requests.get("https://time.akamai.com").text)}
        received_messages.append(new_message)
        return jsonify({"success": True, "response": response.json()})
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    VERIFY_TOKEN = "desitestt1"
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    
    if mode and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Received WhatsApp Message:", data)
    if data.get("object") == "whatsapp_business_account":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                message = change.get("value", {}).get("messages", [{}])[0]
                if message:
                    from_number = message.get("from")
                    if from_number not in known_numbers:
                        known_numbers.add(from_number)
                        trigger_whatsapp_flow(from_number)
                    received_messages.append({"from": from_number, "message": message})
    return "OK", 200

def trigger_whatsapp_flow(to):
    try:
        payload = {
            "messaging_product": "whatsapp", "to": to, "type": "template",
            "template": {"name": "new_temp", "language": {"code": "en_US"},
                "components": [{"type": "header", "parameters": [{"type": "image", "image": {"link": "https://media.istockphoto.com/id/1280385511/photo/colorful-background.jpg?s=612x612&w=0&k=20&c=kj0PRQlgvWLzA1-1me6iZp5mlwsZhC4QlcvIEb1J1bs="}}]}]}
        }
        response = requests.post(
            f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages",
            json=payload,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
        print("Flow Triggered:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error triggering flow:", str(e))

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify(received_messages)

if __name__ == '__main__':
    app.run(port=PORT, debug=True)
