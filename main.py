
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from supabase import create_client, Client
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Configurações de Nuvem
URL = "https://wcfldifyyntiqvtvkfdk.supabase.co/rest/v1/"
KEY = "sb_publishable_E9Kd_3eIElgKbsRUpkQbHw_IMZUlpYr"
supabase: Client = create_client(URL, KEY)

@app.route("/api/ruido", methods=["POST"])
def receber_ruido():
    dados = request.get_json()
    id_dispositivo = dados.get("id_dispositivo")
    
    # 1. Busca no Supabase quem está com esse microfone agora (alocação ativa)
    alocacao = supabase.table("alocacoes").select("id_funcionario").eq("id_dispositivo", id_dispositivo).eq("ativa", True).execute()
    
    # Se encontrar alguém, pega o ID; se não, fica vazio (None)
    id_func = alocacao.data[0]['id_funcionario'] if alocacao.data else None

    # 2. Salva a leitura já vinculada ao funcionário correto
    supabase.table("leituras").insert({
        "id_dispositivo": id_dispositivo,
        "id_funcionario": id_func, 
        "decibeis": dados.get("decibeis")
    }).execute()
    
    return jsonify({"status": "recebido"})


@app.route("/api/alocacao", methods=["POST"])
def alocar_funcionario():
    dados = request.get_json()
    # Desativa alocações anteriores para esse dispositivo
    supabase.table("alocacoes").update({"ativa": False}).eq("id_dispositivo", dados.get("id_dispositivo")).execute()
    
    # Cria a nova alocação ativa
    supabase.table("alocacoes").insert({
        "id_funcionario": dados.get("id_funcionario"),
        "id_dispositivo": dados.get("id_dispositivo"),
        "id_maquina": dados.get("id_maquina"),
        "ativa": True
    }).execute()
    return jsonify({"status": "Alocação realizada!"})
    

@app.route("/api/ultimas", methods=["GET"])
def ultimas_leituras():
    # Apenas busca os dados para conferência
    res = supabase.table("leituras").select("*").order("id", desc=True).limit(20).execute()
    return jsonify(res.data)

@app.route("/")
def pagina():
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Ponte de Dados - Monitoramento</title>
        <style>
            body { font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; border: 1px solid #333; }
            th, td { padding: 12px; border: 1px solid #333; text-align: left; }
            th { background: #252525; color: #fff; }
            h1 { color: #fff; border-bottom: 1px solid #333; padding-bottom: 10px; }
        </style>
    </head>
    <body>
        <h1>LOGS TÉCNICOS: MICROFONE -> BANCO</h1>
        <p>Status: Conexão Ativa | Aguardando Pacotes...</p>
        <table>
            <thead>
                <tr>
                    <th>Data/Hora (Brasília)</th>
                    <th>Dispositivo</th>
                    <th>ID Funcionário</th>
                    <th>Nível (dB)</th>
                </tr>
            </thead>
            <tbody id="tabela"></tbody>
        </table>
        <script>
            async function atualizar() {
                try {
                    const res = await fetch('/api/ultimas');
                    const dados = await res.json();
                    document.getElementById('tabela').innerHTML = dados.map(d => `
                        <tr>
                            <td>${new Date(d.created_at).toLocaleString('pt-BR')}</td>
                            <td>${d.id_dispositivo || '---'}</td>
                            <td>${d.id_funcionario || 'Sem Operador'}</td>
                            <td>${d.decibeis} dB</td>
                        </tr>
                    `).join('')
                } catch (e) { console.error("Erro na ponte:", e); }
            }
            setInterval(atualizar, 3000);
            atualizar();
        </script>
    </body>
    </html>
    """)
