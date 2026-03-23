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
    _is_rate_limit_error,
    _invoke_llm_with_fallback,
    _warn_if_tokens_high,
    split_transcript_by_chapters,
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


class TestIsRateLimitError:
    """
    M-10 — _is_rate_limit_error detecta erros de rate limit do Groq.

    O Groq pode sinalizar TPM excedido de formas diferentes dependendo
    da versão do SDK e de como o LangChain encapsula o erro:
    - Exceção com atributo status_code=429
    - Exceção cujo nome é 'RateLimitError'
    - Exceção cuja mensagem contém '429' ou 'rate limit'
    Qualquer um desses deve ser reconhecido como rate limit.
    """

    def test_reconhece_status_code_429(self):
        e = Exception("error")
        e.status_code = 429
        assert _is_rate_limit_error(e) is True

    def test_reconhece_nome_RateLimitError(self):
        class RateLimitError(Exception):
            pass
        assert _is_rate_limit_error(RateLimitError("too many")) is True

    def test_reconhece_mensagem_com_429(self):
        assert _is_rate_limit_error(Exception("HTTP 429 Too Many Requests")) is True

    def test_reconhece_mensagem_rate_limit(self):
        assert _is_rate_limit_error(Exception("rate limit exceeded")) is True

    def test_nao_reconhece_erro_generico(self):
        assert _is_rate_limit_error(ValueError("algo deu errado")) is False

    def test_nao_reconhece_erro_500(self):
        e = Exception("server error")
        e.status_code = 500
        assert _is_rate_limit_error(e) is False


class TestInvokeLlmWithFallback:
    """
    M-10 — _invoke_llm_with_fallback tenta o modelo primário e,
    se receber rate limit, reexecuta com o modelo de fallback.

    A função recebe o prompt já renderizado (sem variáveis de template)
    e chama ChatGroq.invoke([HumanMessage(...)]) diretamente — sem
    ChatPromptTemplate, o que evita conflitos com chaves '{...}' que
    podem aparecer em transcrições de código.

    Testamos mockando ChatGroq.invoke para controlar falhas e respostas.
    """

    def _make_rate_limit_error(self):
        e = Exception("rate_limit_exceeded")
        e.status_code = 429
        return e

    def test_retorna_resultado_do_modelo_primario_quando_funciona(self):
        mock_result = MagicMock()
        mock_result.content = "nota gerada"

        with patch("src.core.notes2.ChatGroq") as MockGroq:
            instance = MagicMock()
            instance.invoke.return_value = mock_result
            MockGroq.return_value = instance

            result = _invoke_llm_with_fallback(
                prompt_text="Resuma este texto sem variáveis de template",
                primary_model="llama-3.3-70b-versatile",
                fallback_model="llama-3.1-8b-instant",
                api_key="fake-key",
            )

        assert result == "nota gerada"

    def test_usa_fallback_quando_primario_lanca_rate_limit(self):
        fallback_result = MagicMock()
        fallback_result.content = "nota do fallback"

        with patch("src.core.notes2.ChatGroq") as MockGroq:
            rate_limit = self._make_rate_limit_error()

            primary_instance = MagicMock()
            primary_instance.invoke.side_effect = rate_limit

            fallback_instance = MagicMock()
            fallback_instance.invoke.return_value = fallback_result

            MockGroq.side_effect = [primary_instance, fallback_instance]

            result = _invoke_llm_with_fallback(
                prompt_text="Resuma este texto",
                primary_model="llama-3.3-70b-versatile",
                fallback_model="llama-3.1-8b-instant",
                api_key="fake-key",
            )

        assert result == "nota do fallback"

    def test_instancia_fallback_com_modelo_correto(self):
        fallback_result = MagicMock()
        fallback_result.content = "ok"

        with patch("src.core.notes2.ChatGroq") as MockGroq:
            rate_limit = self._make_rate_limit_error()

            primary_instance = MagicMock()
            primary_instance.invoke.side_effect = rate_limit

            fallback_instance = MagicMock()
            fallback_instance.invoke.return_value = fallback_result

            MockGroq.side_effect = [primary_instance, fallback_instance]

            _invoke_llm_with_fallback(
                prompt_text="prompt",
                primary_model="llama-3.3-70b-versatile",
                fallback_model="llama-3.1-8b-instant",
                api_key="fake-key",
            )

        # Segundo ChatGroq instanciado deve usar o modelo de fallback
        assert MockGroq.call_args_list[1].kwargs.get("model") == "llama-3.1-8b-instant" or \
               MockGroq.call_args_list[1].args[0] == "llama-3.1-8b-instant"

    def test_nao_faz_fallback_em_erro_generico(self):
        with patch("src.core.notes2.ChatGroq") as MockGroq:
            instance = MagicMock()
            instance.invoke.side_effect = ValueError("erro de parsing")
            MockGroq.return_value = instance

            with pytest.raises(ValueError, match="erro de parsing"):
                _invoke_llm_with_fallback(
                    prompt_text="prompt",
                    primary_model="llama-3.3-70b-versatile",
                    fallback_model="llama-3.1-8b-instant",
                    api_key="fake-key",
                )

    def test_propaga_erro_se_fallback_tambem_falha(self):
        with patch("src.core.notes2.ChatGroq") as MockGroq:
            rate_limit = self._make_rate_limit_error()

            primary_instance = MagicMock()
            primary_instance.invoke.side_effect = rate_limit

            fallback_instance = MagicMock()
            fallback_instance.invoke.side_effect = Exception("fallback também falhou")

            MockGroq.side_effect = [primary_instance, fallback_instance]

            with pytest.raises(Exception, match="fallback também falhou"):
                _invoke_llm_with_fallback(
                    prompt_text="prompt",
                    primary_model="llama-3.3-70b-versatile",
                    fallback_model="llama-3.1-8b-instant",
                    api_key="fake-key",
                )


