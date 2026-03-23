"""
Testes unitários para src/core/notes2.py

Testamos as funções de template e formatação — o motor que transforma
a transcrição bruta numa nota Obsidian estruturada.
Nenhum teste aqui chama a API da Groq.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.core.notes2 import (
    gerar_capitulos_formatado,
    preencher_variables,
    ler_md_template,
    _estimate_tokens,
    _split_into_chunks,
)


class TestGerarCapitulosFormatado:
    """
    Formata a lista de capítulos do vídeo para o corpo da nota.
    Exemplo de output esperado:
        - 0:00 - **Introdução**
        - 1:30 - **Desenvolvimento**

    Pseudo-código:
        recebe lista de capítulos [{start_time: segundos, title: str}]
        converte segundos → "M:SS"
        monta linha "- M:SS - **título**" para cada capítulo
        junta com \n
        se lista vazia/None → retorna ""
    """

    def test_formata_capitulos_corretamente(self):
        capitulos = [
            {"start_time": 0, "title": "Introdução"},
            {"start_time": 90, "title": "Desenvolvimento"},
            {"start_time": 3661, "title": "Conclusão"},
        ]
        resultado = gerar_capitulos_formatado(capitulos)
        assert "0:00" in resultado
        assert "**Introdução**" in resultado
        assert "1:30" in resultado       # 90s = 1min30s
        assert "**Desenvolvimento**" in resultado
        assert "61:01" in resultado      # 3661s = 61min01s

    def test_lista_vazia_retorna_string_vazia(self):
        # Muitos vídeos não têm capítulos — não pode crashar
        assert gerar_capitulos_formatado([]) == ""

    def test_none_retorna_string_vazia(self):
        # yt-dlp retorna chapters=None quando o vídeo não tem capítulos definidos
        assert gerar_capitulos_formatado(None) == ""

    def test_string_vazia_retorna_string_vazia(self):
        # dados.get("chapters", "") retorna "" se a chave não existir
        assert gerar_capitulos_formatado("") == ""

    def test_capitulo_unico(self):
        capitulos = [{"start_time": 0, "title": "Único"}]
        resultado = gerar_capitulos_formatado(capitulos)
        assert "**Único**" in resultado
        assert "\n" not in resultado  # só uma linha, sem quebra no final


class TestPreencherVariables:
    """
    Motor de template: substitui {{chave}} pelos valores do contexto.
    É o que faz o frontmatter YAML da nota ser preenchido automaticamente.

    Pseudo-código:
        recebe string com {{chaves}} e dict de contexto
        para cada {{chave}} encontrada:
            se chave existe no contexto → substitui pelo valor
            se não existe → mantém {{chave}} intacto
        retorna string substituída

    Por que manter {{chave}} quando ausente?
    → Falha silenciosa (virar "") seria pior: o YAML ficaria inválido
      e você não saberia qual campo está faltando.
    """

    def test_substitui_variavel_existente(self):
        resultado = preencher_variables("título: {{title}}", {"title": "Meu Vídeo"})
        assert resultado == "título: Meu Vídeo"

    def test_mantem_variavel_ausente(self):
        # Variável não encontrada deve ser MANTIDA, não virar string vazia
        resultado = preencher_variables("link: {{url}}", {})
        assert "{{url}}" in resultado

    def test_substitui_multiplas_variaveis(self):
        yaml = "título: {{title}}\nauthor: {{uploader}}"
        ctx = {"title": "Video Incrível", "uploader": "Canal Top"}
        resultado = preencher_variables(yaml, ctx)
        assert "Video Incrível" in resultado
        assert "Canal Top" in resultado

    def test_contexto_vazio_mantém_tudo(self):
        template = "{{a}} e {{b}}"
        resultado = preencher_variables(template, {})
        assert "{{a}}" in resultado
        assert "{{b}}" in resultado

    def test_valor_numerico_convertido_para_string(self):
        # duration_sec vem como int do yt-dlp — precisa funcionar no template
        resultado = preencher_variables("duração: {{duration_sec}}", {"duration_sec": 3600})
        assert "3600" in resultado


class TestLerMdTemplate:
    """
    Separa frontmatter YAML do prompt no arquivo de template.
    Estrutura esperada do template:
        ---
        yaml aqui
        ---
        prompt aqui

    Se o parsing errar, o prompt do LLM pode vazar para o corpo da nota
    (o modelo "vê" as instruções e às vezes as reproduz no output).

    Usamos tmp_path — fixture nativa do pytest que cria uma pasta
    temporária limpa para cada teste, sem depender de arquivos reais no disco.
    """

    def test_template_com_frontmatter(self, tmp_path):
        # Caso normal: template bem formado com --- separando yaml e prompt
        template = tmp_path / "template.md"
        template.write_text(
            "---\ntítulo: {{title}}\nauthor: {{uploader}}\n---\nResuma o vídeo abaixo.",
            encoding="utf-8"
        )

        yaml, prompt = ler_md_template(str(template))

        assert "título: {{title}}" in yaml
        assert "author: {{uploader}}" in yaml
        assert "Resuma o vídeo abaixo." in prompt
        # O prompt não deve conter o YAML
        assert "título:" not in prompt

    def test_template_sem_frontmatter(self, tmp_path):
        # Template que é só prompt, sem ---
        # yaml deve ser "" e prompt deve conter o texto inteiro
        template = tmp_path / "template.md"
        template.write_text("Apenas prompt, sem frontmatter.", encoding="utf-8")

        yaml, prompt = ler_md_template(str(template))

        assert yaml == ""
        assert "Apenas prompt" in prompt

    def test_prompt_com_hifen_triplo_no_corpo(self, tmp_path):
        # --- pode aparecer como separador decorativo no corpo do prompt
        # O parser deve pegar apenas o primeiro bloco como frontmatter
        template = tmp_path / "template.md"
        template.write_text(
            "---\ntag: {{tag}}\n---\nIntrodução\n---\nSeção 2",
            encoding="utf-8"
        )

        yaml, prompt = ler_md_template(str(template))

        assert "tag: {{tag}}" in yaml
        assert "Introdução" in prompt
        assert "Seção 2" in prompt


class TestChunking:
    """
    ERR-02 — Chunking automático para transcrições longas.

    _estimate_tokens: estimativa rápida baseada em chars (1 token ≈ 4 chars).
    _split_into_chunks: divide o texto em blocos que cabem no limite de tokens,
    respeitando fronteiras de palavras — nunca corta no meio de uma palavra.

    Por que testar isso separadamente do gerar_nota_md?
    → gerar_nota_md precisa de API key + arquivos no disco. As funções de
      chunking são pura lógica; testá-las isoladamente garante o comportamento
      sem nenhum mock de infra.
    """

    def test_estimate_tokens_proporcional_ao_tamanho(self):
        # 400 chars → ~100 tokens
        texto = "a" * 400
        assert _estimate_tokens(texto) == 100

    def test_estimate_tokens_string_vazia(self):
        assert _estimate_tokens("") == 0

    def test_texto_curto_retorna_chunk_unico(self):
        texto = "palavra " * 10  # ~80 chars → 20 tokens — bem abaixo de qualquer limite
        chunks = _split_into_chunks(texto, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0].strip() == texto.strip()

    def test_divide_em_multiplos_chunks(self):
        # 100 palavras de 5 chars cada → ~600 chars → 150 tokens
        # Com limite de 50 tokens (200 chars), espera pelo menos 2 chunks
        texto = "abcde " * 100
        chunks = _split_into_chunks(texto, max_tokens=50)
        assert len(chunks) >= 2

    def test_nenhuma_palavra_e_perdida(self):
        palavras = ["palavra" + str(i) for i in range(200)]
        texto = " ".join(palavras)
        chunks = _split_into_chunks(texto, max_tokens=50)
        reconstruido = " ".join(chunks)
        for palavra in palavras:
            assert palavra in reconstruido

    def test_cada_chunk_respeita_limite(self):
        texto = "abcde " * 200  # ~1200 chars
        max_tokens = 30  # 120 chars por chunk
        chunks = _split_into_chunks(texto, max_tokens=max_tokens)
        for chunk in chunks:
            assert _estimate_tokens(chunk) <= max_tokens + 2  # +2 de margem por palavra longa


class TestLoadDotenvPath:
    """
    ERR-03 — load_dotenv deve receber um path explícito para o .env na raiz
    do projeto, não depender do find_dotenv() que falha via stdin/heredoc.

    Verificamos que load_dotenv é chamado com um Path (não sem argumentos),
    e que esse Path termina em '.env'.
    """

    def test_load_dotenv_recebe_path_explicito(self, tmp_path):
        # Monta um JSON de transcrição mínimo e um template mínimo
        transcricao_json = tmp_path / "transcricao.json"
        transcricao_json.write_text(
            '{"transcription": {"text": "texto curto"}, "metadata": {}}',
            encoding="utf-8"
        )
        template_md = tmp_path / "template.md"
        template_md.write_text("---\ntag: teste\n---\nResuma: {transcricao}", encoding="utf-8")

        mock_result = MagicMock()
        mock_result.content = "# Nota gerada"

        with patch("src.core.notes2.load_dotenv") as mock_load, \
             patch("src.core.notes2.ChatGroq") as mock_groq, \
             patch.dict("os.environ", {"GROQ_API_KEY": "fake-key"}):

            mock_groq.return_value.__or__ = lambda self, other: MagicMock(
                invoke=lambda _: mock_result
            )
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_result
            mock_groq.return_value.__ror__ = MagicMock(return_value=mock_chain)

            # Importamos gerar_nota_md aqui pra evitar efeito colateral no topo do módulo
            from src.core.notes2 import gerar_nota_md
            try:
                gerar_nota_md(
                    path_transcricao_json=str(transcricao_json),
                    path_template_md=str(template_md),
                    output_dir=str(tmp_path),
                )
            except Exception:
                pass  # erros de LLM mock são esperados; o que importa é o assert abaixo

        # Confirma que load_dotenv foi chamado com um argumento Path (não sem args)
        mock_load.assert_called_once()
        call_arg = mock_load.call_args[0][0]
        assert isinstance(call_arg, Path)
        assert call_arg.name == ".env"
