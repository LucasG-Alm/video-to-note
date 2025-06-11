import os
from datetime import datetime
import subprocess

# Configurações
pasta_projeto = "."  # ou coloque o caminho do seu projeto
pasta_logs_obsidian = "logs_git"  # subpasta onde salvará o log .md
os.makedirs(pasta_logs_obsidian, exist_ok=True)

# Data
hoje = datetime.now()
data_str = hoje.strftime("%Y-%m-%d")
hora_str = hoje.strftime("%H:%M:%S")

# Lista de arquivos modificados hoje
modificados = []
for root, dirs, files in os.walk(pasta_projeto):
    for file in files:
        caminho = os.path.join(root, file)
        if ".git" in caminho:
            continue
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(caminho))
            if mod_time.date() == hoje.date():
                modificados.append((caminho, mod_time.strftime("%H:%M:%S")))
        except:
            continue

# Criar conteúdo do markdown
log = [f"# 🚀 Log de Progresso – {data_str}\n"]
log.append(f"**Horário do log:** {hora_str}\n")
log.append(f"**Total de arquivos modificados:** {len(modificados)}\n\n")

for path, hora in modificados:
    log.append(f"- `{path}` (modificado às {hora})")

conteudo_md = "\n".join(log)

# Salva o log no formato Obsidian
arquivo_log = os.path.join(pasta_logs_obsidian, f"log_{data_str}.md")
with open(arquivo_log, "w", encoding="utf-8") as f:
    f.write(conteudo_md)

print(f"✅ Log salvo em: {arquivo_log}")

# Commit automático (opcional)
try:
    subprocess.run(["git", "add", "."], cwd=pasta_projeto)
    subprocess.run(["git", "commit", "-m", f"📅 Progresso automático – {data_str}"], cwd=pasta_projeto)
    print("✅ Commit automático feito com sucesso.")
except Exception as e:
    print("⚠️ Não foi possível commitar automaticamente:", e)