class TestWarnIfTokensHigh:
    """
    M-09 — _warn_if_tokens_high imprime aviso quando o texto está
    próximo do limite de 12k tokens do free tier da Groq.

    Threshold: 10000 tokens estimados (~40000 chars).
    Abaixo: sem output. Acima: print com a contagem.
    A geração continua em ambos os casos — é só informativo.
    """

    def test_sem_output_abaixo_do_threshold(self, capsys):
        texto_curto = "palavra " * 100  # ~800 chars → ~200 tokens
        _warn_if_tokens_high(texto_curto)
        assert capsys.readouterr().out == ""

    def test_imprime_aviso_acima_do_threshold(self, capsys):
        texto_longo = "palavra " * 6000  # ~48000 chars → ~12000 tokens
        _warn_if_tokens_high(texto_longo)
        output = capsys.readouterr().out
        assert output != ""

    def test_aviso_contem_contagem_de_tokens(self, capsys):
        texto_longo = "a" * 44000  # 44000 chars → 11000 tokens
        _warn_if_tokens_high(texto_longo)
        output = capsys.readouterr().out
        assert "11000" in output

    def test_nao_lanca_excecao(self):
        # Garantir que o aviso nunca interrompe o pipeline
        texto_longo = "x" * 100000
        _warn_if_tokens_high(texto_longo)  # não deve lançar nada


class TestSplitTranscriptByChapters:
    """
    M-05 — split_transcript_by_chapters divide segmentos de transcrição
    pelos capítulos do vídeo usando os timestamps de cada segmento.

    Regra de atribuição: segmento vai para o capítulo cujo
    intervalo [start_time, próximo_capítulo.start_time) o contém.
    O último capítulo vai até o fim da transcrição.

    Por que isso importa?
    → Sem essa função, --by-chapter não consegue separar o conteúdo
      de cada parte do vídeo. Um erro aqui mistura trechos de capítulos
      diferentes, gerando notas incoerentes.
    """

    CHAPTERS = [
        {'start_time': 0,  'title': 'Introdução'},
        {'start_time': 30, 'title': 'Desenvolvimento'},
        {'start_time': 60, 'title': 'Conclusão'},
    ]

    SEGMENTS = [
        {'start': 0.0,  'duration': 5.0, 'text': 'texto intro 1'},
        {'start': 10.0, 'duration': 5.0, 'text': 'texto intro 2'},
        {'start': 30.0, 'duration': 5.0, 'text': 'texto dev 1'},
        {'start': 45.0, 'duration': 5.0, 'text': 'texto dev 2'},
        {'start': 60.0, 'duration': 5.0, 'text': 'texto conclusao'},
    ]

    def test_retorna_um_grupo_por_capitulo(self):
        result = split_transcript_by_chapters(self.SEGMENTS, self.CHAPTERS)
        assert len(result) == 3

    def test_titulos_preservados(self):
        result = split_transcript_by_chapters(self.SEGMENTS, self.CHAPTERS)
        titles = [g['title'] for g in result]
        assert titles == ['Introdução', 'Desenvolvimento', 'Conclusão']

    def test_segmentos_atribuidos_ao_capitulo_correto(self):
        result = split_transcript_by_chapters(self.SEGMENTS, self.CHAPTERS)
        assert 'texto intro 1' in result[0]['text']
        assert 'texto intro 2' in result[0]['text']
        assert 'texto dev 1' in result[1]['text']
        assert 'texto dev 2' in result[1]['text']
        assert 'texto conclusao' in result[2]['text']

    def test_segmento_no_inicio_exato_do_capitulo(self):
        # Segmento em start=30.0 deve ir para 'Desenvolvimento', não 'Introdução'
        result = split_transcript_by_chapters(self.SEGMENTS, self.CHAPTERS)
        assert 'texto dev 1' not in result[0]['text']
        assert 'texto dev 1' in result[1]['text']

    def test_sem_capitulos_retorna_tudo_em_um_grupo(self):
        result = split_transcript_by_chapters(self.SEGMENTS, [])
        assert len(result) == 1
        assert 'texto intro 1' in result[0]['text']
        assert 'texto conclusao' in result[0]['text']

    def test_sem_capitulos_titulo_e_vazio_ou_padrao(self):
        result = split_transcript_by_chapters(self.SEGMENTS, [])
        # Não deve lançar exceção e deve ter algum título (pode ser "" ou padrão)
        assert 'title' in result[0]

    def test_capitulo_sem_segmentos_retorna_texto_vazio(self):
        chapters = [
            {'start_time': 0,   'title': 'Com conteúdo'},
            {'start_time': 100, 'title': 'Vazio'},  # nenhum segmento aqui
        ]
        segments = [{'start': 5.0, 'duration': 2.0, 'text': 'só aqui'}]
        result = split_transcript_by_chapters(segments, chapters)
        assert result[1]['text'].strip() == ''

    def test_capitulo_unico_recebe_todos_os_segmentos(self):
        chapters = [{'start_time': 0, 'title': 'Único'}]
        result = split_transcript_by_chapters(self.SEGMENTS, chapters)
        assert len(result) == 1
        for seg in self.SEGMENTS:
            assert seg['text'] in result[0]['text']

    def test_segmentos_vazios_retorna_grupos_com_texto_vazio(self):
        result = split_transcript_by_chapters([], self.CHAPTERS)
        assert len(result) == 3
        for group in result:
            assert group['text'].strip() == ''
