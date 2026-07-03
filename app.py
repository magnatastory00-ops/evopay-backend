from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

EVOPAY_API_KEY = "1dec524a-3b3e-429f-8583-99a8f2dafa20"
EVOPAY_URL = "https://pix.evopay.cash/v1/pix/"

@app.route('/')
def home():
    return jsonify({"status": "EvoPay API Gateway rodando!", "version": "1.0"})

@app.route('/api/criar_pix', methods=['POST'])
def criar_pix():
    try:
        data = request.json
        print(f"Dados recebidos: {data}")
        
        valor_centavos = data.get('amount')
        
        if not valor_centavos:
            return jsonify({'error': 'Valor nao informado'}), 400
        
        if valor_centavos > 100000:
            return jsonify({
                'error': f'Valor R$ {valor_centavos/100:.2f} nao permitido. Maximo: R$ 1.000,00'
            }), 400
        
        headers = {
            'API-Key': EVOPAY_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {
            "amount": valor_centavos,
            "callbackUrl": "https://magnatastore.netlify.app/",
            "payerName": "Cliente Magnata Store",
            "payerDocument": "12345678909",
            "payerEmail": "cliente@magnata.com",
            "externalReference": f"pedido_{valor_centavos}"
        }
        
        print(f"Enviando para EvoPay: {payload}")
        
        response = requests.post(EVOPAY_URL, json=payload, headers=headers, timeout=30)
        print(f"Resposta EvoPay: {response.status_code} - {response.text}")
        
        return jsonify(response.json()), response.status_code
        
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/verificar_pix/<transaction_id>', methods=['GET'])
def verificar_pix(transaction_id):
    return jsonify({
        'status': 'pending',
        'message': 'Verificacao manual necessaria.',
        'transaction_id': transaction_id
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
