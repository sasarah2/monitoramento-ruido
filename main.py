
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from supabase import create_client, Client
import os

app = Flask(__name__)
CORS(app)

# Configurações de Nuvem
URL = "https://wcfldifyyntiqvtvkfdk.supabase.co/rest/v1/"
KEY = "sb_publishable_E9Kd_3eIElgKbsRUpkQbHw_IMZUlpYr"
supabase: Client = create_client(URL, KEY)

@app.route("/api/ruido", methods=["POST"])
def receber_ruido():
    dados = request.get_json()
    # Pega o dado do microfone e joga no banco
    supabase.table("leituras").insert({
        "id_dispositivo": dados.get("operador", "Sensor_01"), 
        "decibeis": dados.get("decibeis")
    }).execute()
    return jsonify({"status": "recebido"})

@app.route("/api/ultimas", methods=["GET"])
def ultimas_leituras():
    # Apenas busca os dados para conferência
    res = supabase.table("leituras").select("*").order("id", desc=True).limit(20).execute()
    return jsonify(res.data)

@app.route("/")
def pagina():
    # Página técnica simples para ver se os dados estão chegando
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Logs de Monitoramento</title>
        <style>
            body { font-family: monospace; background: #222; color: #0f0; padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; border: 1px solid #444; }
            th, td { padding: 10px; border: 1px solid #444; text-align: left; }
            th { background: #333; }
            h1 { color: #fff; }
        </style>
    </head>
    <body>
        <h1>Ponte de Dados: Microfone -> Banco</h1>
        <p>Status: Servidor Operacional (Aguardando entrada...)</p>
        <table>
            <thead>
                <tr>
                    <th>Data/Hora</th>
                    <th>Valor Capturado (dB)</th>
                </tr>
            </thead>
            <tbody id="tabela"></tbody>
        </table>
        <script>
            async function atualizar() {
                const res = await fetch('/api/ultimas');
                const dados = await res.json();
                document.getElementById('tabela').innerHTML = dados.map(d => `
                    <tr>
                        <td>${d.created_at}</td>
                        <td>${d.decibeis} dB</td>
                    </tr>
                `).join('');
            }
            setInterval(atualizar, 3000);
            atualizar();
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
