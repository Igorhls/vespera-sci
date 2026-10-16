"""
Gerenciamento de persistência de projetos (.vespera / .json) para o Vespera Sci.
Totalmente compatível com os arquivos de projeto gerados na versão web anterior.
"""

from datetime import datetime
import json
import os
import pandas as pd


class ProjectManager:
    """Gerencia o banco local de projetos salvos e a importação/exportação de arquivos."""

    def __init__(self, caminho_banco: str = None):
        if caminho_banco is None:
            raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            caminho_banco = os.path.join(raiz, "projetos_salvos.json")
        self.caminho_banco = caminho_banco

    def ler_banco(self) -> dict:
        """Lê o arquivo JSON local contendo os projetos salvos."""
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
        """Salva o dicionário de projetos no arquivo JSON local."""
        with open(self.caminho_banco, "w", encoding="utf-8") as f:
            json.dump(banco, f, ensure_ascii=False, indent=2)

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
        """Empacota todos os dados e configurações do projeto para serialização JSON."""
        df_clean = df.copy()
        registros = []
        if tipo_grafico == "barras":
            for _, row in df_clean.iterrows():
                registros.append({
                    "Mes": str(row.get("Mes", "")),
                    "Bosque": None if pd.isna(row.get("Bosque")) else float(row.get("Bosque")),
                    "Desvio_Bosque": None if pd.isna(row.get("Desvio_Bosque")) else float(row.get("Desvio_Bosque")),
                    "Estacionamento": None if pd.isna(row.get("Estacionamento")) else float(row.get("Estacionamento")),
                    "Desvio_Estacionamento": (
                        None if pd.isna(row.get("Desvio_Estacionamento")) else float(row.get("Desvio_Estacionamento"))
                    ),
                })
        else:
            for _, row in df_clean.iterrows():
                registros.append({
                    "Pontos": str(row.get("Pontos", "")),
                    "Manha": None if pd.isna(row.get("Manha")) else float(row.get("Manha")),
                    "Tarde": None if pd.isna(row.get("Tarde")) else float(row.get("Tarde")),
                    "Noite": None if pd.isna(row.get("Noite")) else float(row.get("Noite")),
                })

        return {
            "nome_projeto": nome_projeto.strip(),
            "tipo_grafico": tipo_grafico,
            "atualizado_em": datetime.now().strftime("%d/%m/%Y às %H:%M:%S"),
            "titulo_dia": titulo_dia,
            "titulo_grafico": titulo_grafico,
            "min_y": float(min_y),
            "max_y": float(max_y),
            "dados": registros,
            "config": dict(cfg),
        }
