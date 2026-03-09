# CashU | Validador de Base

Aplicação Streamlit para upload, validação e normalização de datasets BNPL (Buy Now Pay Later) antes da ingestão no pipeline de dados.

## Visão Geral

O validador recebe um arquivo (Excel ou CSV) enviado pelo usuário, executa um pipeline de 6 etapas de validação e processamento, e disponibiliza o arquivo normalizado para download caso todas as validações sejam aprovadas.

## Arquitetura

```
sales_validador_base/
├── app.py                    # Ponto de entrada Streamlit (página única)
├── config.py                 # Stub de configuração (compatibilidade com shared/)
├── requirements.txt          # Dependências Python
├── validator/                # Lógica de validação e processamento
│   ├── __init__.py
│   ├── schemas.py            # Schemas esperados, limites de nulos, mapa de tipos
│   └── engine.py             # Motor de validação, normalização DuckDB, estatísticas
└── shared/                   # Design system (copiado do whitelabel_dashboard)
    ├── __init__.py
    ├── styles.py             # Cores, CSS, estilos de tabela
    ├── db.py                 # Camada de conexão (não utilizada, mantida por compatibilidade)
    └── components/
        ├── __init__.py
        ├── charts.py         # Componentes de gráficos Plotly
        ├── chiclet.py        # Seletor de filtros
        └── table.py          # Tabela com headers agrupados
```

## Pipeline de Validação

O pipeline é executado sequencialmente. Erros críticos interrompem a execução nos passos 1 e 2.

### Etapa 1 — Validação Pré-processamento

Verifica o arquivo bruto antes de qualquer transformação:

- **Colunas obrigatórias**: confirma que todas as colunas definidas no schema existem no arquivo.
- **Tipos de dados**: verifica compatibilidade básica (modo não-estrito). Divergências são reportadas como avisos, pois o passo 2 tentará corrigir.

Se houver colunas obrigatórias faltando, o pipeline é interrompido.

### Etapa 2 — Normalização dos Dados (DuckDB)

Executa uma query DuckDB sobre o DataFrame em memória para padronizar os dados:

| Campo | Transformação |
|---|---|
| `cliente_cnpj`, `emitente_cnpj` | Remove caracteres não-numéricos, aplica zero-padding (11 dígitos para CPF, 14 para CNPJ) |
| `id_pedido`, `id_cliente`, `id_parcela`, `forma_pagamento` | Cast para `VARCHAR` |
| `data_pedido`, `data_vencimento`, `data_pagamento` | Tenta parse em múltiplos formatos: `DATE` nativo, `dd/mm/yyyy`, `yyyy-mm-dd` |
| `valor_parcela`, `valor_pago` | Detecta formato numérico brasileiro (`1.234,56`) e americano (`1,234.56`), converte para `DOUBLE` |

Se a normalização falhar (ex: coluna inexistente referenciada na query), o pipeline é interrompido.

### Etapa 3 — Validação Pós-processamento

Verifica o DataFrame normalizado em modo **estrito**:

- Todas as colunas do schema devem existir.
- Os tipos Pandas devem corresponder exatamente aos tipos esperados (`datetime64` para datas, `float64` para numéricos, `object` para strings).

Erros nesta etapa indicam que a normalização não conseguiu converter algum campo corretamente. O download é bloqueado, mas o pipeline continua para exibir estatísticas.

### Etapa 4 — Estatísticas dos Dados

Gera uma tabela com métricas por coluna:

| Métrica | Descrição |
|---|---|
| Total Linhas | Contagem total de registros |
| Únicos | Valores distintos (excluindo nulos) |
| Nulos / Nulos % | Contagem e percentual de valores nulos |
| Mín / Máx | Valor mínimo e máximo (numéricos e datas) |
| Média | Média aritmética (apenas numéricos) |

### Etapa 5 — Limites de Nulos

Verifica se colunas críticas não excedem o limite máximo de nulos permitido:

| Coluna | Máximo de nulos permitido |
|---|---|
| `cliente_cnpj` | 0 |
| `id_pedido` | 0 |
| `data_pedido` | 0 |
| `data_vencimento` | 0 |
| `valor_parcela` | 0 |
| `forma_pagamento` | 0 |

### Etapa 6 — Regras de Negócio

Validações de consistência lógica dos dados:

| Regra | Condição de erro |
|---|---|
| Consistência de datas (pagamento) | `data_pagamento` anterior a `data_pedido` |
| Consistência de datas (vencimento) | `data_vencimento` anterior a `data_pedido` |
| Valor de parcela positivo | `valor_parcela <= 0` |
| Valor pago não-negativo | `valor_pago < 0` |

Cada violação reporta a quantidade de linhas afetadas e o percentual sobre o total.

## Schema Esperado

O arquivo de entrada deve conter as seguintes colunas:

| Coluna | Tipo | Descrição |
|---|---|---|
| `emitente_cnpj` | str | CNPJ do emitente |
| `cliente_cnpj` | str | CPF/CNPJ do cliente |
| `id_cliente` | str | Identificador do cliente |
| `id_pedido` | str | Identificador do pedido |
| `id_parcela` | str | Identificador da parcela |
| `forma_pagamento` | str | Forma de pagamento |
| `data_pedido` | date | Data do pedido |
| `data_vencimento` | date | Data de vencimento da parcela |
| `data_pagamento` | date | Data do pagamento (pode ser nula) |
| `valor_parcela` | float | Valor da parcela |
| `valor_pago` | float | Valor efetivamente pago |

## Download do CSV Validado

O botão de download na sidebar só é habilitado quando **todas** as validações dos passos 3, 5 e 6 passam sem erros. O arquivo gerado é um CSV UTF-8 com os dados já normalizados.

Avisos do passo 1 (pré-processamento) **não** bloqueiam o download, pois são resolvidos pela normalização do passo 2.

## Como Executar

```bash
cd sales_validador_base
pip install -r requirements.txt
streamlit run app.py
```

## Configuração da Sidebar

| Controle | Descrição |
|---|---|
| **Tipo de Arquivo** | Dropdown: `Excel` ou `CSV` |
| **Nome da Aba** | Aparece quando Excel é selecionado. Nome da sheet a ser lida (padrão: `Preencher`) |
| **Separador** | Aparece quando CSV é selecionado. Opções: vírgula, ponto e vírgula, tab, pipe |
| **Upload do Arquivo** | Aceita `.xlsx`/`.xls` para Excel ou `.csv`/`.txt` para CSV |

## Dependências

| Pacote | Uso |
|---|---|
| `streamlit` | Interface web |
| `pandas` | Manipulação de DataFrames |
| `numpy` | Operações numéricas (dependência do design system) |
| `duckdb` | Normalização SQL em memória |
| `openpyxl` | Leitura de arquivos Excel (.xlsx) |
| `plotly` | Gráficos (dependência do design system) |
| `python-dotenv` | Carregamento de variáveis de ambiente |
