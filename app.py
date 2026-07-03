from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import json
import time

app = Flask(__name__)
CORS(app)

EVOPAY_API_KEY = "1dec524a-3b3e-429f-8583-99a8f2dafa20"
EVOPAY_URL = "https://pix.evopay.cash/v1/pix/"

# Armazenar transações
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
        
        valor = float(valor)
        valor_centavos = int(valor * 100)
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
            "callbackUrl": "https://evopay-backend.onrender.com/webhook",
            "payerName": "Cliente Magnata Store",
            "payerDocument": "12345678909",
            "payerEmail": "cliente@magnata.com",
            "externalReference": f"pedido_{int(valor_reais)}"
        }
        
        print(f"Enviando para EvoPay: {payload}")
        
        response = requests.post(EVOPAY_URL, json=payload, headers=headers, timeout=30)
        print(f"Status EvoPay: {response.status_code}")
        print(f"Resposta EvoPay (TEXTO): {response.text}")
        
        data_resp = response.json()
        print(f"Resposta EvoPay (JSON): {json.dumps(data_resp, indent=2)}")
        
        # 🔥 TENTA PEGAR O QR CODE EM VÁRIOS LUGARES
        qr_code = ''
        codigo_pix = ''
        
        # Verifica se tem pix dentro da resposta
        if 'pix' in data_resp:
            pix = data_resp['pix']
            qr_code = pix.get('pix_qr_code', '')
            codigo_pix = pix.get('pix_code', '')
            print(f"PIX encontrado: QR={qr_code[:50]}... CODIGO={codigo_pix[:50]}...")
        else:
            # Tenta pegar diretamente
            qr_code = data_resp.get('pix_qr_code', '') or data_resp.get('qr_code', '') or data_resp.get('qrCode', '')
            codigo_pix = data_resp.get('pix_code', '') or data_resp.get('brcode', '') or data_resp.get('pix', '')
            print(f"QR direto: {qr_code[:50]}... CODIGO direto: {codigo_pix[:50]}...")
        
        # 🔥 SE NÃO ACHOU, USA O QR CODE COMO CÓDIGO (FALLBACK)
        if not codigo_pix and qr_code:
            codigo_pix = qr_code
            print("Usando QR Code como código PIX (fallback)")
        
        # 🔥 SE AINDA NÃO ACHOU, GERA UM QR CODE SIMULADO
        if not qr_code and codigo_pix:
            qr_code = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={codigo_pix}"
            print("QR Code gerado via API externa")
        
        transaction_id = data_resp.get('id')
        
        if response.ok and transaction_id:
            transacoes[transaction_id] = {
                'status': 'pending',
                'valor': valor_reais,
                'qr_code': qr_code,
                'codigo_pix': codigo_pix,
                'timestamp': time.time()
            }
            print(f"✅ Transação salva: {transaction_id}")
            print(f"📊 Total de transações: {len(transacoes)}")
        
        # 🔥 ADICIONA OS DADOS NA RESPOSTA
        data_resp['qr_code'] = qr_code
        data_resp['codigo_pix'] = codigo_pix
        
        return jsonify(data_resp), response.status_code
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return jsonify({'error': str(e)}), 500

# 🔥 WEBHOOK
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"📥 WEBHOOK RECEBIDO: {data}")
        
        status = data.get('status') or data.get('payment_status') or data.get('state')
        transaction_id = data.get('id') or data.get('transaction_id') or data.get('externalReference')
        
        print(f"Status: {status}, ID: {transaction_id}")
        
        if status in ['paid', 'confirmed', 'approved']:
            if transaction_id:
                if transaction_id in transacoes:
                    transacoes[transaction_id]['status'] = 'paid'
                    print(f"✅ PAGAMENTO CONFIRMADO: {transaction_id}")
                else:
                    transacoes[transaction_id] = {
                        'status': 'paid',
                        'valor': 0,
                        'qr_code': '',
                        'codigo_pix': '',
                        'timestamp': time.time()
                    }
                    print(f"✅ Nova transação confirmada via webhook: {transaction_id}")
        
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/api/verificar_pix/<transaction_id>', methods=['GET'])
def verificar_pix(transaction_id):
    print(f"🔍 Verificando transação: {transaction_id}")
    print(f"📊 Transações disponíveis: {list(transacoes.keys())}")
    
    if transaction_id in transacoes:
        dados = transacoes[transaction_id]
        status = dados.get('status', 'pending')
        print(f"📌 Status: {status}")
        return jsonify({
            'status': status,
            'transaction_id': transaction_id,
            'qr_code': dados.get('qr_code', ''),
            'codigo_pix': dados.get('codigo_pix', ''),
            'valor': dados.get('valor', 0)
        })
    
    return jsonify({
        'status': 'pending',
        'transaction_id': transaction_id,
        'message': 'Transação não encontrada. Aguarde alguns segundos.'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
