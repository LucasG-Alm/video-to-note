"""
Testes unitários para src/core/notes2.py

Testamos as funções de template e formatação — o motor que transforma
a transcrição bruta numa nota Obsidian estruturada.
Nenhum teste aqui chama a API da Groq.
"""
import pytest
from src.core.notes2 import gerar_capitulos_formatado, preencher_variables, ler_md_template


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
