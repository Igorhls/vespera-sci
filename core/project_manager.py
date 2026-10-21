"""
Gerenciamento de persistência de projetos (.vespera / .json) para o Vespera Sci.
Suporta persistência local em arquivo único (.vespera) e banco histórico (projetos_salvos.json).
Totalmente retrocompatível com projetos antigos e datasets prévios.
"""

from datetime import datetime
import json
import os
import pandas as pd


class ProjectManager:
    """Gerencia arquivos de projetos individuais (.vespera / .json) e o banco local."""

    def __init__(self, caminho_banco: str = None):
        if caminho_banco is None:
            raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            caminho_banco = os.path.join(raiz, "projetos_salvos.json")
        self.caminho_banco = caminho_banco

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
        except Exception:
            return {"ultimo_projeto_ativo": None, "projetos": {}}

    def gravar_banco(self, banco: dict):
        """Salva o dicionário de projetos no banco local."""
        try:
            with open(self.caminho_banco, "w", encoding="utf-8") as f:
                json.dump(banco, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao gravar banco local: {e}")

    @staticmethod
    def salvar_arquivo_projeto(caminho: str, payload: dict) -> bool:
        """Salva o projeto em um arquivo individual (.vespera ou .json) no disco."""
        try:
            pasta = os.path.dirname(os.path.abspath(caminho))
            if pasta and not os.path.exists(pasta):
                os.makedirs(pasta, exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar arquivo de projeto em {caminho}: {e}")
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
        except Exception as e:
            print(f"Erro ao ler arquivo de projeto {caminho}: {e}")
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
