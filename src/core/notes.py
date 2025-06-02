from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
import os
import json
from dotenv import load_dotenv
from src.prompts import *
from datetime import datetime

# 🗂️ Caminho do arquivo JSON da transcrição
#caminho_arquivo = "src\\03. transcrições\\Plataforma_Finclass\\01. Como funciona a Finclass - 2025-05-12 15-34-07.json"

def gerar_nota_md(
    caminho_arquivo: str,
    prompt_task: str,
    area: str = None,
    tags_adicionais: list = None,
):
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        return
    
    if os.path.getsize(caminho_arquivo) == 0:
        print(f"⚠️ Arquivo vazio: {caminho_arquivo}")
        return

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        try:
            dados_transcricao = json.load(f)
        except json.JSONDecodeError:
            print(f"🚫 Erro ao ler JSON: {caminho_arquivo}")
            return
    
    # 📥 Carrega o JSON
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        dados_transcricao = json.load(f)

    # 🔎 Extrai a transcrição completa
    transcricao = dados_transcricao.get("text", "")

    # 🔍 Extrai metadados do arquivo
    partes = caminho_arquivo.split("\\")
    curso = partes[-2] if len(partes) >= 2 else partes[-1]
    titulo_aula = caminho_arquivo.split("\\")[-1].split(" - ")[0]
    data_aula_original = caminho_arquivo.split("/")[-1].split(" - ")[1].split(".")[0]
    data_aula = datetime.strptime(data_aula_original, "%Y-%m-%d %H-%M-%S").strftime("%d/%m/%Y %H:%M:%S")

    # 🕓 Duração
    duracao_segundos = dados_transcricao.get("duration", 0)
    horas = int(duracao_segundos // 3600)
    minutos = int((duracao_segundos % 3600) // 60)
    segundos = int(duracao_segundos % 60)
    duracao_formatada = f"{horas}h{minutos:02d}m{segundos:02d}s"

    # 🏷️ Tags
    if tags_adicionais is None:
        tags_adicionais = []
    tags = tags_adicionais
    tags_md = "\n    - ".join(tags)

    # 🗂️ Cabeçalho YAML
    dados_aula = f"""---
curso: "[[{curso}]]"
time: {duracao_formatada}
Área: 
    - {area}
tags: 
    - {tags_md}
data_aula: {data_aula}
status:
revisao:
---
"""
    # 🔐 Carregar API Key
    load_dotenv()
    # 🧠 Definir o LLM
    api_key = os.getenv('GROQ_API_KEY')
    os.environ['GROQ_API_KEY'] = api_key
    chat = ChatGroq(model='llama-3.3-70b-versatile')

    # 🎯 Template do Prompt
    template = """
    Você é um assistente especializado em transformar transcrições de aulas em notas bem estruturadas no seguinte formato Markdown.
    {prompt_task}

    -----------
    Transcrição:
    {transcricao}
    """

    prompt = ChatPromptTemplate.from_template(template)

    # 🚀 Inputs manuais + transcrição carregada do JSON
    inputs = {
        "prompt_task": prompt_task,
        "transcricao": transcricao,
    }

    # 🔥 Executa o modelo
    chain = prompt | chat
    resultado = chain.invoke(inputs)

    nota_final = f"""{dados_aula}
{resultado.content}
"""

    # 💾 Caminho de saída
    caminho_nota = "\\".join(caminho_arquivo.replace("03. transcrições", "04. notas").split("\\")[:-1])
    os.makedirs(caminho_nota, exist_ok=True)

    caminho_arquivo_md = f"{caminho_nota}/{titulo_aula}.md"
    with open(caminho_arquivo_md, "w", encoding="utf-8") as file:
        file.write(nota_final)

    print(f"✅ Nota gerada e salva em: {caminho_arquivo_md}")
    return caminho_arquivo_md
