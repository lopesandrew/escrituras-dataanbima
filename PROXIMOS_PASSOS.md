# Próximos Passos - Escrituras ANBIMA

## Status Atual - Commit: e1f6a6b

### ✅ Concluído até agora:

1. **Script de Extração de Links (`extrator_click_intercept.py`)**
   - ✅ Extrai escrituras de debêntures do site ANBIMA
   - ✅ Usa Selenium Wire para interceptar requisições de rede
   - ✅ Clica nos botões "Baixar" para gerar URLs S3
   - ✅ Processou com sucesso **25 ativos** de `ativos.txt`
   - ✅ Gerou CSV final: `escrituras_FINAL_20251021_155810.csv`

2. **Resultados Obtidos:**
   - ✅ 19 ativos COM escrituras (links S3 capturados)
   - ⚠️ 6 ativos SEM documentos disponíveis
   - ✅ 0 erros de processamento

3. **Arquivos Importantes:**
   - `extrator_click_intercept.py` - Script principal funcionando
   - `ativos.txt` - Lista completa de 25 ativos
   - `ativos_remaining.txt` - 16 ativos restantes (usado na segunda execução)
   - `requirements.txt` - Dependências (selenium, selenium-wire, webdriver-manager)
   - `escrituras_FINAL_20251021_155810.csv` - CSV com todos os links S3

---

## 🚧 Pendente: Módulo de Download de PDFs

### Objetivo:
Criar um módulo que **baixa automaticamente** os PDFs das escrituras a partir do CSV gerado.

### Especificações Aprovadas:

#### 1. **Links a baixar:**
- ⚠️ **TODOS os links únicos** encontrados durante a extração
- **Problema:** O CSV atual (`escrituras_FINAL_*.csv`) só armazena 2 links por ativo (Original e Recente)
- **Solução necessária:** Alguns ativos têm mais escrituras:
  - QMCT14 tem **4 escrituras**
  - BTCL11 tem **5 escrituras**
  - PNXT11 tem **3 escrituras**

#### 2. **Organização dos arquivos:**
- 📁 **Subpastas por empresa**
- Estrutura: `escrituras/QMCT/`, `escrituras/ATBR/`, `escrituras/BTCL/`
- Extrai código da empresa dos primeiros 4 caracteres do ativo

#### 3. **Nomenclatura dos arquivos:**
- 📝 **Nome original do S3** (preservar nome exato)
- Exemplo: `QMCT_4_Escritura - Aditamento_20250814_000.pdf`
- Fazer URL decode para remover %20, etc.

---

## 📋 Tarefas a Implementar:

### Passo 1: Modificar `extrator_click_intercept.py`
- [ ] Adicionar coluna `Todos_Links` no CSV com lista completa de URLs S3
- [ ] Salvar links como string separada por pipe `|` ou como JSON
- [ ] Manter compatibilidade com colunas existentes (Link Original/Recente)

### Passo 2: Criar `downloader_pdfs.py`
- [ ] Ler CSV expandido com todos os links
- [ ] Para cada ativo com escrituras:
  - [ ] Extrair código da empresa (primeiros 4 chars)
  - [ ] Criar subpasta `escrituras/{EMPRESA}/` se não existir
  - [ ] Baixar cada PDF único usando `requests`
  - [ ] Fazer URL decode do nome do arquivo
  - [ ] Salvar com nome original do S3
  - [ ] Evitar re-download se arquivo já existe
  - [ ] Mostrar barra de progresso

### Passo 3: Tratamento de Erros
- [ ] Retry automático (até 3 tentativas) em caso de falha
- [ ] Log de downloads bem-sucedidos
- [ ] Log de falhas
- [ ] Resumo final com estatísticas

### Passo 4: Re-executar Extrator
- [ ] Modificar `extrator_click_intercept.py` para usar arquivo original `ativos.txt`
- [ ] Executar para gerar CSV expandido com TODOS os links
- [ ] Verificar que todos os 25 ativos foram processados

### Passo 5: Executar Downloader
- [ ] Executar `downloader_pdfs.py` no CSV expandido
- [ ] Verificar PDFs baixados na pasta `escrituras/`
- [ ] Conferir resumo de downloads

---

## 🔧 Dependências Adicionais Necessárias:

```python
# Adicionar ao requirements.txt:
requests>=2.31.0
urllib3>=2.0.0
tqdm>=4.65.0  # Para barra de progresso
```

---

## 📊 Estrutura Esperada Após Download:

```
escrituras/
├── QMCT/
│   ├── QMCT_4_Escritura - Aditamento_20250814_000.pdf
│   ├── QMCT_4_Escritura - Aditamento_20250814_001.pdf
│   ├── QMCT_4_Escritura - Aditamento_20250814_002.pdf
│   └── QMCT_4_Escritura - Escritura_20250724_000.pdf
├── ATBR/
│   ├── ATBR_2_Escritura - Aditamento_20250107_000.pdf
│   └── ATBR_2_Escritura - Escritura_20241213_000.pdf
├── BTCL/
│   ├── BTCL_2_Escritura - Aditamento_20250213_000.pdf
│   └── ...
└── ... (outras empresas)
```

---

## 🔗 Links Úteis:

- **Repositório GitHub:** https://github.com/lopesandrew/escrituras-dataanbima
- **Site ANBIMA:** https://data.anbima.com.br/debentures/

---

## 📝 Como Continuar:

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/lopesandrew/escrituras-dataanbima.git
   cd escrituras-dataanbima
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Continue a implementação:**
   - Implemente as tarefas listadas acima
   - Teste com poucos ativos primeiro
   - Depois execute para todos os 25 ativos

4. **Commit das mudanças:**
   ```bash
   git add .
   git commit -m "Add downloader module"
   git push
   ```

---

## 💡 Observações Importantes:

- O script atual (`extrator_click_intercept.py`) está funcionando perfeitamente
- Os links S3 são públicos e podem ser baixados diretamente via HTTP GET
- Não é necessário autenticação para baixar os PDFs
- Alguns ativos não têm escrituras disponíveis no site (6 de 25)
- O CSV final já contém os links necessários, mas precisa ser expandido para incluir TODOS os links

---

**Data:** 21/10/2025
**Último Commit:** e1f6a6b
**Status:** Pronto para implementar módulo de download
