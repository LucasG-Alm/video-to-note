# 🎥 Videos to Notes – Organize seu Conhecimento em Markdown

Transforme vídeos em notas estruturadas no Obsidian.  
Resumos automáticos, transcrição, templates personalizáveis e muito mais.  

> ⚠️ **Uso Pessoal & Educacional:**  
> Este projeto não distribui nem incentiva a reprodução de conteúdos protegidos por direitos autorais. Seu objetivo é servir como ferramenta pessoal de organização de conhecimento a partir de conteúdos de uso próprio ou de acesso livre.

---

## 🧠 Funcionalidades
- 🎥 **Videos e audios locais:** Processamentos de arquivos locais salvos em data\01. videos
- 🎯 **Transcrição Automática:** Convertendo vídeo → áudio → texto (via Whisper).
- 📝 **Geração de Notas Markdown:** Organizadas com resumo, tópicos, palavras-chave e questionamentos.
- 🔗 **Organização para Obsidian:** Compatível com Zettelkasten, mapas mentais e sistemas de PKM.
- 🌐 **Suporte a YouTube:** Processamento de vídeos do youtube via links.
- 🎨 **Templates Personalizados:** Layout das notas 100% configurável.
- 📂 **Gestão Visual (via Streamlit):** Interface para controlar todo o fluxo.

---

## 🚀 Tecnologias Utilizadas
- 🐍 **Python 3.10+**
- 📜 **Whisper** – Transcrição automática
- 🎥 **YouTube API** – Metadados e Transcrição
- 📊 **Streamlit** – Interface gráfica
- 🗄️ **MongoDB** (planejado) – Banco de dados para escalabilidade
- 🧠 **Poetry** – Gerenciamento de dependências

---
## 🗂️ Estrutura do Projeto
```
src/
├── core/                # Núcleo do projeto
│   ├── file_handler.py
│   ├── notes.py
│   ├── converter.py
│   ├── audio.py
│   └── __init__.py
│
├── services/            # Serviços externos
│   ├── transcription.py
│   ├── youtube.py
│   ├── youtube-ai.py
│   ├── mongodb.py
│   └── __init__.py
│
├── utils/               # Funções auxiliares
│   ├── utils.py
│   └── __init__.py
│
├── templates/           # Templates de notas
│   ├── template_youtube.md
│   └── template_curso.md
│
├── app_youtube.py       # Interface para YouTube
├── prompts.py           # Prompts e textos auxiliares
├── __init__.py
└── app.py               # Interface principal (Streamlit)


data/
├── 01. videos/          # Vídeos de entrada
│   └── *Estrutura de pastas desejada*/
├── 02. audio/           # Áudios extraídos
│   ├── Youtube/
│   └── *Estrutura de pastas desejada*/
├── 03. transcriptions/  # Transcrições em texto
│   ├── Youtube/
│   └── *Estrutura de pastas desejada*/
├── 04. notes/           # Notas Markdown geradas
│   ├── Youtube/
│   └── *Estrutura de pastas desejada*/
```

---
## 🚀 Como Usar

### ✅ Pré-requisitos
- Python 3.10 ou superior
- Instalar dependências:

```bash
poetry install
```

### ✅ Passo a Passo
1. 🎥 Coloque os vídeos em data/videos/.

2. 🚀 Execute:
```bash
poetry run python src/app.py
```
3. 🖥️ A interface Streamlit abrirá. Nela, você pode:
- 🔊 Extrair áudio dos vídeos
- 📝 Transcrever com Whisper
- ✍️ Gerar notas com resumos, tópicos e questionamentos
- 🎯 Organizar tudo no padrão Obsidian

### 🌐 Integração com YouTube
O projeto permite gerar notas diretamente a partir de links do YouTube.

Funciona assim: (em anadamento)
1. Cole a url do video em youtube.py
2. Extrai metadados (título, canal, descrição, data)
3. Obtém transcrição (quando disponível)
4. Gera a nota Markdown

Execute:
```bash
poetry run python src/app_youtube.py
```

# 🗺️ Roadmap e Futuro
|🔥 Funcionalidade|🚧 Status|
|------------------|--------|
|Criar testes|🕐 Planejado|
|Armazenamento MongoDB|🕐 Planejado|
|Templates Dinâmicos|🕐 Em Progresso|
|Gerador de Templates|🕐 Planejado|
|Auto-Linkagem Inteligente|🕐 Ideia|
|Plugin para Obsidian|🕐 Visão Futuro|
|Videos Longos no Youtube | 🕐 Planejado|

## 💡 Ideias Futuras
- Geração automática de templates baseados em exemplos.
- Detecção de tópicos recorrentes no vault (Análise de Grafo).
- Auto-Linkagem entre notas.

# 📜 Licença
MIT License – Use, adapte, compartilhe, só não seja um vacilão. 😎

---

## 🆕 Novidades e Atualizações

### Funcionalidades Recentes
- 🖥️ **Interface Streamlit para Vídeos Locais:**
  - Visualize o status de vídeos, áudios, transcrições e notas em uma interface interativa.
  - Permite processar arquivos manualmente ou em lote (extrair áudio, transcrever, gerar nota).
  - Edição rápida do status dos arquivos e processamento por caminho manual.
- 📝 **Nova Pipeline de Notas (notes2.py):**
  - Geração de notas Markdown a partir de templates dinâmicos com variáveis.
  - Integração com LLM (LangChain + Groq) para resumos e estruturação automática.
  - Metadados enriquecidos, como duração formatada e preenchimento automático de campos.
- 🗄️ **Integração com MongoDB:**
  - Modelos Pydantic para vídeos e transcrições.
  - Scripts de exemplo para salvar e consultar dados no banco.
  - Estrutura pronta para escalabilidade e armazenamento centralizado.
- 🎬 **Aprimoramentos YouTube:**
  - Extração de metadados mais completa e robusta.
  - Download de áudio e fallback para transcrição via Whisper caso não haja legenda.
  - Funções para sanitizar nomes de arquivos e organizar melhor os dados.

### Mudanças na Estrutura do Projeto
- Nova pasta `src/interfaces/` para interfaces gráficas (ex: local-videos.py).
- Nova pasta `src/services/mongo/` para integração e modelos do MongoDB.
- Novo arquivo `notes2.py` em `src/core/` para pipeline de notas baseada em templates.
- Modularização aprimorada e separação clara entre core, serviços, utilitários e interfaces.