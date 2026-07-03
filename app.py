from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

EVOPAY_API_KEY = "1dec524a-3b3e-429f-8583-99a8f2dafa20"
EVOPAY_URL = "https://pix.evopay.cash/v1/pix/"

# Armazenar transações temporariamente
transacoes = {}

@app.route('/')
def home():
    return jsonify({"status": "EvoPay API Gateway rodando!"})

@app.route('/api/criar_pix', methods=['POST', 'OPTIONS'])
def criar_pix():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        print(f"Dados recebidos: {data}")
        
        valor = data.get('amount')
        
        if not valor:
            return jsonify({'error': 'Valor nao informado'}), 400
        
        valor_centavos = int(float(valor) * 100)
        valor_reais = valor_centavos / 100
        print(f"Valor: R$ {valor_reais:.2f}")
        
        if valor_centavos > 100000:
            return jsonify({'error': 'Valor maximo R$ 1.000,00'}), 400
        
        headers = {
            'API-Key': EVOPAY_API_KEY,
            'Content-Type': 'application/json'
        }
        
        payload = {
            "amount": valor_centavos,
            "callbackUrl": "https://evopay-backend7.onrender.com/webhook",
            "payerName": "Cliente Magnata Store",
            "payerDocument": "12345678909",
            "payerEmail": "cliente@magnata.com",
            "externalReference": f"pedido_{int(valor_reais)}"
        }
        
        print(f"Enviando: {payload}")
        
        response = requests.post(EVOPAY_URL, json=payload, headers=headers, timeout=30)
        print(f"Resposta: {response.status_code} - {response.text}")
        
        data_resp = response.json()
        
        if response.ok and data_resp.get('id'):
            transacoes[data_resp['id']] = {
                'status': 'pending',
                'valor': valor_reais
            }
        
        return jsonify(data_resp), response.status_code
        
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"WEBHOOK RECEBIDO: {data}")
        
        if data.get('status') == 'paid' or data.get('payment_status') == 'paid':
            transaction_id = data.get('id') or data.get('transaction_id')
            if transaction_id and transaction_id in transacoes:
                transacoes[transaction_id]['status'] = 'paid'
                print(f"Pagamento CONFIRMADO: {transaction_id}")
        
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/api/verificar_pix/<transaction_id>', methods=['GET'])
def verificar_pix(transaction_id):
    if transaction_id in transacoes:
        status = transacoes[transaction_id].get('status', 'pending')
        return jsonify({
            'status': status,
            'transaction_id': transaction_id
        })
    
    return jsonify({
        'status': 'pending',
        'transaction_id': transaction_id,
        'message': 'Aguardando pagamento...'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
