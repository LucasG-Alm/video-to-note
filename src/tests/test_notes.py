import sys
import os
import time
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.core.notes2 import gerar_nota_md
from src.core.file_handler import listar_arquivos


transcricoes = listar_arquivos('data\\03. transcriptions\\Plataforma_Finclass')
#print(transcricoes)

for t in transcricoes:
  print(t)
  gerar_nota_md(
    path_transcricao_json=t,
    path_template_md="D:\\Users\\Lucas\\OneDrive\\Documentos\\PROGRAMAÇÃO\\Python\\Doc courses\\templates\\template_curso.md",
    metadata={
    "curso": "Inteligência Financeira",
    "area": "Finanças",
    "tags_md": "Curso\n    - Finanças/Finclass/Finclasses"
    }
  )
  delay = random.uniform(90, 150)
  print(f"Aguardando {round(delay,2)} segundos pra não tomar bloco 🚫")
  time.sleep(delay)