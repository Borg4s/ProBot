# 📥 Importações
import mercadopago
from utils.database import get_mercadopago_token

# 🏦 Criar Cobrança Pix Direto
def criar_pagamento(nome_produto, preco, user_id, guild_id):
    token = get_mercadopago_token(guild_id)
    if not token:
        raise Exception("Access Token do MercadoPago não configurado para este servidor.")

    sdk = mercadopago.SDK(token)

    preference_data = {
        "transaction_amount": preco,
        "description": nome_produto,
        "payment_method_id": "pix",
        "payer": {
            "email": f"{user_id}@exemplo.com",
            "first_name": "Cliente",
            "last_name": "Discord"
        }
    }

    payment = sdk.payment().create(preference_data)

    qr_code = payment["response"]["point_of_interaction"]["transaction_data"]["qr_code"]
    payment_id = payment["response"]["id"]

    return qr_code, payment_id

# 🏦 Consultar Status do Pagamento
def consultar_pagamento(payment_id, guild_id):
    token = get_mercadopago_token(guild_id)
    if not token:
        raise Exception("Access Token do MercadoPago não configurado para este servidor.")

    sdk = mercadopago.SDK(token)
    payment = sdk.payment().get(payment_id)

    status = payment["response"]["status"]
    return status
