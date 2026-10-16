"""
Sistema de Auto-Update conectado ao GitHub (https://github.com/Igorhls/vespera-sci.git).
Permite verificar se há novos commits ou novas versões no repositório oficial,
baixar o pacote atualizado preservando os projetos salvos do usuário e reiniciar o aplicativo.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
import requests


REPO_OWNER = "Igorhls"
REPO_NAME = "vespera-sci"
BRANCH = "main"

ARQUIVOS_PRESERVADOS = {
    "projetos_salvos.json",
    ".git",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
}


def obter_diretorio_raiz() -> str:
    """Retorna o diretório raiz da instalação do Vespera Sci."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ler_versao_local() -> dict:
    """Lê os metadados locais de version.json e o SHA da última sincronização."""
    raiz = obter_diretorio_raiz()
    caminho_ver = os.path.join(raiz, "version.json")
    dados = {
        "version": "1.0.0",
        "release_date": "",
        "repo": f"{REPO_OWNER}/{REPO_NAME}",
        "branch": BRANCH,
        "notes": "",
        "local_sha": "",
    }
    if os.path.exists(caminho_ver):
        try:
            with open(caminho_ver, "r", encoding="utf-8") as f:
                dados.update(json.load(f))
        except Exception:
            pass

    caminho_sha = os.path.join(raiz, ".last_update_sha")
    if os.path.exists(caminho_sha):
        try:
            with open(caminho_sha, "r", encoding="utf-8") as f:
                dados["local_sha"] = f.read().strip()
        except Exception:
            pass

    if not dados["local_sha"]:
        # Tenta obter do git local caso seja um clone git
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=raiz,
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0:
                dados["local_sha"] = res.stdout.strip()
        except Exception:
            pass

    return dados


def _comparar_versoes(v_remota: str, v_local: str) -> int:
    """Retorna 1 se v_remota > v_local, 0 se iguais, -1 se menor."""
    def parse(v):
        limpo = str(v).lstrip("vV").strip()
        partes = []
        for p in limpo.split("."):
            try:
                partes.append(int(p))
            except ValueError:
                partes.append(0)
        return tuple(partes)

    pr, pl = parse(v_remota), parse(v_local)
    if pr > pl:
        return 1
    if pr < pl:
        return -1
    return 0


def verificar_atualizacao_github(timeout: int = 10) -> dict:
    """
    Consulta o repositório Igorhls/vespera-sci no GitHub para verificar:
    1. O arquivo version.json remoto na branch main.
    2. O último commit na branch main (via GitHub API).
    """
    local_info = ler_versao_local()
    versao_local = local_info.get("version", "1.0.0")
    sha_local = local_info.get("local_sha", "")

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "VesperaSci-Updater/1.0",
    }

    # 1. Busca version.json remoto
    ts = int(time.time())
    url_version = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/version.json?t={ts}"
    remoto_ver_info = {}
    try:
        r_ver = requests.get(url_version, headers=headers, timeout=timeout)
        if r_ver.status_code == 200:
            remoto_ver_info = r_ver.json()
    except Exception as e:
        return {
            "sucesso": False,
            "erro": f"Não foi possível conectar ao GitHub: {e}",
            "versao_local": versao_local,
        }

    # 2. Busca o último commit da branch main
    url_commit = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits/{BRANCH}"
    ultimo_sha = ""
    msg_commit = ""
    data_commit = ""
    try:
        r_com = requests.get(url_commit, headers=headers, timeout=timeout)
        if r_com.status_code == 200:
            c_json = r_com.json()
            ultimo_sha = c_json.get("sha", "")
            commit_obj = c_json.get("commit", {})
            msg_commit = commit_obj.get("message", "").split("\n")[0]
            data_commit = commit_obj.get("committer", {}).get("date", "")[:10]
    except Exception:
        pass

    versao_remota = remoto_ver_info.get("version", versao_local)
    notas_remotas = remoto_ver_info.get("notes", "")
    data_remota = remoto_ver_info.get("release_date", data_commit)

    cmp_ver = _comparar_versoes(versao_remota, versao_local)
    sha_diferente = bool(ultimo_sha and sha_local and ultimo_sha != sha_local)

    tem_atualizacao = (cmp_ver > 0) or sha_diferente

    return {
        "sucesso": True,
        "tem_atualizacao": tem_atualizacao,
        "versao_local": versao_local,
        "versao_remota": versao_remota,
        "sha_local": sha_local[:7] if sha_local else "N/D",
        "sha_remoto": ultimo_sha[:7] if ultimo_sha else "N/D",
        "sha_remoto_full": ultimo_sha,
        "mensagem_commit": msg_commit or notas_remotas or "Atualização disponível no repositório.",
        "notas_versao": notas_remotas,
        "data_remota": data_remota,
    }


