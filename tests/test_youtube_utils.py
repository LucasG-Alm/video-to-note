"""
Testes unitários para src/services/youtube.py

Testamos apenas funções puras — sem chamadas de API, sem rede, sem disco.
São o contrato do que cada função DEVE fazer. Se alguém mudar o comportamento
acidentalmente, o teste quebra e avisa antes de chegar em produção.
"""
import pytest
from src.services.youtube import extract_video_id, sanitize_filename, transcript_to_text, _parse_vtt, _parse_json3, _vtt_time_to_seconds


class TestExtractVideoId:
    """
    extract_video_id é o portão de entrada da pipeline de YouTube.
    Se retornar None silenciosamente, o vídeo é pulado sem nenhum aviso.

    Pseudo-código do que ela faz:
        recebe url
        procura padrão (?v=XXXXXXXXXXX ou youtu.be/XXXXXXXXXXX)
        retorna os 11 caracteres do ID, ou None se não encontrar
    """

    def test_url_padrao(self):
        # Formato mais comum — watch?v=
        assert extract_video_id("https://www.youtube.com/watch?v=XswU6CRs79s") == "XswU6CRs79s"

    def test_url_curta_youtu_be(self):
        # Links encurtados são muito usados quando alguém compartilha no celular
        assert extract_video_id("https://youtu.be/XswU6CRs79s") == "XswU6CRs79s"

    def test_url_shorts(self):
        # YouTube Shorts tem URL diferente mas o ID ainda tem 11 chars
        assert extract_video_id("https://www.youtube.com/shorts/2DGce61n8rY") == "2DGce61n8rY"

    def test_url_com_timestamp(self):
        # ?t=120s aparece quando alguém compartilha um momento específico
        # O ID deve ser extraído mesmo com parâmetros extras
        assert extract_video_id("https://www.youtube.com/watch?v=XswU6CRs79s&t=120s") == "XswU6CRs79s"

    def test_url_com_playlist(self):
        # URLs de playlist têm &list= mas o ID do vídeo ainda está lá
        assert extract_video_id("https://www.youtube.com/watch?v=XswU6CRs79s&list=PLxyz") == "XswU6CRs79s"

    def test_url_invalida_retorna_none(self):
        # Não deve lançar exceção — deve retornar None para o caller decidir o que fazer
        assert extract_video_id("https://www.google.com") is None

    def test_string_vazia_retorna_none(self):
        assert extract_video_id("") is None


class TestSanitizeFilename:
    """
    sanitize_filename define o nome de TODOS os arquivos gerados.
    Um bug aqui renomeia silenciosamente todos os outputs — difícil de rastrear.

    Pseudo-código:
        recebe título (pode ter acentos, caracteres especiais, ser longo)
        normaliza unicode (remove acentos)
        remove caracteres proibidos em nomes de arquivo: \\ / * ? : " < > |
        colapsa espaços duplos
        trunca em max_length (padrão 100)
        retorna string segura para usar como nome de arquivo
    """

    def test_titulo_normal_sem_modificacao(self):
        # Happy path — título limpo não deve ser modificado
        assert sanitize_filename("Como aprender Python") == "Como aprender Python"

    def test_remove_acentos(self):
        # Acentos causam problemas em filesystems não-UTF8 e em alguns terminais
        resultado = sanitize_filename("Programação e Inteligência Artificial")
        assert "ã" not in resultado
        assert "ê" not in resultado

    def test_remove_caracteres_invalidos_windows(self):
        # Esses chars são proibidos no Windows: \ / : * ? " < > |
        resultado = sanitize_filename('título: "filme" <2024>')
        assert ":" not in resultado
        assert '"' not in resultado
        assert "<" not in resultado
        assert ">" not in resultado

    def test_trunca_titulo_longo(self):
        # Títulos de vídeo podem ser enormes. Nome de arquivo tem limite no SO.
        titulo_longo = "A" * 200
        assert len(sanitize_filename(titulo_longo)) <= 100

    def test_trunca_com_max_length_customizado(self):
        assert len(sanitize_filename("A" * 200, max_length=50)) <= 50


class TestTranscriptToText:
    """
    Converte lista de segmentos [{text, start, duration}] em texto contínuo.
    É a "cola" entre a transcrição bruta e o LLM.

    Pseudo-código:
        recebe lista de segmentos
        extrai campo 'text' de cada um
        junta tudo com espaço
        retorna string única
    """

    def test_lista_normal(self):
        transcript = [
            {"start": 0.0, "duration": 1.5, "text": "Olá"},
            {"start": 1.5, "duration": 2.0, "text": "mundo"},
        ]
        assert transcript_to_text(transcript) == "Olá mundo"

    def test_lista_vazia_retorna_string_vazia(self):
        # Vídeo sem legenda disponível → lista vazia. Não pode lançar exceção.
        assert transcript_to_text([]) == ""

    def test_preserva_ordem(self):
        # A ordem dos segmentos é cronológica — não pode ser embaralhada
        transcript = [
            {"text": "primeiro"},
            {"text": "segundo"},
            {"text": "terceiro"},
        ]
        resultado = transcript_to_text(transcript)
        assert resultado.index("primeiro") < resultado.index("segundo") < resultado.index("terceiro")


