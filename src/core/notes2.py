import os
import re
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

from src.utils.utils import print_hex_color

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


def preencher_variables(yaml_str, contexto: dict):
    def replacer(match):
        chave = match.group(1).strip()
        # Se existir a chave, retorna o valor, senão mantém {{chave}}
        return str(contexto.get(chave, f'{{{{{chave}}}}}'))
    
    return re.sub(r'\{\{(.*?)\}\}', replacer, yaml_str)



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
    model: str = 'llama-3.3-70b-versatile',
    output_dir: str = None,
):
    # 🔍 Extrai metadados do arquivo
    if title is None:
        title = Path(path_transcricao_json).stem.split(" - ")[0]

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
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY não encontrada. Verifique o arquivo .env")
    chat = ChatGroq(model=model, api_key=api_key)

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
    if output_dir:
        pasta_saida = Path(output_dir)
    else:
        pasta_saida = Path(str(Path(path_transcricao_json).parent).replace("03. transcriptions", "04. notes"))
    pasta_saida.mkdir(parents=True, exist_ok=True)

    path_saida = pasta_saida / f"{title}.md"
    with open(path_saida, 'w', encoding='utf-8') as f:
        f.write(nota_final)

    print_hex_color('#0bd271', f"✅ Nota salva em:",f"{path_saida}")
    return path_saida

if __name__ == "__main__":
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    gerar_nota_md(
        path_transcricao_json=str(PROJECT_ROOT / "data/03. transcriptions/Youtube/exemplo.json"),
        path_template_md=str(PROJECT_ROOT / "templates/template_youtube copy.md"),
        metadata={
            "area": "",
            "tags_md": "YouTube/Vídeo"
        }
    )
