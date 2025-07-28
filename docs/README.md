# Videos to Notes 

Esse projeto tem como objetivo automatizar a criação de notas markdown para um sistema Obsidian Zettelkalsten a partir de videos locais e auxiliar na documentação de conteudos, com resumos, palavras-chave, e questionamentos dos temas abordados. 

Atualmente, funciona apenas com arquivos locais salvos em [[data/01. videos]], mas estou trabalhando com a API do youtube para gerar notas personalizaveis com base nas url dos videos

Lembrando q os layout das notas é totalmente personalizavel, bastal alterar os arquivos em [[src/templates]]

> ⚠️ Este projeto não inclui nem incentiva a distribuição de conteúdos protegidos por direitos autorais.  
Ele serve como ferramenta pessoal de organização de conhecimento a partir de conteúdos de acesso livre ou de uso pessoal.

## Tecnologias Utilizadas
- Python 3.10+
- Streamlit
- Whisper (transcrição)
- yt-dlp (YouTube)
- MongoDB (planejado)
- Poetry (gerenciamento de dependências)


## Estrutura do Projeto
```
src/
├── core/                    # Núcleo do projeto
│   ├── __init__.py
│   ├── file_handler.py     # Gerenciamento de arquivos
│   └── audio_handler.py    # Manipulação de áudio
│
├── services/               # Serviços externos
│   ├── __init__.py
│   └── transcription.py    # Serviço de transcrição
│
├── utils/                  # Utilitários
│   ├── __init__.py
│   ├── prompts.py         # Templates de prompts
│   └── helpers.py         # Funções auxiliares
│
├── data/                   # Dados do projeto
│   ├── videos/            # Vídeos das aulas
│   ├── audio/             # Áudios extraídos
│   ├── transcriptions/    # Transcrições
│   └── notes/             # Notas e resumos
│
└── app.py                 # Aplicação principal
```
## Como Usar
1. Coloque os vídeos das aulas na pasta `data/videos/` na estrutura de pastas desejada
2. Execute o script principal:
   ```bash
   python src/app.py
   ```
3. O sistema irá abrir uma interface streamlit com os arquivos e apartir dos arquivos selecionados, vc poderá:
   - Extrair áudio dos vídeos 
   - Transcrever os áudios (via wisper)
   - Organizar as transcrições
   - Gerar notas e resumos

## Integração com YouTube
O sistema permite processar vídeos diretamente a partir de **links do YouTube**. Basta inserir o link do vídeo e o sistema irá:
- Extrair metadados (título, descrição, canal, data, etc.)
- Obter a transcrição automática (quando disponível)
- Gerar notas organizadas em Markdown a partir do conteúdo do vídeo

Para usar, execute o módulo específico ou utilize a interface Streamlit disponível em `src/app_youtube.py`.

---
## Ideias e Futuro
- **Armazenamento em MongoDB:** Planeja-se migrar o armazenamento das transcrições de arquivos locais para um banco de dados MongoDB, facilitando buscas, organização e escalabilidade.
- **Templates dinâmicos de notas:** O projeto já possui diferentes templates de notas (ex: para vídeos do YouTube ou aulas locais). Futuramente, a IA será treinada para escolher e aplicar automaticamente o template mais adequado conforme o tipo de entrada (vídeo local ou link) e o objetivo do usuário.
- **Gerador de Templates:** Permite q vc carregue uma nota de exemplo ou solicite tópicos e metadados para a IA gerar um template personalizado
- **Personalização de notas:** Possibilidade de salvar e gerenciar diversos templates de notas, permitindo que o usuário escolha ou crie modelos conforme sua necessidade.

---
## Sobre o Autor

