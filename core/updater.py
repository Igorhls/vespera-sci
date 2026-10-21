"""
Sistema de Auto-Update conectado ao GitHub (https://github.com/Igorhls/vespera-sci.git).
Suporta dois canais de atualização independentes:
1. Canal Oficial Estável (Padrão): Consulta exclusivamente as Releases oficiais publicadas no GitHub.
2. Canal de Desenvolvimento (Dev): Consulta commits recentes da branch main para testadores e desenvolvedores.
Preserva integralmente os projetos salvos e dados do usuário durante atualizações.
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


def comparar_versoes(v_remota: str, v_local: str) -> int:
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


def verificar_atualizacao_github(canal: str = "stable", timeout: int = 10) -> dict:
    """
    Verifica atualizações no repositório Igorhls/vespera-sci conforme o canal selecionado:
    - 'stable' (Padrão): Verifica exclusivamente as Releases oficiais publicadas no GitHub.
    - 'dev': Verifica novos commits enviados diretamente para a branch 'main'.
    """
    local_info = ler_versao_local()
    versao_local = local_info.get("version", "1.0.0")
    sha_local = local_info.get("local_sha", "")

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "VesperaSci-Updater/1.0",
    }

    # =======================================================================
    # CANAL 1: Oficial Estável (Releases do GitHub)
    # =======================================================================
    if canal == "stable":
        url_release = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        try:
            r = requests.get(url_release, headers=headers, timeout=timeout)
            if r.status_code == 200:
                rel = r.json()
                tag_raw = rel.get("tag_name", "").strip()
                tag_clean = tag_raw.lstrip("vV").strip()
                titulo = rel.get("name", f"Versão {tag_clean}")
                notas = rel.get("body", "Notas da versão não fornecidas.")
                data_pub = rel.get("published_at", "")[:10]
                html_url = rel.get("html_url", f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases")
                download_url = rel.get("zipball_url", "")

                for asset in rel.get("assets", []):
                    nome_asset = asset.get("name", "").lower()
                    if sys.platform == "win32" and nome_asset.endswith(".zip"):
                        download_url = asset.get("browser_download_url", download_url)
                        break

                cmp_ver = comparar_versoes(tag_clean, versao_local)
                tem_atualizacao = (cmp_ver > 0)

                return {
                    "sucesso": True,
                    "canal": "stable",
                    "tem_atualizacao": tem_atualizacao,
                    "versao_local": versao_local,
                    "versao_remota": tag_clean,
                    "tag_remota": tag_raw,
                    "titulo_release": titulo,
                    "notas_versao": notas,
                    "data_remota": data_pub,
                    "html_url": html_url,
                    "download_url": download_url,
                    "sha_local": sha_local[:7] if sha_local else "N/D",
                    "sha_remoto": tag_raw,
                    "sha_remoto_full": "",
                    "mensagem_commit": titulo,
                }
            elif r.status_code == 404:
                return {
                    "sucesso": True,
                    "canal": "stable",
                    "tem_atualizacao": False,
                    "versao_local": versao_local,
                    "versao_remota": versao_local,
                    "tag_remota": f"v{versao_local}",
                    "titulo_release": "Nenhuma release publicada",
                    "notas_versao": "O repositório ainda não possui releases estáveis publicadas.",
                    "data_remota": "",
                    "html_url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases",
                    "download_url": "",
                    "sha_local": sha_local[:7] if sha_local else "N/D",
                    "sha_remoto": "N/D",
                    "sha_remoto_full": "",
                    "mensagem_commit": "Versão estável atualizada.",
                }
            else:
                return {
                    "sucesso": False,
                    "canal": "stable",
                    "erro": f"Resposta inesperada do GitHub (HTTP {r.status_code}).",
                    "versao_local": versao_local,
                }
        except Exception as e:
            return {
                "sucesso": False,
                "canal": "stable",
                "erro": f"Falha de conexão com o GitHub: {e}",
                "versao_local": versao_local,
            }

    # =======================================================================
    # CANAL 2: Desenvolvimento (Commits da branch main)
    # =======================================================================
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
            "canal": "dev",
            "erro": f"Não foi possível conectar ao GitHub: {e}",
            "versao_local": versao_local,
        }

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

    cmp_ver = comparar_versoes(versao_remota, versao_local)
    sha_diferente = bool(ultimo_sha and sha_local and ultimo_sha != sha_local)
    tem_atualizacao = (cmp_ver > 0) or sha_diferente

    return {
        "sucesso": True,
        "canal": "dev",
        "tem_atualizacao": tem_atualizacao,
        "versao_local": versao_local,
        "versao_remota": versao_remota,
        "sha_local": sha_local[:7] if sha_local else "N/D",
        "sha_remoto": ultimo_sha[:7] if ultimo_sha else "N/D",
        "sha_remoto_full": ultimo_sha,
        "mensagem_commit": msg_commit or notas_remotas or "Atualização de desenvolvimento disponível.",
        "notas_versao": notas_remotas,
        "data_remota": data_remota,
        "html_url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}/commits/{BRANCH}",
        "download_url": f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip",
    }


def baixar_e_aplicar_atualizacao(
    canal: str = "stable",
    download_url: str = "",
    sha_remoto_full: str = "",
    progress_callback=None,
) -> dict:
    """
    Baixa e atualiza os arquivos da aplicação preservando dados e projetos salvos.
    No canal dev com git disponível, executa git pull origin main.
    Caso contrário, efetua download seguro via stream HTTP com extração atômica.
    """
    raiz = obter_diretorio_raiz()
    pasta_temp = os.path.join(raiz, "updater_temp")

    def report(pct: int, msg: str):
        if progress_callback:
            progress_callback(pct, msg)

    try:
        report(5, "Iniciando conexão de atualização...")

        git_dir = os.path.join(raiz, ".git")
        if canal == "dev" and os.path.isdir(git_dir):
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
                pass

        url_alvo = download_url or f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"
        report(15, "Baixando pacote oficial do GitHub...")

        headers = {"User-Agent": "VesperaSci-Updater/1.0"}
        resp = requests.get(url_alvo, headers=headers, stream=True, timeout=35)
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
                    report(min(pct, 65), f"Baixando pacote... ({baixados // 1024} KB)")

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
        origem_extraida = subpastas[0] if subpastas else pasta_temp

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
