"""
Gerenciamento de persistência de projetos (.vespera / .json) para o Vespera Sci.
Suporta persistência local em arquivo único (.vespera) e banco histórico (projetos_salvos.json).
O banco fica na pasta de dados do usuário (gravável mesmo com o app em Program Files ou num .app);
um banco antigo na pasta de instalação é migrado automaticamente na primeira execução.
Totalmente retrocompatível com projetos antigos e datasets prévios.
"""

from datetime import datetime
import json
import logging
import os
import shutil
import pandas as pd

from core.paths import diretorio_codigo_fonte, diretorio_dados_usuario, gravar_json_atomico

logger = logging.getLogger(__name__)


class ProjectManager:
    """Gerencia arquivos de projetos individuais (.vespera / .json) e o banco local."""

    def __init__(self, caminho_banco: str = None):
        if caminho_banco is None:
            caminho_banco = os.path.join(diretorio_dados_usuario(), "projetos_salvos.json")
            self._migrar_banco_legado(caminho_banco)
        self.caminho_banco = caminho_banco

    @staticmethod
    def _migrar_banco_legado(caminho_novo: str):
        """Copia o projetos_salvos.json das versões antigas (pasta de instalação) para a pasta do usuário."""
        legado = os.path.join(diretorio_codigo_fonte(), "projetos_salvos.json")
        if os.path.exists(caminho_novo) or not os.path.exists(legado):
            return
        try:
            shutil.copy2(legado, caminho_novo)
            logger.info("Banco de projetos migrado de %s para %s", legado, caminho_novo)
        except OSError:
            logger.exception("Falha ao migrar o banco de projetos legado")

    def ler_banco(self) -> dict:
        """Lê o arquivo JSON local contendo os projetos salvos na máquina."""
        if not os.path.exists(self.caminho_banco):
            return {"ultimo_projeto_ativo": None, "projetos": {}}
        try:
            with open(self.caminho_banco, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if not isinstance(dados, dict) or "projetos" not in dados:
                    return {"ultimo_projeto_ativo": None, "projetos": {}}
                return dados
        except (OSError, ValueError):
            logger.exception("Banco de projetos ilegível: %s", self.caminho_banco)
            return {"ultimo_projeto_ativo": None, "projetos": {}}

    def gravar_banco(self, banco: dict):
        """Salva o dicionário de projetos no banco local."""
        try:
            gravar_json_atomico(self.caminho_banco, banco)
        except (OSError, TypeError, ValueError):
            logger.exception("Erro ao gravar banco local: %s", self.caminho_banco)

    @staticmethod
    def salvar_arquivo_projeto(caminho: str, payload: dict) -> bool:
        """Salva o projeto em um arquivo individual (.vespera ou .json) no disco."""
        try:
            gravar_json_atomico(caminho, payload)
            return True
        except (OSError, TypeError, ValueError):
            logger.exception("Erro ao salvar arquivo de projeto em %s", caminho)
            return False

    @staticmethod
    def carregar_arquivo_projeto(caminho: str) -> dict:
        """Carrega e valida um arquivo de projeto (.vespera ou .json) do disco."""
        if not os.path.exists(caminho):
            return {}
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, dict) and "dados" in dados:
                return dados
            return {}
        except (OSError, ValueError):
            logger.exception("Erro ao ler arquivo de projeto %s", caminho)
            return {}

    @staticmethod
    def construir_payload(
        nome_projeto: str,
        tipo_grafico: str,
        df: pd.DataFrame,
        titulo_dia: str,
        titulo_grafico: str,
        min_y: float,
        max_y: float,
        cfg: dict,
    ) -> dict:
        """Empacota dados (qualquer quantidade de colunas/séries) e configurações do projeto."""
        df_clean = df.copy()
        registros = []
        colunas = list(df_clean.columns)

        for _, row in df_clean.iterrows():
            item = {}
            for idx_c, col in enumerate(colunas):
                val = row.get(col)
                if pd.isna(val) or val == "":
                    item[col] = None
                else:
                    if idx_c == 0:
                        item[col] = str(val)
                    else:
                        try:
                            item[col] = float(val)
                        except (ValueError, TypeError):
                            item[col] = str(val)
            registros.append(item)

        return {
            "formato": "vespera_project",
            "versao_formato": "1.0.0",
            "software": "Vespera Sci",
            "nome_projeto": nome_projeto.strip() if nome_projeto else "Novo Projeto",
            "tipo_grafico": tipo_grafico,
            "atualizado_em": datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
            "titulo_dia": titulo_dia,
            "titulo_grafico": titulo_grafico,
            "min_y": float(min_y) if min_y is not None else 0.0,
            "max_y": float(max_y) if max_y is not None else 35.0,
            "colunas": colunas,
            "dados": registros,
            "config": dict(cfg),
        }
