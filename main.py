
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
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Monitoramento de Ruído Industrial (NR-15)</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: sans-serif; background: #f4f4f9; padding: 20px; color: #333; }
            .container { max-width: 900px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .status-box { text-align: center; padding: 20px; margin-bottom: 20px; border-radius: 8px; font-size: 24px; font-weight: bold; }
            .normal { background: #d4edda; color: #155724; }
            .alerta { background: #f8d7da; color: #721c24; animation: pisca 1s infinite; }
            @keyframes pisca { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #2c3e50; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Monitoramento em Tempo Real - NR-15/17</h1>
            <div id="status" class="status-box normal">Aguardando dados do sensor...</div>
            <canvas id="graficoRuido" height="100"></canvas>
            <table>
                <thead>
                    <tr>
                        <th>Data/Hora</th>
                        <th>Operador/Setor</th>
                        <th>Nível (dB)</th>
                    </tr>
                </thead>
                <tbody id="tabela-corpo"></tbody>
            </table>
        </div>

        <script>
            const ctx = document.getElementById('graficoRuido').getContext('2d');
            const chart = new Chart(ctx, {
                type: 'line',
                data: { labels: [], datasets: [{ label: 'Decibéis (dB)', data: [], borderColor: '#3498db', fill: true }] },
                options: { scales: { y: { min: 40, max: 110 } } }
            });

            async function atualizar() {
                try {
                    const response = await fetch('/api/ultimas');
                    const dados = await response.json();
                    
                    if (dados.length > 0) {
                        const ultima = dados[0];
                        const statusDiv = document.getElementById('status');
                        statusDiv.innerText = `Nível Atual: ${ultima.decibeis} dB`;
                        
                        if (ultima.decibeis >= 85) {
                            statusDiv.className = 'status-box alerta';
                            statusDiv.innerText += " - LIMITE EXCEDIDO (NR-15)";
                        } else {
                            statusDiv.className = 'status-box normal';
                        }

                        const corpo = document.getElementById('tabela-corpo');
                        corpo.innerHTML = dados.map(d => `
                            <tr>
                                <td>${new Date(d.data_hora).toLocaleString()}</td>
                                <td>${d.operador}</td>
                                <td>${d.decibeis} dB</td>
                            </tr>
                        `).join('');

                        chart.data.labels = dados.map(d => new Date(d.data_hora).toLocaleTimeString()).reverse();
                        chart.data.datasets[0].data = dados.map(d => d.decibeis).reverse();
                        chart.update();
                    }
                } catch (e) { console.error("Erro ao buscar dados", e); }
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
