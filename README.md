# 🌌 Vespera Sci — Scientific Plotting & Data Analysis Studio

**Vespera Sci** é uma plataforma desktop científica modular para análise de dados experimentais, estatística descritiva e produção de figuras de alta precisão com padrão editorial internacional (*OriginLab Pro*, *Nature*, *Science*, *ABNT*).

* **Repositório Oficial:** [https://github.com/Igorhls/vespera-sci.git](https://github.com/Igorhls/vespera-sci.git)
* **Origem Acadêmica (Versão Web Streamlit):** [VZN EcoClima (`malu-tcc`)](https://github.com/Igorhls/malu-tcc.git)

---

## ✨ Principais Recursos

* 🖥️ **Aplicação Desktop Nativa (PySide6 / Qt):** Desempenho fluido, execução 100% local/offline e interface adaptativa a temas claros e escuros.
* 🖱️ **Canvas Matplotlib Interativo:** Arraste a legenda diretamente com o cursor do mouse sobre o gráfico (`draggable legend`), aplique zoom, pan e visualize alterações estéticas em tempo real sem recarregamentos de página.
* 📊 **Múltiplos Modos Gráficos Científicos:**
  * **Séries Espaço-Temporais (Gráfico de Linhas $P_1\text{–}P_n$):** Monitoramento por pontos amostrais com controle individual de séries visíveis, marcadores geométricos e estilos de linha (sólido, tracejado, pontilhado).
  * **Comparativos de Média e Desvio Padrão (Barras Agrupadas):** Rótulos automáticos no topo das barras formatados no padrão nacional (vírgula decimal) e largura de agrupamento ajustável.
* 📐 **Controle Milimétrico Estilo *OriginLab Pro*:**
  * Seleção de família tipográfica (*Times New Roman*, *Arial*, *Cambria*, *Garamond*, *Calibri*).
  * Controle individual das 4 bordas da caixa (*Top, Bottom, Left, Right Spines*).
  * Configuração de *Major & Minor Ticks* voltados para dentro (`in`) ou para fora (`out`).
* 📋 **Integração Direta com Microsoft Excel:** Copie e cole blocos de células diretamente do Excel com sanitização automática de casas decimais e separadores brasileiros.
* 💾 **Gerenciador de Projetos (`.vespera` / `.json`):** Salve, carregue e exporte sessões completas de trabalho preservando tanto os dados quanto todas as customizações visuais.
* 📥 **Exportação para Publicação Científica:**
  * **PNG de Alta Resolução (300 / 600 DPI)** para artigos, dissertações e TCCs.
  * **PDF Vetorial** para escalabilidade infinita em documentos LaTeX e Word.
  * **Planilha Excel (`.xlsx`)** com tabelas formatadas e gráficos nativos editáveis gerados via `openpyxl`.
* 🔄 **Auto-Update Integrado via GitHub:** Botão **"Verificar Atualizações"** na própria interface que consulta este repositório, baixa novas versões e atualiza o software automaticamente.

---

## 🏗️ Arquitetura Modular do Projeto

```text
vespera-sci/
├── version.json                    # Metadados de versão para o sistema de Auto-Update
├── requirements.txt                # Dependências do ambiente desktop (PySide6, Matplotlib, etc.)
├── VESPERA_SCI_AGENT_CONTEXT.md    # Blueprint arquitetural e contexto completo para Agentes de IA
├── README.md                       # Documentação oficial do repositório
│
├── config/                         # Camada de Configurações e Presets
│   ├── __init__.py
│   ├── themes.py                   # Paletas científicas, fontes e parâmetros padrão
│   └── presets.py                  # Conjuntos de dados experimentais pré-cadastrados
│
├── core/                           # Motor Científico, Gráfico e de Persistência (Independente de UI)
│   ├── __init__.py
│   ├── sanitizer.py                # Limpeza de dados colados do Excel, formatação PT-BR e estatísticas
│   ├── plot_engine.py              # Renderização Matplotlib (Linhas e Barras) com legenda arrastável
│   ├── excel_exporter.py           # Geração de planilhas .xlsx com gráficos nativos (openpyxl)
│   └── project_manager.py          # Persistência de projetos (.vespera / .json)
│
└── ui/                             # Camada de Interface Gráfica Desktop (PySide6 / Qt)
    └── __init__.py                 # Componentes visuais nativos (Etapa 2)
```

---

## 🗺️ Roadmap de Desenvolvimento

- [x] **Etapa 1:** Estruturação do repositório `vespera-sci`, documentação oficial e desacoplamento completo do motor científico/gráfico (`config/` e `core/`).
- [ ] **Etapa 2:** Construção da Interface Gráfica Desktop em **PySide6** (`main.py` e pacote `ui/`) com tabela estilo Excel, Canvas interativo do Matplotlib e barra de gerenciamento de projetos.
- [ ] **Etapa 3:** Implementação do módulo de **Auto-Update via GitHub** (`core/updater.py` + modal de atualização) e script de empacotamento executável (`.exe`).

---

## 📦 Instalação do Ambiente de Desenvolvimento

```bash
git clone https://github.com/Igorhls/vespera-sci.git
cd vespera-sci
py -m pip install -r requirements.txt
```

---

## 📄 Licença

Distribuído sob a licença **GNU General Public License v3.0 (GPL-3.0)**. Consulte o arquivo [`LICENSE`](LICENSE) para mais detalhes.