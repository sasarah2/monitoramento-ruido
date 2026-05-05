
from flask import Flask, request, jsonify, render_template_string      # Bibliotecas para: receber(ler) dados de chegam, formato de dados, exibir pagina web
from flask_cors import CORS                                            # Permite receber dados externos(Esp32 + Aplicativo)
from supabase import create_client, Client                             # Importa biblioteca propria da Supabase (Banco de dados) - Ferramneta de conexão
from datetime import datetime, timedelta                               # Biblioteca Data e hora + calculos

app = Flask(__name__)
CORS(app)

# Configurações de Nuvem
URL = "https://wcfldifyyntiqvtvkfdk.supabase.co/rest/v1/"            #[ Chaves
KEY = "sb_publishable_E9Kd_3eIElgKbsRUpkQbHw_IMZUlpYr"               #[
supabase: Client = create_client(URL, KEY)                           #Conexão com o banco

#Receber Ruído

@app.route("/api/ruido", methods=["POST"])
def receber_ruido():
    dados = request.get_json()                                       # Json -> Python
    id_dispositivo = dados.get("id_dispositivo")
    
    # 1. Busca qual NOME está ativo para este microfone
    alocacao = supabase.table("alocacoes").select("nome_funcionario").eq("id_dispositivo", id_dispositivo).eq("ativa", True).execute()
    
    # 2. VERIFICAÇÃO: Só continua se houver alguém logado
    if alocacao.data:
        nome_atual = alocacao.data[0]['nome_funcionario']
        
        # 3. Salva a leitura apenas se o funcionário existir
        supabase.table("leituras").insert({
            "id_dispositivo": id_dispositivo,
            "nome_funcionario": nome_atual, 
            "decibeis": dados.get("decibeis")
        }).execute()
        
        return jsonify({"status": "recebido e salvo"})
    else:
        # Se não tiver ninguém, retornamos uma mensagem diferente e NÃO salvamos nada
        return jsonify({"status": "ignorado", "motivo": "nenhum operador ativo"}), 200

#Aplicativo Dados    

@app.route("/api/alocacao", methods=["POST"])
def alocar_funcionario():
    dados = request.get_json()                                         # Json -> Python
    # Pega o nome escrito no aplicativo
    nome_escrito = dados.get("nome_funcionario") 
    id_dispositivo = dados.get("id_dispositivo")

    # 1. Desativa quem estava usando esse microfone antes
    supabase.table("alocacoes").update({"ativa": False}).eq("id_dispositivo", id_dispositivo).execute()
    
    # 2. Salva a nova alocação usando o NOME diretamente
    supabase.table("alocacoes").insert({
        "nome_funcionario": nome_escrito,
        "id_dispositivo": id_dispositivo,
        "id_maquina": dados.get("id_maquina"),
        "ativa": True
    }).execute()
    
    return jsonify({"status": f"O operador {nome_escrito} está ativo!"})
    
# Últimas Leituras Render   

@app.route("/api/ultimas", methods=["GET"])
def ultimas_leituras():
    # Apenas busca os dados para conferência
    res = supabase.table("leituras").select("*").order("id", desc=True).limit(40).execute()
    return jsonify(res.data)
    
#Site Render

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
        <h1>DADOS TÉCNICOS: MICROFONE + APLICATIVO -> BANCO</h1>
        <p>Status: Conexão Ativa | Aguardando dados...</p>
        <table>
            <thead>
                <tr>
                    <th>Data/Hora (Brasília)</th>
                    <th>Dispositivo</th>
                   <th>Operador Ativo</th>
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
                            <td>${d.nome_funcionario || 'Sem Nome'}</td>
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
