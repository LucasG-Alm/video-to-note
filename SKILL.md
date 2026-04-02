# Media to Notes Skill (MTN)

Esta skill permite que o Gemini CLI processe vídeos do YouTube ou arquivos locais em notas estruturadas no Obsidian.

## Gatilhos (Trigger Conditions)
Ative esta skill automaticamente quando o usuário:
- Colar uma URL do YouTube (`youtube.com`, `youtu.be`, `/shorts/`).
- Fornecer um caminho de arquivo de áudio ou vídeo (`.mp3`, `.mp4`, `.wav`, `.m4a`, etc.).
- Usar frases como: "gera nota desse vídeo", "resume este áudio", "processa o vídeo: <url>".

## Configuração de Caminhos
- **Projeto:** `Principal/Projetos/Programação/Media to Notes`
- **Output Padrão (Vault Inbox):** `Principal/_revisar`

## Como Executar (Protocolo IA)

### 1. Selecionar Profundidade
Se o usuário não especificar, use `intermediario`.
- `raso`: Bullets rápidos (≤ 10 linhas).
- `intermediario`: Resumo + Pontos principais + Aplicações (Padrão).
- `avancado`: Frameworks + Análise crítica + Interconexões.
- `metacognitivo`: Reflexão profunda + Impacto pessoal.

### 2. Comando de Execução (Global)
Como o projeto está instalado em modo editável (`pip install -e .`), o comando `mtn` está disponível globalmente. A IA deve executá-lo diretamente:

**YouTube:**
```bash
mtn youtube "<URL>" --depth <DEPTH> --output "Principal/_revisar"
```

**Local:**
```bash
mtn local "<CAMINHO_ARQUIVO>" --depth <DEPTH> --output "Principal/_revisar"
```

*Nota: O Gemini CLI deve garantir que o caminho de `--output` seja resolvido corretamente em relação à raiz do workspace.*

## Requisitos
- `GROQ_API_KEY` configurada no `.env` do projeto.
- FFmpeg instalado no sistema.
- Poetry instalado.

## Notas Técnicas
- O sistema tenta capturar legendas automáticas primeiro (yt-dlp).
- Se não houver legenda, usa Groq Whisper (com chunking automático para arquivos > 25MB).
- O Gemini CLI deve reportar o caminho final da nota no Obsidian após o sucesso.
