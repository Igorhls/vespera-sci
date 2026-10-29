# Vespera Sci

**Estúdio Científico de Análise de Dados e Geração de Gráficos Acadêmicos**  
Versão: **1.0.0 (Beta)** | Licença: **GNU GPL v3.0** | Plataformas: **Windows 10/11 (x64)** e **macOS 13+ Ventura (Apple Silicon & Intel)**

---

## 1. Visão Geral

O **Vespera Sci** é uma aplicação desktop desenvolvida para pesquisadores, docentes e estudantes que necessitam processar dados experimentais, efetuar análises estatísticas descritivas e gerar figuras científicas no padrão editorial de periódicos internacionais e normas ABNT (*OriginLab Pro*, *Nature*, *Science*).

O software opera de forma 100% local e offline, garantindo a privacidade dos dados brutos de pesquisa, com suporte nativo a temas visuais claro e escuro.

* **Repositório Oficial:** [github.com/Igorhls/vespera-sci](https://github.com/Igorhls/vespera-sci)
* **Releases e Instaladores:** [github.com/Igorhls/vespera-sci/releases](https://github.com/Igorhls/vespera-sci/releases)

---

## 2. Modalidades Gráficas e Métodos Estatísticos

O Vespera Sci disponibiliza quatro motores de renderização gráfica baseados em Matplotlib, calibrados para rigor visual e precisão paramétrica:

### 2.1 Gráfico de Séries Temporais e Linhas (Pontos P1 a Pn)
* Destinado ao acompanhamento de medições ao longo de pontos de coleta ou estações experimentais.
* Suporte a séries sobrepostas (ex.: Manhã, Tarde e Noite).
* Controle milimétrico de marcadores geométricos (círculos, quadrados, triângulos, losangos) e espessura de traçado.
* Opções de estilos contínuos, tracejados, pontilhados ou traço-ponto.

### 2.2 Gráfico de Barras Agrupadas com Desvio Padrão
* Desvio padrão desenhado como barra de erro (± DP) sobre a média, no padrão dos periódicos; o layout legado com o desvio como barra separada continua disponível em *Opções de Barras*.
* Comparação de médias e dispersões amostrais entre diferentes períodos ou variáveis.
* Exibição de valores numéricos no topo das barras com formatação regional brasileira (vírgula decimal).
* Padrões de hachuras científicas (linhas diagonais, xadrez, pontilhados) para diferenciação gráfica em publicações monocromáticas (preto e branco).
* Ajuste de espaçamento entre grupos e subgrupos de barras.

### 2.3 Gráfico de Dispersão e Regressão Linear Simples
* Análise bivariada entre pares de variáveis quantitativas (X vs. Y).
* Traçado da reta de ajuste pelo método dos mínimos quadrados ordinários (MQO).
* Cálculo em tempo real dos seguintes parâmetros científicos:
  * Coeficiente de determinação ($R^2$) e percentual de variância explicada.
  * Coeficiente de correlação linear de Pearson ($r$) com classificação de força e sentido.
  * Erro padrão da estimativa ($S_e$).
  * Equação analítica da reta ($y = ax + b$).
  * Banda opcional do intervalo de confiança de 95% da reta ajustada, calculada com a distribuição *t* de Student (n − 2 graus de liberdade): $\hat{y} \pm t \cdot S_e \sqrt{1/n + (x-\bar{x})^2/S_{xx}}$.

### 2.4 Boxplot e Distribuição Amostral (Diagrama de Caixas)
* Avaliação comparativa da dispersão e assimetria térmica/ambiental.
* Cálculo automático dos parâmetros descritivos:
  * Mediana ($Q_2$) e Quartis ($Q_1$ a 25% e $Q_3$ a 75%).
  * Amplitude interquartílica ($\text{IQR} = Q_3 - Q_1$).
  * Limites dos *whiskers* baseados na regra clássica de Tukey ($1{,}5 \times \text{IQR}$).
  * Identificação de dados discrepantes (*outliers*) destacados visualmente.
  * Marcador de média amostral em losango vazado.
  * Opção de sobreposição de pontos experimentais reais via *jitter* aleatório controlado.

---

## 3. Recursos de Interface e Produtividade

* **Início Limpo e Modular:** A aplicação inicializa em branco por padrão, permitindo montar experimentos do zero com facilidade (`Ctrl+N`), preservando sessões e projetos anteriores.
* **Galeria de Modelos Prontos (Templates):** Acesso rápido a modelos pré-configurados e dados experimentais de referência para séries temporais, barras com desvio, dispersão com regressão e diagramas de boxplot.
* **Séries e Colunas Dinâmicas:** Adicione (`+ Série`) ou remova (`- Série`) colunas livremente no modo de séries temporais. Dê duplo clique no cabeçalho de qualquer coluna para renomeá-la de forma imediata.
* **Gerenciamento de Arquivos de Projeto (`.json`, compatível com `.vespera`):** Salve e reabra projetos completos em arquivos independentes com atalhos padrão (`Ctrl+O`, `Ctrl+S`, `Ctrl+Shift+S`) e histórico persistente de projetos recentes.
* **Colagem Direta no Grid (`Ctrl+V`):** Permite copiar blocos de dados de planilhas eletrônicas (Excel, Google Sheets, LibreOffice Calc) e colá-los diretamente sobre a tabela. As linhas são expandidas dinamicamente conforme necessário. Se o bloco colado parecer ter perdido a vírgula decimal (ex.: `274` em vez de `27,4`), o Vespera Sci pergunta antes de corrigir. Os valores nunca são alterados sem confirmação.
* **Histórico de Edição (`Ctrl+Z` e `Ctrl+Y`):** Mecanismo de desfazer e refazer integrado à matriz de dados, retendo até 60 etapas de alterações.
* **Sinalização Visual de Células Vazias / NaN:** Destaque em tom âmbar nas células com valores numéricos faltantes, prevenindo inconsistências em relatórios analíticos.
* **Legenda Arrastável com o Mouse:** A legenda do gráfico pode ser reposicionada livremente no canvas através de arrasto direto.
* **Controles de Eixos Estilo OriginLab:**
  * Configuração individual das 4 bordas do quadro (*Top, Bottom, Left, Right Spines*).
  * Ticks principais e secundários direcionáveis para fora (`out`) ou para dentro (`in`).
  * Controle de passo de escala nos eixos X e Y.
* **Resumo Estatístico Descritivo:** Painel dinâmico que sintetiza médias, desvios padrão, amplitudes e quartis à medida que os dados são alterados.
* **Calculadora Rápida Integrada:** Utilitário para cálculo instantâneo de média e desvio padrão amostral a partir de valores numéricos brutos.

---

## 4. Padrões de Exportação Científica

* **Vetor SVG (`.svg`):** Gráficos vetoriais de resolução infinita, ideais para editoração gráfica e diagramação web.
* **Vetor PDF (`.pdf`):** Documento vetorial para inclusão direta em artigos científicos diagramados em LaTeX ou Microsoft Word.
* **Imagem Rasterizada (`.png` a 300 DPI):** Figura de alta densidade de pixels pronta para impressão editorial, relatórios técnicos e dissertações.
* **Imagem TIFF (`.tif` a 600 DPI, compressão LZW):** Formato exigido por diversos periódicos para submissão de figuras.
* **Planilhas Microsoft Excel (`.xlsx`):** Arquivos gerados via OpenPyXL contendo as tabelas estruturadas e formatadas com metadados experimentais.
* **Arquivos de Projeto (`.json` / `.vespera`):** Salva o estado completo da sessão de trabalho, incluindo dados tabulares, nomes de séries e preferências de formatação estética.

### Onde ficam os dados do usuário
O histórico de projetos (`projetos_salvos.json`) e o log de diagnóstico (`vespera.log`) ficam numa pasta do usuário, fora da instalação, e não são afetados por atualizações:
* **Windows:** `%APPDATA%\VesperaSci`
* **macOS:** `~/Library/Application Support/VesperaSci`
* **Linux:** `~/.local/share/VesperaSci`

---

## 5. Instalação e Execução

### 5.1 No Windows (Binário Standalone)
1. Acesse a aba de [Releases](https://github.com/Igorhls/vespera-sci/releases) do repositório.
2. Baixe o pacote compactado `VesperaSci-Windows-x64.zip`.
3. Extraia o arquivo para uma pasta local e execute `VesperaSci.exe`.

### 5.2 No macOS (Ventura 13 ou Superior — Apple Silicon & Intel)
1. Acesse a aba de [Releases](https://github.com/Igorhls/vespera-sci/releases) e baixe a imagem correspondente à sua arquitetura:
   * **MacBooks Apple Silicon (M1/M2/M3/M4):** `VesperaSci-macOS-AppleSilicon-arm64.dmg`
   * **MacBooks Intel (x86_64):** `VesperaSci-macOS-Intel-x86_64.dmg`
2. Dê dois cliques no arquivo `.dmg` e arraste o aplicativo **Vespera Sci** para a pasta **Applications**.
3. Na primeira execução:
   * Clique com o **botão direito** sobre o aplicativo e selecione **Abrir**, confirmando a execução; ou
   * Acesse **Ajustes do Sistema > Privacidade e Segurança** e clique em **Abrir Mesmo Assim**.

### 5.3 Execução via Código-Fonte (Python 3.10+)
Caso prefira executar diretamente pelo interpretador Python:

```bash
# 1. Clonar o repositório
git clone https://github.com/Igorhls/vespera-sci.git
cd vespera-sci

# 2. Instalar dependências
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Iniciar a aplicação
python main.py
```

---

## 6. Arquitetura do Software

O código segue separação estrita de responsabilidades em camadas desacopladas:

```text
vespera-sci/
├── main.py                     # Ponto de entrada e inicialização da aplicação Qt
├── version.json                # Metadados de versão e controle de atualizações
├── requirements.txt            # Dependências de execução (PySide6, Matplotlib, Pandas, etc.)
├── requirements-dev.txt        # Ferramentas de desenvolvimento (PyInstaller, pytest, ruff)
├── pyproject.toml              # Configuração do lint (ruff)
│
├── config/                     # Configurações e presets experimentais
│   ├── presets.py              # Conjuntos de dados acadêmicos pré-configurados
│   └── themes.py               # Paletas de cores, tipografias e definições padrão
│
├── core/                       # Motor científico e analítico (independente de interface)
│   ├── excel_exporter.py       # Gerador de planilhas .xlsx com formatação nativa
│   ├── paths.py                # Pastas de instalação, recursos e dados do usuário; logging
│   ├── plot_engine.py          # Renderização científica Matplotlib (Linhas, Barras, Dispersão, Boxplot)
│   ├── project_manager.py      # Persistência de sessões e projetos em formato JSON
│   ├── sanitizer.py            # Sanitização de entradas, conversão numérica e cálculos estatísticos
│   └── updater.py              # Atualizações via GitHub (Releases com SHA-256 ou branch main)
│
├── ui/                         # Camada de Interface Gráfica (PySide6 / Qt)
│   ├── data_table_widget.py    # Editor tabular com suporte a Ctrl+V, Undo/Redo e destaque NaN
│   ├── icons.py                # Gerenciador de ícones vetoriais SVG
│   ├── main_window.py          # Janela principal, barra de menus e gerenciamento de abas
│   ├── plot_canvas_widget.py   # Visualizador do gráfico com toolbar e botões de exportação
│   ├── sidebar_controls.py     # Painel de customização estética de eixos, traços e cores
│   ├── styles.py               # Folhas de estilo QSS para temas Claro e Escuro
│   └── templates_dialog.py     # Diálogo da Galeria de Modelos e Presets Acadêmicos
│
├── tests/                      # Suíte de testes automatizados
│   └── test_all.py             # Testes unitários de sanitização, estatísticas, plotagem e exportação
│
└── .github/workflows/          # Automação de CI/CD (GitHub Actions)
    └── build.yml               # Compilação multiplataforma para Windows e macOS
```

---

## 7. Testes Automatizados

A aplicação inclui uma suíte de testes unitários que valida a integridade dos cálculos matemáticos, da renderização gráfica e da exportação de dados:

```bash
pip install -r requirements-dev.txt
ruff check .
python -m pytest tests
```

---

## 8. Licença

Este projeto é distribuído sob a licença **GNU General Public License v3.0 (GPL-3.0)**. Consulte o arquivo [`LICENSE`](LICENSE) para mais informações.
