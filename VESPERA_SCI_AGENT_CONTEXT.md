# 🚀 Vespera Sci — Documento de Contexto e Arquitetura para Agentes de IA (Handoff Blueprint)

> **Instrução para o Agente de IA:**  
> Leia este documento integralmente antes de propor ou executar qualquer ação. Ele contém todo o histórico, regras de negócio, dados experimentais, especificações gráficas e o plano de trabalho acordado com o usuário para a construção do software desktop **Vespera Sci**.

---

## ⚠️ REGRA DE OURO DE INTERAÇÃO COM O USUÁRIO
1. **Consulte sempre antes de executar:** O usuário solicitou expressamente ser consultado **antes** do início ou execução de cada etapa. Apresente o que será feito, aguarde o "de acordo" e só então gere/modifique os arquivos.
2. **Idioma:** Português (Brasil).
3. **Repositórios:**
   * **Repositório Legado/Web (Streamlit — Mantido intacto para o TCC):** `https://github.com/Igorhls/malu-tcc.git`
   * **Novo Repositório Oficial (Aplicação Desktop — Vespera Sci):** `https://github.com/Igorhls/vespera-sci.git`

---

## 1. Status Atual das 3 Etapas

* ✅ **Etapa 1 (Concluída):** Setup do repositório `vespera-sci`, documentação oficial (`README.md`) e extração modular completa das camadas `config/` (`themes.py`, `presets.py`) e `core/` (`sanitizer.py`, `plot_engine.py`, `excel_exporter.py`, `project_manager.py`).
* ⏳ **Etapa 2 (Próxima Etapa — Aguardando Aprovação do Usuário):** Construção do aplicativo desktop nativo em **PySide6** (`main.py` e módulos dentro de `ui/`: janela principal, painel lateral de estilo OriginLab, tabela editável com suporte a copiar/colar do Excel, `FigureCanvasQTAgg` com legenda arrastável pelo mouse, calculadora de média/desvio e barra de projetos).
* ⏳ **Etapa 3 (Futura — Após Etapa 2):** Implementação do sistema de **Auto-Update via GitHub** (`core/updater.py` + botão "🔄 Verificar Atualizações" na UI) e empacotamento local (`.exe` / lançador portátil) para a usuária final.

---

## 2. Arquitetura de Diretórios (`vespera-sci`)

```text
vespera-sci/
├── main.py                         # [Etapa 2] Ponto de entrada da aplicação Desktop (PySide6)
├── version.json                    # [Concluído] Versão atual do sistema ("1.0.0")
├── requirements.txt                # [Concluído] PySide6, matplotlib, pandas, numpy, openpyxl, requests
├── README.md                       # [Concluído] Documentação oficial do Vespera Sci
├── VESPERA_SCI_AGENT_CONTEXT.md    # [Concluído] Este documento de referência para agentes de IA
│
├── config/
│   ├── __init__.py                 # [Concluído]
│   ├── presets.py                  # [Concluído] Dados pré-definidos (Dias 14, 16, 19 Ago + TA Barras)
│   └── themes.py                   # [Concluído] Paletas, Fontes, Coordenadas de Legenda e DEFAULT_CONFIG
│
├── core/
│   ├── __init__.py                 # [Concluído]
│   ├── sanitizer.py                # [Concluído] Limpeza de dados colados do Excel, formatação PT-BR e estatísticas
│   ├── plot_engine.py              # [Concluído] Renderização Matplotlib (Linhas e Barras) com leg.set_draggable(True)
│   ├── excel_exporter.py           # [Concluído] Geração de planilhas .xlsx com gráficos nativos (openpyxl)
│   ├── project_manager.py          # [Concluído] Leitura/Gravação de projetos (.vespera / .json)
│   └── updater.py                  # [Etapa 3] Cliente de atualização automática via GitHub (Igorhls/vespera-sci)
│
└── ui/
    ├── __init__.py                 # [Concluído]
    ├── main_window.py              # [Etapa 2] Janela Principal (Menus, Barra de Projetos, Splitters)
    ├── sidebar_controls.py         # [Etapa 2] Painel lateral de estilo (Fontes, Cores, Bordas, Ticks, Legenda)
    ├── data_table_widget.py        # [Etapa 2] Tabela interativa com colagem rápida do Excel e calculadora
    ├── plot_canvas_widget.py       # [Etapa 2] FigureCanvasQTAgg interativo com barra de navegação/exportação
    └── update_dialog.py            # [Etapa 3] Modal de verificação e progresso de atualização do GitHub
```

---

## 3. Especificações Técnicas Já Implementadas no `core/` e `config/`

1. **`config/presets.py`**:
   * `PRESETS_LINHAS`: Contém `"Dia 14 de Agosto"`, `"Dia 16 de Agosto"` e `"Dia 19 de Agosto"` com os pontos `P1` a `P10` e colunas `Manha`, `Tarde`, `Noite`.
   * `PRESETS_BARRAS`: Contém `"TA — Média e Desvio Padrão (Agosto e Dezembro)"` com colunas `Mes`, `Bosque`, `Desvio_Bosque`, `Estacionamento`, `Desvio_Estacionamento`.
2. **`config/themes.py`**:
   * `PALETAS_LINHAS`, `PALETAS_BARRAS`, `FONTES_DISPONIVEIS`, `POSICOES_LEGENDA`, `COORDENADAS_LEGENDA_PRESET` e `DEFAULT_CONFIG`.
3. **`core/sanitizer.py`**:
   * `sanitizar_dados_tabela(df)`: Corrige números colados do Excel sem vírgula (ex: `274` -> `27.4`) e preenche `P1..Pn`.
   * `sanitizar_dados_barras(df)`: Sanitiza valores da tabela de Média e Desvio Padrão.
   * `formatar_numero_ptbr(valor, modo_formato)`: Formata números com vírgula decimal (`27,32`, `2,3`).
   * `calcular_estatisticas_serie(valores)`: Retorna `n`, `media`, `desvio` (amostral `ddof=1`), `minimo`, `maximo`, `amplitude`.
4. **`core/plot_engine.py`**:
   * `renderizar_grafico_linhas(..., fig=None)` e `renderizar_grafico_barras(..., fig=None)`: Podem receber uma instância `Figure` existente do `FigureCanvasQTAgg` (limpando e redesenhando com `fig.clear()`) ou criar uma nova figura para exportação. Já ativa `leg.set_draggable(True)`.
5. **`core/excel_exporter.py`**:
   * `gerar_excel_linhas_bytes(...)` e `gerar_excel_barras_bytes(...)`: Geram os bytes do arquivo `.xlsx` com tabela formatada e gráfico nativo do Excel (`LineChart` / `BarChart`).
6. **`core/project_manager.py`**:
   * Classe `ProjectManager`: Lê e grava `projetos_salvos.json` e empacota o estado completo do projeto com `construir_payload(...)`.
