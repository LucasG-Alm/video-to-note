# 🧠 MTN CLI Update — Issue

## 🎯 Objetivo
Simplificar a interface do CLI do projeto Media to Notes (MTN), reduzindo fricção para uso humano e integração com IA-CLI.

---

## ❗ Problema Atual
O CLI atual exige comandos mais verbosos e decisões adicionais:
- Uso de subcomandos (`youtube`, `local`)
- Necessidade de passar parâmetros como `--output`
- Maior carga cognitiva para IA (precisa decidir fluxo antes de executar)

Isso gera:
- Mais tokens utilizados por IA
- Mais etapas de execução
- Maior chance de erro
- Experiência menos fluida no terminal

---

## 🚀 Resultado Esperado
Permitir execução simples e direta com um único comando:

```bash
mtn "<input>" -d <nivel>
```

Exemplos:
```bash
mtn "https://youtube.com/..." 
mtn "https://youtube.com/..." -d avancado
mtn "C:/videos/aula.mp4" -d raso
```

Com comportamento:
- Detectar automaticamente se é URL ou arquivo local
- Usar profundidade padrão se não informada
- Usar diretório padrão configurado se não informado

---

## 🧩 Escopo da Implementação

### 1. Unificação de Entrada
- Criar comando principal que recebe `input_source`
- Detectar automaticamente:
  - URL YouTube → pipeline youtube
  - Caminho local → pipeline local

### 2. Configuração Padrão
Adicionar suporte a:
- `DEFAULT_OUTPUT_DIR`
- `DEFAULT_DEPTH` (já existe, manter)
- `DEFAULT_MODEL` (manter)
- `DEFAULT_LANG` (manter)

Fonte:
- `.env` ou `config.toml`

### 3. Interface Simplificada
Novo padrão:

```bash
mtn "<input>" [-d nivel] [-o output]
```

### 4. Manter Compatibilidade
- Preservar comandos:
  - `mtn youtube`
  - `mtn local`
- Marcar como uso avançado (não principal)

---

## 🛠️ Como Implementar

### Etapa 1 — Criar comando raiz
- Adicionar função principal no Typer sem subcomando
- Receber argumento `input_source`

### Etapa 2 — Detectar tipo de entrada
Pseudo-lógica:

```python
if input.startswith("http"):
    usar youtube_to_notes
elif os.path.exists(input):
    usar local_to_notes
else:
    erro claro
```

### Etapa 3 — Configuração padrão
- Criar variável `DEFAULT_OUTPUT_DIR`
- Se `output` for None → usar default

### Etapa 4 — Ajustar CLI
- Tornar `depth` opcional com fallback
- Tornar `output` opcional com fallback

---

## 🧱 Dependências / Tecnologias
- Typer (já em uso)
- Python stdlib (`os`, `pathlib`)
- Config via `.env` ou arquivo próprio

---

## ⚠️ Regras Importantes (Para IA)
- NÃO alterar pipelines (`youtube_to_notes`, `local_to_notes`)
- NÃO mudar lógica de geração de notas
- Apenas ajustar interface do CLI
- Manter compatibilidade com comandos existentes
- Evitar adicionar complexidade desnecessária

---

## ✅ Critérios de Aceite
- [ ] Comando `mtn "<input>"` funciona
- [ ] Detecta corretamente URL vs arquivo local
- [ ] Usa profundidade padrão corretamente
- [ ] Usa diretório padrão corretamente
- [ ] Subcomandos antigos continuam funcionando
- [ ] Código continua simples e legível

---

## 🧠 Motivação Estratégica
- Reduzir tokens e decisões para IA-CLI
- Melhorar experiência no terminal
- Preparar o projeto para uso recorrente
- Evoluir de “projeto” para “ferramenta”

---

## 🏁 Definição de Pronto
A tarefa está concluída quando:
- Um usuário ou IA consegue rodar o MTN com **1 comando simples**
- Sem precisar conhecer a estrutura interna do projeto
