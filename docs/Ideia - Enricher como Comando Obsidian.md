---
tags:
  - Programação/Inteligencia_Artificial_IA
  - Programação/Desenvolvimento
status: inbox
data_nota: 2026-03-20
revisao:
---

# Ideia — Enricher como Comando Obsidian (Media-to-Notes v2)

> **Status:** Ideia registrada. Implementar apenas após corrigir bugs e melhorar testes da v1.
> Ver pendências em: [[Teste - Sessão 2026-03-20]]

---

## O que é

Uma camada de enriquecimento **separada do pipeline** de geração de nota. Em vez de enriquecer durante o processamento, o enriquecimento acontece **dentro do Obsidian**, sob demanda, como um comando personalizado.

## Por que separar do pipeline

O pipeline (`mtn`) faz o que faz bem: transcrever e montar nota base.
Enriquecer durante o pipeline:
- aumenta custo por vídeo (mesmo quando não precisa)
- torna o processo mais lento e frágil
- mistura responsabilidades

Fora do pipeline, o enriquecimento fica **intencional e cirúrgico** — você aciona quando e onde quer.

## Como funcionaria

Um comando Obsidian (`Enricher: enriquecer seleção` ou similar) que:

1. **Detecta o escopo** — o que enriquecer:
   - Texto selecionado manualmente
   - Conteúdo do bloco H2 ou H3 atual
   - Nota inteira (opcional, mais caro)

2. **Classifica o conteúdo** — extrai automaticamente:
   - Conceitos citados mas não explicados
   - Links na descrição (do frontmatter ou do corpo)
   - Claims que precisam de contexto externo

3. **Consulta fonte de enriquecimento** (configurável):
   - **Perplexity API** — para contexto externo recente, docs oficiais, comparações
   - **notebooklm-py** — para síntese sobre corpus fechado (vídeo + links + PDFs relacionados)
   - **Sem API** — só classificação e detecção de lacunas (modo offline)

4. **Injeta resultado** de volta na nota, como nova seção ou expandindo o bloco atual

## Critério de enriquecimento (filtro anti-ruído)

Só enriquecer se o contexto fizer pelo menos 1 destes:

| Critério | Exemplo |
|----------|---------|
| Explica algo implícito | termo citado mas não definido |
| Valida uma ideia | doc oficial ou fonte forte |
| Amplia aplicação prática | mostra uso real |
| Conecta com tema do vault | LKE, DWG Explorer, estudos |
| Evita interpretação errada | contexto que muda entendimento |

Se não cumprir nenhum: não enriquece. Tesoura também é inteligência.

## Classificação de links da descrição

Links da descrição do vídeo têm qualidade muito variada. O comando classifica antes de processar:

| Tipo | Ação |
|------|------|
| Documentação oficial | priorizar e resumir |
| Artigo técnico | resumir |
| Vídeo complementar | referenciar |
| Produto/ferramenta citada | resumir se relevante |
| Propaganda / afiliado / social | ignorar |
| Link morto / paywall / login | marcar |

## Arquitetura futura do pipeline completo

```
Media input
  → Extractor (transcript + descrição + links + metadados)
  → Composer (Claude — nota base no template Obsidian)
  → [salvo no vault]

[dentro do Obsidian, sob demanda]
  → Enricher (comando personalizado)
      → Link Classifier
      → Fonte: Perplexity | notebooklm-py | offline
      → Resultado injetado na nota
```

## Referência

- Conversa com GPT: `ideia-media-to-notes-V2.0.pdf` (2026-03-20)
- Inspiração da sessão de teste: [[Teste - Sessão 2026-03-20]]
- Projeto base: [[Media to Notes]]

## Notas relacionadas

- [[Método Akita de Vibe Coding]] — o enriquecimento resolveria exatamente as lacunas identificadas na nota do Akita
- [[Do Zero a Pos-Producao em 1 Semana - IA em Projetos de Verdade]]
