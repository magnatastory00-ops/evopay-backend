async function gerarPixEvopay() {
    if (carrinho.length === 0) {
        alert('Carrinho vazio!');
        return;
    }

    const total = calcularTotal();
    
    // 🔥 VALIDAÇÃO: Limite de R$ 1.000
    if (total > 1000) {
        document.getElementById('pagamentoConteudo').innerHTML = `
            <div style="background:rgba(255,170,68,0.1);border:1px solid #ffaa44;padding:15px;border-radius:10px;margin:10px 0">
                ⚠️ <strong>Valor muito alto!</strong> O valor máximo por transação é R$ 1.000.<br><br>
                Seu total é <strong>R$ ${total.toFixed(2)}</strong>.<br>
                <span style="color:#ffaa44;">💡 Divida sua compra em várias de até R$ 1.000.</span>
            </div>
            <button class="btn-finalizar" onclick="fecharModal('modalPagamento')">Fechar</button>
        `;
        abrirModal('modalPagamento');
        return;
    }

    // 🔥 CORREÇÃO: Envia o valor EM CENTAVOS (multiplica por 100)
    const valorCentavos = Math.round(total * 100);

    document.getElementById('pagamentoConteudo').innerHTML = '<div style="text-align:center;padding:30px">⏳ Gerando PIX...</div>';
    abrirModal('modalPagamento');

    try {
        const response = await fetch(`${BACKEND_URL}/api/criar_pix`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                amount: valorCentavos  // 🔥 JÁ EM CENTAVOS
            })
        });

        const data = await response.json();

        if (response.ok && data.id) {
            const qrCode = data.pix_qr_code || data.qr_code || '';
            const codigoPix = data.pix_code || data.brcode || data.pix_qr_code || qrCode;

            document.getElementById('pagamentoConteudo').innerHTML = `
                <div class="qr-code">
                    <img src="${qrCode || `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(codigoPix)}`}" alt="QR Code PIX">
                </div>
                <div class="pix-code">
                    <p>Código PIX:</p>
                    <div class="codigo" id="codigoPix">${codigoPix}</div>
                    <button class="copiar-btn" onclick="copiarPix()">📋 Copiar Código</button>
                </div>
                <div style="background:rgba(0,255,136,0.1);border:1px solid #00ff88;padding:10px;border-radius:8px;margin:10px 0">
                    ✅ Pagamento gerado com sucesso!<br>
                    <small>Valor: R$ ${total.toFixed(2)}</small><br>
                    <small>ID: ${data.id}</small>
                </div>
                <button class="btn-finalizar" onclick="verificarPagamentoEvopay('${data.id}')">
                    ✅ JÁ PAGUEI - CONFIRMAR
                </button>
            `;
        } else {
            throw new Error(data.message || data.error || 'Erro ao gerar PIX');
        }
    } catch (error) {
        document.getElementById('pagamentoConteudo').innerHTML = `
            <div style="background:rgba(255,68,68,0.1);border:1px solid #ff4444;padding:10px;border-radius:8px;margin:10px 0">
                ❌ Erro: ${error.message}
            </div>
            <button class="btn-finalizar" onclick="gerarPixEvopay()">
                🔄 Tentar Novamente
            </button>
        `;
    }
}