def baixar_e_aplicar_atualizacao(sha_remoto_full: str = "", progress_callback=None) -> dict:
    """
    Baixa o pacote .zip mais recente da branch main no GitHub, extrai e atualiza os arquivos
    da aplicação preservando os dados e projetos salvos do usuário.
    """
    raiz = obter_diretorio_raiz()
    pasta_temp = os.path.join(raiz, "updater_temp")

    def report(pct: int, msg: str):
        if progress_callback:
            progress_callback(pct, msg)

    try:
        report(5, "Iniciando conexão com o GitHub...")

        # Se a pasta for um repositório Git com git instalado, tenta git pull primeiro
        git_dir = os.path.join(raiz, ".git")
        if os.path.isdir(git_dir):
            report(20, "Sincronizando via Git (git pull origin main)...")
            try:
                res = subprocess.run(
                    ["git", "pull", "origin", BRANCH],
                    cwd=raiz,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if res.returncode == 0:
                    if sha_remoto_full:
                        with open(os.path.join(raiz, ".last_update_sha"), "w", encoding="utf-8") as f:
                            f.write(sha_remoto_full)
                    report(100, "Atualização concluída com sucesso via Git!")
                    return {"sucesso": True, "metodo": "git_pull", "detalhe": res.stdout.strip()}
            except Exception:
                pass  # Continua para o download via ZIP do GitHub caso git não esteja disponível

        # Download direto do arquivo ZIP da branch main (não exige Git instalado na máquina da usuária)
        url_zip = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"
        report(15, "Baixando pacote atualizado do GitHub...")

        resp = requests.get(url_zip, stream=True, timeout=30)
        resp.raise_for_status()

        total_bytes = int(resp.headers.get("content-length", 0))
        buffer_zip = io.BytesIO()
        baixados = 0

        for chunk in resp.iter_content(chunk_size=16384):
            if chunk:
                buffer_zip.write(chunk)
                baixados += len(chunk)
                if total_bytes > 0:
                    pct = 15 + int((baixados / total_bytes) * 50)
                    report(min(pct, 65), f"Baixando arquivos... ({baixados // 1024} KB)")

        report(70, "Extraindo pacote de atualização...")
        if os.path.exists(pasta_temp):
            shutil.rmtree(pasta_temp, ignore_errors=True)
        os.makedirs(pasta_temp, exist_ok=True)

        buffer_zip.seek(0)
        with zipfile.ZipFile(buffer_zip, "r") as zf:
            zf.extractall(pasta_temp)

        subpastas = [
            os.path.join(pasta_temp, d)
            for d in os.listdir(pasta_temp)
            if os.path.isdir(os.path.join(pasta_temp, d))
        ]
        if not subpastas:
            raise RuntimeError("Estrutura de arquivo ZIP inválida.")

        origem_extraida = subpastas[0]
        report(85, "Atualizando módulos do Vespera Sci (preservando seus projetos salvos)...")

        for item in os.listdir(origem_extraida):
            if item in ARQUIVOS_PRESERVADOS:
                continue
            src_path = os.path.join(origem_extraida, item)
            dst_path = os.path.join(raiz, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dst_path)

        if sha_remoto_full:
            with open(os.path.join(raiz, ".last_update_sha"), "w", encoding="utf-8") as f:
                f.write(sha_remoto_full)

        shutil.rmtree(pasta_temp, ignore_errors=True)
        report(100, "Atualização concluída com sucesso!")
        return {"sucesso": True, "metodo": "zip_download", "detalhe": "Arquivos atualizados via GitHub."}

    except Exception as e:
        if os.path.exists(pasta_temp):
            shutil.rmtree(pasta_temp, ignore_errors=True)
        return {"sucesso": False, "erro": str(e)}
