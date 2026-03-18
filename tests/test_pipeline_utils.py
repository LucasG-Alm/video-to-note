"""
Testes unitários para src/pipeline.py

Testamos resolve_template — a função que mapeia um nível de profundidade
para o caminho absoluto do template correto no disco.

Por que testar isso?
→ Se alguém renomear um template ou errar no mapeamento, todos os
  processamentos de um determinado depth vão silenciosamente usar
  o template errado (ou explodir com FileNotFoundError em runtime).
  Melhor descobrir aqui.
"""
import pytest
from pathlib import Path
from src.pipeline import resolve_template, DEPTH_TEMPLATES


class TestResolveTemplate:
    """
    resolve_template recebe um depth (str) e retorna o caminho absoluto
    do template .md correspondente.

    Pseudo-código:
        recebe depth
        busca filename em DEPTH_TEMPLATES (fallback: template_youtube_intermediario.md)
        monta caminho: PROJECT_ROOT / "templates" / filename
        verifica se o arquivo existe no disco
        retorna caminho como string (ou levanta FileNotFoundError)
    """

    def test_raso_aponta_para_template_correto(self):
        # Cada depth tem seu próprio template — confirma o mapeamento
        resultado = resolve_template("raso")
        assert resultado.endswith("template_youtube_raso.md")

    def test_intermediario_aponta_para_template_correto(self):
        resultado = resolve_template("intermediario")
        assert resultado.endswith("template_youtube_intermediario.md")

    def test_avancado_aponta_para_template_correto(self):
        resultado = resolve_template("avancado")
        assert resultado.endswith("template_youtube_avancado.md")

    def test_metacognitivo_aponta_para_template_correto(self):
        resultado = resolve_template("metacognitivo")
        assert resultado.endswith("template_youtube_metacognitivo.md")

    def test_todos_os_templates_existem_no_disco(self):
        # Garante que nenhum template foi renomeado ou deletado acidentalmente
        for depth in DEPTH_TEMPLATES:
            caminho = resolve_template(depth)
            assert Path(caminho).exists(), f"Template ausente para depth='{depth}': {caminho}"

    def test_depth_desconhecido_cai_no_intermediario(self):
        # DEPTH_TEMPLATES.get(depth, fallback) — depth inválido não deve explodir
        resultado = resolve_template("nao_existe")
        assert resultado.endswith("template_youtube_intermediario.md")

    def test_retorna_string(self):
        # gerar_nota_md espera str, não Path
        resultado = resolve_template("raso")
        assert isinstance(resultado, str)
