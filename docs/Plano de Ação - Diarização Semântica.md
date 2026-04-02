# Plano de Ação: Diarização Semântica (Speaker ID) no MTN

## 1. Objetivo
Transformar a transcrição bruta (monolítica) em um diálogo estruturado, identificando quem são os participantes e atribuindo as falas/insights a cada um deles. Isso elevará a qualidade das notas de podcasts e entrevistas no Obsidian.

## 2. Metodologia (Como e Por que foi feito)
No teste realizado hoje, identifiquei 3 pessoas no vídeo da PodPeople usando:
- **Análise de Metadados:** Título e descrição geralmente contêm o nome do convidado e dos hosts.
- **Análise Semântica Inicial:** Os primeiros minutos de um vídeo costumam ter apresentações formais ("Olá, sou a Bia, estamos aqui com Alex e nossa convidada...").
- **Padrão de Turno:** Identifiquei quem pergunta (Host), quem complementa (Co-host) e quem dá respostas longas (Convidado).

**Por que essa abordagem?** Porque é mais barata e rápida que uma diarização baseada em áudio (que exige re-processar arquivos pesados) e aproveita o contexto que o LLM já possui sobre o mundo.

## 3. Estratégia de Implementação

### Fase 1: O Perfilador (`src/services/speakers.py`)
Criar uma função `get_speaker_profile(metadata, sample_text)` que:
1. Recebe o título, descrição e os primeiros 5.000 caracteres da transcrição.
2. Pergunta ao LLM: "Quem são os participantes? Defina um ID curto para cada um (ex: Host, Convidado, Nome Próprio)."
3. Retorna um objeto `SpeakerProfile`.

### Fase 2: Integração no Pipeline (`src/pipeline.py`)
1. Antes de chamar a geração de notas, o pipeline aciona o `speakers.py`.
2. O perfil detectado é injetado no contexto global da nota.

### Fase 3: Refinamento de Prompt (`src/core/notes2.py`)
1. Atualizar o prompt de resumo de capítulos para:
   > "Considerando os falantes: {speaker_profile}, identifique quem disse o quê e formate como **Nome:** [Resumo]."
2. Ajustar os templates para incluir uma seção opcional `## Participantes`.

## 4. Próximos Passos Técnicos
1. [ ] Criar `src/services/speakers.py`.
2. [ ] Adicionar testes unitários em `tests/test_speakers.py`.
3. [ ] Modificar `_gerar_nota_por_capitulos` para aceitar o perfil.
