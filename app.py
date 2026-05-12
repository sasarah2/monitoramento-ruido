from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from supabase import create_client, Client
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configurações Supabase
URL = "https://wcfldifyyntiqvtvkfdk.supabase.co"
KEY = "sb_publishable_E9Kd_3eIElgKbsRUpkQbHw_IMZUlpYr"

supabase: Client = create_client(URL, KEY)


@app.route("/")
def pagina():
    return render_template("index.html")


@app.route("/api/ruido", methods=["POST"])
def receber_ruido():
    dados = request.get_json()

    if not dados:
        return jsonify({"status": "erro", "mensagem": "JSON vazio ou inválido"}), 400

    # O ESP32 pode mandar "operador" ou "id_dispositivo"
    id_dispositivo = dados.get("id_dispositivo") or dados.get("operador")
    decibeis = dados.get("decibeis")

    if id_dispositivo is None or decibeis is None:
        return jsonify({
            "status": "erro",
            "mensagem": "Faltando id_dispositivo/operador ou decibeis",
            "dados_recebidos": dados
        }), 400

    try:
        decibeis = float(decibeis)

        # Busca funcionário ativo para esse dispositivo
        alocacao = supabase.table("alocacoes") \
            .select("nome_funcionario") \
            .eq("id_dispositivo", id_dispositivo) \
            .eq("ativa", True) \
            .execute()

        if alocacao.data:
            nome_atual = alocacao.data[0]["nome_funcionario"]
        else:
            nome_atual = f"Operador {id_dispositivo}"

        leitura = {
            "id_dispositivo": id_dispositivo,
            "nome_funcionario": nome_atual,
            "decibeis": decibeis,
            "data_hora": datetime.now().isoformat()
        }

        supabase.table("leituras").insert(leitura).execute()

        return jsonify({
            "status": "recebido e salvo",
            "leitura": leitura
        }), 200

    except Exception as e:
        return jsonify({
            "status": "erro",
            "mensagem": str(e)
        }), 500


@app.route("/api/alocacao", methods=["POST"])
def alocar_funcionario():
    dados = request.get_json()

    nome_escrito = dados.get("nome_funcionario")
    id_dispositivo = dados.get("id_dispositivo")

    if not nome_escrito or not id_dispositivo:
        return jsonify({
            "status": "erro",
            "mensagem": "nome_funcionario e id_dispositivo são obrigatórios"
        }), 400

    supabase.table("alocacoes") \
        .update({"ativa": False}) \
        .eq("id_dispositivo", id_dispositivo) \
        .execute()

    supabase.table("alocacoes").insert({
        "nome_funcionario": nome_escrito,
        "id_dispositivo": id_dispositivo,
        "id_maquina": dados.get("id_maquina"),
        "ativa": True
    }).execute()

    return jsonify({
        "status": f"O operador {nome_escrito} está ativo!"
    }), 200


@app.route("/api/ultimas", methods=["GET"])
def ultimas_leituras():
    try:
        res = supabase.table("leituras") \
            .select("*") \
            .order("id", desc=True) \
            .limit(40) \
            .execute()

        return jsonify(res.data), 200

    except Exception as e:
        return jsonify({
            "status": "erro",
            "mensagem": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)