import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import re
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
import json
from datetime import datetime
from dotenv import load_dotenv

from src.utils.utils import *

def ler_md_template(caminho_md):
    with open(caminho_md, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    partes = conteudo.split('---')
    if len(partes) >= 3:
        yaml = partes[1].strip()
        prompt = '---'.join(partes[2:]).strip()
    else:
        yaml = ''
        prompt = conteudo.strip()

    return yaml, prompt

#ler = ler_md_template('C:\\Users\\lucas\\OneDrive\\Documentos\\PROGRAMAÇÃO\\Python\\Doc courses\\src\\templates\\template_youtube.md')
#print(ler[0])
#print(len(ler))

def preencher_variables(yaml_str, contexto: dict):
    def replacer(match):
        chave = match.group(1).strip()
        # Se existir a chave, retorna o valor, senão mantém {{chave}}
        return str(contexto.get(chave, f'{{{{{chave}}}}}'))
    
    return re.sub(r'\{\{(.*?)\}\}', replacer, yaml_str)


#with open('C:\\Users\\lucas\\OneDrive\\Documentos\\PROGRAMAÇÃO\\Python\\Doc courses\\data\\03. transcriptions\\Youtube\\FAÇA ISSO SEMPRE QUE RECEBER SEU SALÁRIO _ Como organizar suas finanças e guardar dinheiro.json', 'r', encoding='utf-8') as arquivo:
#    dados = json.load(arquivo)

#print(dados['metadata'])
#t = preencher_variables(ler[0], dados['metadata'])

def gerar_capitulos_formatado(capitulos: list) -> str:
    def segundos_para_minutos(segundos):
        minutos = int(segundos // 60)
        segundos_restantes = int(segundos % 60)
        return f"{minutos}:{segundos_restantes:02d}"

    linhas = []
    if capitulos:
        for cap in capitulos:
            tempo = segundos_para_minutos(cap['start_time'])
            linhas.append(f"- {tempo} - **{cap['title']}**")
    else:
        resultado = ""

    resultado = "\n".join(linhas)
    return resultado

def gerar_nota_md(
    path_transcricao_json: str,
    path_template_md: str,
    metadata: dict = None,
    title: str = None,
    model: str = 'llama-3.3-70b-versatile'
):
    # 🔍 Extrai metadados do arquivo
    if title == None:
        title = path_transcricao_json.split("\\")[-1].split(" - ")[0]

    # 🧠 Leitura da transcrição
    with open(path_transcricao_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    transcricao = dados.get("transcription", {}).get("text", "")
    metadata_json = dados.get("metadata", {})
    capitulos = gerar_capitulos_formatado(dados.get("metadata", {}).get("chapters", ""))
    duracao = metadata_json.get("duration_sec", 0)
    data_atual = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    horas = int(duracao // 3600)
    minutos = int((duracao % 3600) // 60)
    segundos = int(duracao % 60)
    duracao_formatada = f"{horas}h{minutos:02d}m{segundos:02d}s"

    metadata_final = {**metadata_json, **(metadata or {}), **{'date': data_atual}, **{'capitulos': capitulos}, **{'duracao_formatada': duracao_formatada}}

    # 🎯 Leitura do template
    yaml_raw, prompt_raw = ler_md_template(path_template_md)

    # 🏗️ Montagem
    yaml_preenchido = preencher_variables(yaml_raw, metadata_final)
    #print(yaml_preenchido)
    prompt_final = preencher_variables(prompt_raw, metadata_final)
    #print(prompt_final)

    # 🔐 LLM
    load_dotenv()
    chat = ChatGroq(model=model)

    template = f"""
{prompt_final}

-----------
Transcrição:
{transcricao}
"""
    prompt = ChatPromptTemplate.from_template(template)

    chain = prompt | chat
    resultado = chain.invoke({"transcricao": transcricao})

    nota_final = f"""---\n{yaml_preenchido}\n---\n{getattr(resultado, 'content', str(resultado))}"""

    # 💾 Salvar
    pasta_saida = path_transcricao_json.replace("03. transcriptions", "04. notes")
    pasta_saida = "\\".join(pasta_saida.split("\\")[:-1])
    os.makedirs(pasta_saida, exist_ok=True)

    path_saida = f"{pasta_saida}/{title}.md"
    with open(path_saida, 'w', encoding='utf-8') as f:
        f.write(nota_final)

    print_hex_color('#0bd271', f"✅ Nota salva em:",f"{path_saida}")
    return path_saida

# ▶️ TESTE DE EXECUÇÃO
if __name__ == "__main__":
    gerar_nota_md(
        #title="Teste",
        path_transcricao_json="D:\\Users\\Lucas\\OneDrive\\Documentos\\PROGRAMAÇÃO\\Python\\Doc courses\\data\\03. transcriptions\\Youtube\\AUTORIDADE INSTANTANEA_ 15 tecnicas PROIBIDAS para PERSUASAO absoluta.json",
        path_template_md="D:\\Users\\Lucas\\OneDrive\\Documentos\\PROGRAMAÇÃO\\Python\\Doc courses\\templates\\template_youtube copy.md",
        metadata={
            "area": "",
            "tags_md": "finanças\n    - produtividade\n    - aprendizado"
        }
    )