class TestVttTimeToSeconds:
    """
    ERR-04 — Conversão de timestamp VTT para segundos.
    Suporta dois formatos: HH:MM:SS.mmm e MM:SS.mmm
    """

    def test_formato_hh_mm_ss(self):
        assert _vtt_time_to_seconds("00:01:30.500") == pytest.approx(90.5)

    def test_formato_mm_ss(self):
        assert _vtt_time_to_seconds("01:30.500") == pytest.approx(90.5)

    def test_horas_zeradas(self):
        assert _vtt_time_to_seconds("00:00:05.000") == pytest.approx(5.0)

    def test_horas_com_valor(self):
        assert _vtt_time_to_seconds("01:00:00.000") == pytest.approx(3600.0)


class TestParseVtt:
    """
    ERR-04 — Parser VTT extrai segmentos com timestamps reais.

    O YouTube gera VTT com entradas duplicadas para animação de karaokê —
    o parser deve deduplicar pelo texto para não gerar segmentos repetidos.
    Tags HTML como <c> e <00:00:01.000> devem ser removidas.
    """

    VTT_SIMPLES = """WEBVTT

00:00:00.000 --> 00:00:02.500
Olá pessoal

00:00:02.500 --> 00:00:05.000
hoje vamos falar sobre Python
"""

    VTT_COM_TAGS = """WEBVTT

00:00:01.000 --> 00:00:03.000
<c>texto</c> <00:00:01.500><c>com tags</c>

00:00:03.000 --> 00:00:05.000
linha limpa
"""

    VTT_DUPLICADO = """WEBVTT

00:00:00.000 --> 00:00:02.000
primeira frase

00:00:00.500 --> 00:00:02.000
primeira frase

00:00:02.000 --> 00:00:04.000
segunda frase
"""

    def test_extrai_texto_simples(self):
        segs = _parse_vtt(self.VTT_SIMPLES)
        assert len(segs) == 2
        assert segs[0]['text'] == "Olá pessoal"
        assert segs[1]['text'] == "hoje vamos falar sobre Python"

    def test_timestamps_corretos(self):
        segs = _parse_vtt(self.VTT_SIMPLES)
        assert segs[0]['start'] == pytest.approx(0.0)
        assert segs[0]['duration'] == pytest.approx(2.5)
        assert segs[1]['start'] == pytest.approx(2.5)

    def test_remove_tags_html(self):
        segs = _parse_vtt(self.VTT_COM_TAGS)
        assert "<c>" not in segs[0]['text']
        assert "<" not in segs[0]['text']
        assert "texto" in segs[0]['text']

    def test_deduplica_entradas_repetidas(self):
        # YouTube duplica entradas para animação — só deve aparecer uma vez
        segs = _parse_vtt(self.VTT_DUPLICADO)
        textos = [s['text'] for s in segs]
        assert textos.count("primeira frase") == 1

    def test_vtt_vazio_retorna_lista_vazia(self):
        assert _parse_vtt("WEBVTT\n\n") == []


class TestParseJson3:
    """
    ERR-04 — Parser json3 com suporte aos dois formatos de campo de timestamp.
    YouTube usa 'tStartMs'/'dDurationMs' OU 't'/'d' dependendo da versão da API.
    """

    def test_formato_t_d(self):
        data = {'events': [
            {'t': 1000, 'd': 2000, 'segs': [{'utf8': 'texto A'}]},
            {'t': 3000, 'd': 1500, 'segs': [{'utf8': 'texto B'}]},
        ]}
        segs = _parse_json3(data)
        assert segs[0]['start'] == pytest.approx(1.0)
        assert segs[0]['duration'] == pytest.approx(2.0)
        assert segs[0]['text'] == 'texto A'

    def test_formato_tStartMs(self):
        data = {'events': [
            {'tStartMs': 500, 'dDurationMs': 1000, 'segs': [{'utf8': 'olá'}]},
        ]}
        segs = _parse_json3(data)
        assert segs[0]['start'] == pytest.approx(0.5)
        assert segs[0]['duration'] == pytest.approx(1.0)

    def test_ignora_segmentos_vazios(self):
        data = {'events': [
            {'t': 0, 'd': 1000, 'segs': [{'utf8': ''}]},
            {'t': 1000, 'd': 1000, 'segs': [{'utf8': 'real'}]},
        ]}
        segs = _parse_json3(data)
        assert len(segs) == 1
        assert segs[0]['text'] == 'real'

    def test_events_vazio_retorna_lista_vazia(self):
        assert _parse_json3({}) == []
        assert _parse_json3({'events': []}) == []
