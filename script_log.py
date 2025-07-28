import os
import subprocess
import argparse
from datetime import datetime

def gerar_log_auto(pasta_projeto, pasta_logs_obsidian):
    hoje = datetime.now()
    data_str = hoje.strftime("%Y-%m-%d")
    hora_str = hoje.strftime("%H:%M:%S")

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

    log = [f"# 🚀 Log de Progresso – {data_str}\n"]
    log.append(f"**Total de arquivos alterados:** {len(modificados)}")
    log.append(f"**Duração estimada total:** {len(modificados)*10//60:02d}h{len(modificados)*10%60:02d}min\n")
    log.append("| Arquivo | ⏱️ Tempo Estimado | ➕ Linhas Adicionadas | ➖ Linhas Removidas |")
    log.append("|---------|-------------------|------------------------|---------------------|")
    for path, hora in modificados:
        # Aqui você pode aprimorar para calcular mudanças reais por arquivo
        log.append(f"| `{path}` | 10 min | ? | ? |")

    log.append(f"\n📝 Última modificação às {modificados[-1][1] if modificados else 'N/A'}")
    log.append(f"💾 Log gerado às {hora_str}")

    os.makedirs(pasta_logs_obsidian, exist_ok=True)
    arquivo_log = os.path.join(pasta_logs_obsidian, f"log_{data_str}.md")
    with open(arquivo_log, "w", encoding="utf-8") as f:
        f.write("\n".join(log))

    print(f"✅ Log salvo em: {arquivo_log}")

    # Commit automático
    subprocess.run(["git", "add", "."], cwd=pasta_projeto)
    subprocess.run(["git", "commit", "-m", f"📅 Progresso automático – {data_str}"], cwd=pasta_projeto)
    print("✅ Commit automático feito com sucesso.")

def gerar_diff(commita, commitb, pasta_logs_obsidian):
    hoje = datetime.now()
    data_str = hoje.strftime("%Y-%m-%d")
    hora_str = hoje.strftime("%H:%M:%S")

    diff_output = subprocess.run(["git", "diff", "--numstat", commita, commitb],
                                 capture_output=True, text=True)

    linhas = diff_output.stdout.strip().splitlines()
    total_arquivos = len(linhas)

    log = [f"# 🚀 Log de Progresso – {data_str}\n"]
    log.append(f"**Total de arquivos alterados:** {total_arquivos}")
    log.append(f"**Duração estimada total:** {total_arquivos*10//60:02d}h{total_arquivos*10%60:02d}min\n")
    log.append("| Arquivo | ⏱️ Tempo Estimado | ➕ Linhas Adicionadas | ➖ Linhas Removidas |")
    log.append("|---------|-------------------|------------------------|---------------------|")

    for linha in linhas:
        partes = linha.split("\t")
        if len(partes) == 3:
            add, rem, nome = partes
            log.append(f"| `{nome}` | 10 min | {add} | {rem} |")

    log.append(f"\n💾 Log gerado às {hora_str}")

    os.makedirs(pasta_logs_obsidian, exist_ok=True)
    arquivo_log = os.path.join(pasta_logs_obsidian, f"diff_{commita.replace('/', '_')}_to_{commitb.replace('/', '_')}.md")
    with open(arquivo_log, "w", encoding="utf-8") as f:
        f.write("\n".join(log))

    print(f"✅ Diff salvo em: {arquivo_log}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Gera log automático + commit")
    parser.add_argument("--diff", nargs=2, metavar=("COMMIT_A", "COMMIT_B"), help="Gera diff entre dois commits")
    args = parser.parse_args()

    pasta_projeto = "."
    pasta_logs_obsidian = "logs_git"

    #if args.auto:
    gerar_log_auto(pasta_projeto, pasta_logs_obsidian)
    #elif args.diff:
    #    gerar_diff(args.diff[0], args.diff[1], pasta_logs_obsidian)
    #else:
    #    print("❗ Use --auto ou --diff COMMIT_A COMMIT_B")
