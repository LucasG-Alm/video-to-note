"""
Testes unitários para src/services/youtube.py

Testamos apenas funções puras — sem chamadas de API, sem rede, sem disco.
São o contrato do que cada função DEVE fazer. Se alguém mudar o comportamento
acidentalmente, o teste quebra e avisa antes de chegar em produção.
"""
import pytest
from src.services.youtube import extract_video_id, sanitize_filename, transcript_to_text


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
