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
├── core/ # Núcleo do projeto
│ ├── file_handler.py # Gerenciamento de arquivos
│ └── audio_handler.py # Manipulação de áudio
│
├── services/ # Serviços externos
│ └── transcription.py # Serviço de transcrição (Whisper)
│
├── utils/ # Funções auxiliares e prompts
│
├── data/ # Dados
│ ├── videos/ # Vídeos de entrada
│ ├── audio/ # Áudios extraídos
│ ├── transcriptions/ # Transcrições em texto
│ └── notes/ # Notas Markdown geradas
│
└── app.py # Interface Streamlit principal
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

## 💡 Ideias Futuras
- Geração automática de templates baseados em exemplos.
- Detecção de tópicos recorrentes no vault (Análise de Grafo).
- Auto-Linkagem entre notas.

# 🙋‍♂️ Sobre o Autor
👋 Lucas — Tecnólogo em Edifícios, aficionado por dados e eterno curioso.
Apaixonado por conhecimento, automações e IA aplicadas à vida real.
Se quiser trocar uma ideia, colaborar ou sugerir melhorias, bora conversar!

# 📜 Licença
MIT License – Use, adapte, compartilhe, só não seja um vacilão. 😎