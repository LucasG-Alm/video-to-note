import os
import re
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

from src.utils.utils import print_hex_color
from src.config import DEFAULT_MODEL

FALLBACK_MODEL = "llama-3.1-8b-instant"
_TOKEN_WARNING_THRESHOLD = 10000


def _is_rate_limit_error(e: Exception) -> bool:
    """Detecta erros de rate limit do Groq (status 429) em qualquer forma que cheguem."""
    return (
        type(e).__name__ == "RateLimitError"
        or getattr(e, "status_code", None) == 429
        or "429" in str(e)
        or "rate limit" in str(e).lower()
        or "rate_limit" in str(e).lower()
    )


def _invoke_llm_with_fallback(
    prompt_text: str,
    primary_model: str,
    fallback_model: str,
    api_key: str,
) -> str:
    """
    Tenta chamar o LLM com o modelo primário.
    Se receber rate limit (429), reexecuta com o modelo de fallback.
    Usa HumanMessage diretamente — sem ChatPromptTemplate — para evitar
    conflitos com chaves '{...}' em transcrições de código.
    Qualquer outro erro é propagado normalmente.
    """
    def _run(model: str) -> str:
        chat = ChatGroq(model=model, api_key=api_key)
        result = chat.invoke([HumanMessage(content=prompt_text)])
        return getattr(result, "content", str(result))

    try:
        return _run(primary_model)
    except Exception as e:
        if _is_rate_limit_error(e):
            print_hex_color("#f0a500", f"⚠️  TPM excedido no {primary_model} — tentando {fallback_model}...", "")
            return _run(fallback_model)
        raise


def _warn_if_tokens_high(text: str) -> None:
    """Imprime aviso se o texto estiver próximo do limite de 12k tokens do free tier."""
    estimated = _estimate_tokens(text)
    if estimated > _TOKEN_WARNING_THRESHOLD:
        print_hex_color("#f0a500", f"⚠️  Prompt longo ({estimated} tokens estimados) — próximo do limite de 12k TPM.", "")


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



_MAX_TRANSCRIPTION_TOKENS = 8000  # acima disso, chunk antes de enviar ao LLM
_CHUNK_TOKENS = 5000               # tamanho de cada chunk (estimativa: 1 token ≈ 4 chars)


def _estimate_tokens(text: str) -> int:
    return len(text) // 4


def _split_into_chunks(text: str, max_tokens: int) -> list:
    max_chars = max_tokens * 4
    words = text.split()
    chunks, current, current_len = [], [], 0
    for word in words:
        wlen = len(word) + 1
        if current_len + wlen > max_chars and current:
            chunks.append(' '.join(current))
            current, current_len = [word], wlen
        else:
            current.append(word)
            current_len += wlen
    if current:
        chunks.append(' '.join(current))
    return chunks


def _summarize_chunk(chunk: str, primary_model: str, fallback_model: str, api_key: str, idx: int, total: int) -> str:
    prompt_text = (
        f"Você é um assistente de síntese. Resuma os pontos principais desta parte "
        f"({idx} de {total}) da transcrição em tópicos concisos, preservando ideias "
        f"centrais, exemplos e argumentos importantes:\n\n{chunk}"
    )
    return _invoke_llm_with_fallback(prompt_text, primary_model, fallback_model, api_key)


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
    model: str = DEFAULT_MODEL,
    output_dir: str = None,
    date_override: str = None,
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
    data_atual = date_override if date_override else datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    horas = int(duracao // 3600)
    minutos = int((duracao % 3600) // 60)
    segundos = int(duracao % 60)
    duracao_formatada = f"{horas}h{minutos:02d}m{segundos:02d}s"

    metadata_final = {**metadata_json, **(metadata or {}), **{'date': data_atual}, **{'capitulos': capitulos}, **{'duracao_formatada': duracao_formatada}}

    # 🔐 LLM
    load_dotenv(Path(__file__).parent.parent.parent / '.env')
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY não encontrada. Verifique o arquivo .env")
    chat = ChatGroq(model=model, api_key=api_key)

    # ✂️ Chunking automático para transcrições longas
    if _estimate_tokens(transcricao) > _MAX_TRANSCRIPTION_TOKENS:
        chunks = _split_into_chunks(transcricao, _CHUNK_TOKENS)
        print_hex_color('#f0a500', f"⚠️  Transcrição longa ({_estimate_tokens(transcricao)} tokens estimados) — dividindo em {len(chunks)} partes...", "")
        summaries = [_summarize_chunk(chunk, model, FALLBACK_MODEL, api_key, i + 1, len(chunks)) for i, chunk in enumerate(chunks)]
        transcricao = "\n\n---\n\n".join(summaries)
        print_hex_color('#0bd271', f"✅ {len(chunks)} partes resumidas. Gerando nota final...", "")

    # 🎯 Leitura do template
    yaml_raw, prompt_raw = ler_md_template(path_template_md)

    # 🏗️ Montagem
    yaml_preenchido = preencher_variables(yaml_raw, metadata_final)
    prompt_final = preencher_variables(prompt_raw, metadata_final)

    prompt_text = f"""
{prompt_final}

-----------
Transcrição:
{transcricao}
"""

    # ⚠️ M-09: aviso se prompt está próximo do limite de tokens
    _warn_if_tokens_high(prompt_text)

    # 🤖 M-10: fallback automático de modelo se TPM excedido
    conteudo = _invoke_llm_with_fallback(
        prompt_text=prompt_text,
        primary_model=model,
        fallback_model=FALLBACK_MODEL,
        api_key=api_key,
    )

    nota_final = f"""---\n{yaml_preenchido}\n---\n{conteudo}"""

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

def split_transcript_by_chapters(segments: list, chapters: list) -> list:
    """
    Divide segmentos de transcrição pelos capítulos do vídeo.

    Cada segmento é atribuído ao capítulo cujo intervalo
    [start_time, próximo_capítulo.start_time) o contém.
    O último capítulo abrange todos os segmentos restantes.

    Retorna lista de dicts: [{'title': str, 'text': str}, ...]
    Se não há capítulos, retorna lista com um único grupo com toda a transcrição.
    """
    if not chapters:
        return [{'title': '', 'text': ' '.join(s['text'] for s in segments)}]

    groups = [{'title': cap['title'], 'text': ''} for cap in chapters]

    for seg in segments:
        start = seg.get('start', 0)
        idx = len(chapters) - 1
        for i in range(len(chapters) - 1):
            if start < chapters[i + 1]['start_time']:
                idx = i
                break
        sep = ' ' if groups[idx]['text'] else ''
        groups[idx]['text'] += sep + seg['text']

    return groups


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
