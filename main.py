
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from supabase import create_client, Client
import os

app = Flask(__name__)
CORS(app)

# Configurações de Nuvem
URL = "SUA_URL_DO_SUPABASE"
KEY = "SUA_CHAVE_ANON_DO_SUPABASE"
supabase: Client = create_client(URL, KEY)

@app.route("/api/ruido", methods=["POST"])
def receber_ruido():
    dados = request.get_json()
    # Enviando para a nuvem
    supabase.table("leituras").insert({
        "id_dispositivo": dados.get("operador"), 
        "decibeis": dados.get("decibeis")
    }).execute()
    return jsonify({"status": "ok"})

@app.route("/api/ultimas", methods=["GET"])
def ultimas_leituras():
    # Buscando da nuvem
    res = supabase.table("leituras").select("*").order("id", desc=True).limit(20).execute()
    # Adaptando para o seu HTML original
    dados_formatados = [
        {"operador": i["id_dispositivo"], "decibeis": i["decibeis"], "data_hora": i["created_at"]} 
        for i in res.data
    ]
    return jsonify(dados_formatados)

@app.route("/")
def pagina():
    # O seu código HTML/JavaScript continua exatamente o mesmo!
    return render_template_string("""...""") 

if __name__ == "__main__":
    # Para o Render, usamos a porta que o sistema deles fornecer
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)