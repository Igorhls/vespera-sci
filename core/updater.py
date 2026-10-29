"""
Sistema de Auto-Update conectado ao GitHub (https://github.com/Igorhls/vespera-sci.git).
Suporta dois canais de atualização independentes:
1. Canal Oficial Estável (Padrão): Consulta exclusivamente as Releases oficiais publicadas no GitHub.
2. Canal de Desenvolvimento (Dev): Consulta commits recentes da branch main (somente instalação via código-fonte).

Estratégias de aplicação, conforme o tipo de instalação:
- Código-fonte com Git (canal dev): git pull --ff-only.
- Código-fonte sem Git: baixa o pacote, substitui os módulos, remove módulos .py que deixaram de existir
  e reinstala as dependências se o requirements.txt mudou.
- Executável Windows: extrai a nova versão numa pasta temporária e gera um script que substitui a
  instalação depois que o Vespera Sci fecha (arquivos em uso não podem ser sobrescritos).
- macOS (.app) ou pasta de instalação sem permissão de escrita: baixa o instalador para Downloads.

Os projetos salvos ficam na pasta de dados do usuário e nunca são tocados por uma atualização.
"""

import hashlib
import io
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

import requests

from core.paths import diretorio_codigo_fonte, diretorio_instalacao, diretorio_recursos, executando_empacotado

logger = logging.getLogger(__name__)

REPO_OWNER = "Igorhls"
REPO_NAME = "vespera-sci"
BRANCH = "main"

ARQUIVOS_PRESERVADOS = {
    "projetos_salvos.json",
    ".last_update_sha",
    ".git",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    "scratch",
    "updater_temp",
}

# Pastas de código cujo conteúdo é inteiramente gerenciado pelo pacote de atualização
PASTAS_GERENCIADAS = ("core", "ui", "config", "tests")

ACAO_REINICIAR = "reiniciar"
ACAO_APLICAR_AO_FECHAR = "aplicar_ao_fechar"
ACAO_ABRIR_INSTALADOR = "abrir_instalador"


def obter_diretorio_raiz() -> str:
    """Retorna o diretório raiz da instalação do Vespera Sci."""
    return diretorio_instalacao()


def ler_versao_local() -> dict:
    """Lê os metadados locais de version.json e o SHA da última sincronização."""
    dados = {
        "version": "0.0.0",
        "release_date": "",
        "repo": f"{REPO_OWNER}/{REPO_NAME}",
        "branch": BRANCH,
        "notes": "",
        "local_sha": "",
    }
    caminho_ver = os.path.join(diretorio_recursos(), "version.json")
    if os.path.exists(caminho_ver):
        try:
            with open(caminho_ver, "r", encoding="utf-8") as f:
                dados.update(json.load(f))
        except (OSError, ValueError):
            logger.exception("version.json ilegível em %s", caminho_ver)
    else:
        logger.warning("version.json não encontrado em %s", caminho_ver)

    if executando_empacotado():
        return dados

    raiz = diretorio_codigo_fonte()
    caminho_sha = os.path.join(raiz, ".last_update_sha")
    if os.path.exists(caminho_sha):
        try:
            with open(caminho_sha, "r", encoding="utf-8") as f:
                dados["local_sha"] = f.read().strip()
        except OSError:
            logger.exception("Falha ao ler %s", caminho_sha)

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
        except (OSError, subprocess.SubprocessError):
            logger.debug("git indisponível para obter o SHA local")

    return dados


def comparar_versoes(v_remota: str, v_local: str) -> int:
    """
    Retorna 1 se v_remota > v_local, 0 se iguais, -1 se menor.
    Segue a precedência do SemVer para pré-lançamentos do canal Dev:
    1.0.0 < 1.1.0-dev.1 < 1.1.0-dev.2 < 1.1.0.
    """
    def parse(v):
        limpo = str(v).lstrip("vV").strip()
        nucleo, _, pre = limpo.partition("-")
        numeros = []
        for p in nucleo.split("."):
            try:
                numeros.append(int(p))
            except ValueError:
                numeros.append(0)
        while len(numeros) < 3:
            numeros.append(0)
        # Versão final vem depois de qualquer pré-lançamento com o mesmo núcleo
        if not pre:
            return (tuple(numeros), 1, ())
        identificadores = tuple(
            (0, int(i), "") if i.isdigit() else (1, 0, i) for i in pre.split(".")
        )
        return (tuple(numeros), 0, identificadores)

    pr, pl = parse(v_remota), parse(v_local)
    if pr > pl:
        return 1
    if pr < pl:
        return -1
    return 0


def _arquitetura_mac() -> str:
    return "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x86_64"


def selecionar_asset_release(assets: list, plataforma: str = None, arquitetura: str = None):
    """Escolhe o pacote binário da release adequado à plataforma (ou None)."""
    plataforma = plataforma or sys.platform
    for asset in assets:
        nome = asset.get("name", "").lower()
        if plataforma == "win32" and nome.endswith(".zip") and "windows" in nome:
            return asset
        if plataforma == "darwin" and nome.endswith(".dmg"):
            arq = arquitetura or _arquitetura_mac()
            marcadores = ("arm64", "applesilicon") if arq == "arm64" else ("x86_64", "intel")
            if any(m in nome for m in marcadores):
                return asset
    return None


def _resultado_erro(canal: str, versao_local: str, mensagem: str) -> dict:
    return {"sucesso": False, "canal": canal, "erro": mensagem, "versao_local": versao_local}


def verificar_atualizacao_github(canal: str = "stable", timeout: int = 10) -> dict:
    """
    Verifica atualizações no repositório Igorhls/vespera-sci conforme o canal selecionado:
    - 'stable' (Padrão): Verifica exclusivamente as Releases oficiais publicadas no GitHub.
    - 'dev': Verifica novos commits enviados diretamente para a branch 'main'.
    """
    local_info = ler_versao_local()
    versao_local = local_info.get("version", "0.0.0")
    sha_local = local_info.get("local_sha", "")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "VesperaSci-Updater/1.1",
    }

    # =======================================================================
    # CANAL 1: Oficial Estável (Releases do GitHub)
    # =======================================================================
    if canal == "stable":
        url_release = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        try:
            r = requests.get(url_release, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            return _resultado_erro("stable", versao_local, f"Falha de conexão com o GitHub: {e}")

        if r.status_code == 404:
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
                "sha256_esperado": "",
                "sha_local": sha_local[:7] if sha_local else "N/D",
                "sha_remoto": "N/D",
                "sha_remoto_full": "",
                "mensagem_commit": "Versão estável atualizada.",
            }
        if r.status_code != 200:
            return _resultado_erro("stable", versao_local, f"Resposta inesperada do GitHub (HTTP {r.status_code}).")

        rel = r.json()
        tag_raw = (rel.get("tag_name") or "").strip()
        tag_clean = tag_raw.lstrip("vV").strip()
        titulo = rel.get("name") or f"Versão {tag_clean}"

        download_url = ""
        sha256_esperado = ""
        if executando_empacotado():
            asset = selecionar_asset_release(rel.get("assets", []))
            if asset:
                download_url = asset.get("browser_download_url", "")
                digest = asset.get("digest") or ""
                if digest.startswith("sha256:"):
                    sha256_esperado = digest.split(":", 1)[1].lower()
        else:
            download_url = rel.get("zipball_url", "")

        return {
            "sucesso": True,
            "canal": "stable",
            "tem_atualizacao": comparar_versoes(tag_clean, versao_local) > 0,
            "versao_local": versao_local,
            "versao_remota": tag_clean,
            "tag_remota": tag_raw,
            "titulo_release": titulo,
            "notas_versao": rel.get("body") or "Notas da versão não fornecidas.",
            "data_remota": (rel.get("published_at") or "")[:10],
            "html_url": rel.get("html_url", f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases"),
            "download_url": download_url,
            "sha256_esperado": sha256_esperado,
            "sha_local": sha_local[:7] if sha_local else "N/D",
            "sha_remoto": tag_raw,
            "sha_remoto_full": "",
            "mensagem_commit": titulo,
        }

    # =======================================================================
    # CANAL 2: Desenvolvimento (Commits da branch main)
    # =======================================================================
    if executando_empacotado():
        return _resultado_erro(
            "dev",
            versao_local,
            "O Canal de Desenvolvimento só está disponível na instalação a partir do código-fonte. "
            "Use o Canal Oficial Estável no aplicativo instalado.",
        )

    ts = int(time.time())
    url_version = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/version.json?t={ts}"
    remoto_ver_info = {}
    try:
        r_ver = requests.get(url_version, headers=headers, timeout=timeout)
        if r_ver.status_code == 200:
            remoto_ver_info = r_ver.json()
    except requests.RequestException as e:
        return _resultado_erro("dev", versao_local, f"Não foi possível conectar ao GitHub: {e}")
    except ValueError:
        logger.warning("version.json remoto inválido")

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
    except (requests.RequestException, ValueError):
        logger.warning("Não foi possível consultar o último commit da branch %s", BRANCH, exc_info=True)

    versao_remota = remoto_ver_info.get("version", versao_local)
    notas_remotas = remoto_ver_info.get("notes", "")
    data_remota = remoto_ver_info.get("release_date", data_commit)

    cmp_ver = comparar_versoes(versao_remota, versao_local)
    # Sem SHA local (ex.: instalação pelo Instalar_Online.bat) não há como provar que está em dia:
    # oferecer a sincronização grava o .last_update_sha e resolve nas próximas verificações.
    sha_diferente = bool(ultimo_sha and ultimo_sha != sha_local)
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
        "sha256_esperado": "",
    }


# =======================================================================
# Aplicação da atualização
# =======================================================================

def _baixar(url: str, destino, report, pct_ini: int = 15, pct_fim: int = 65, sha256_esperado: str = ""):
    """Baixa url para o objeto arquivo destino (stream), validando o SHA-256 quando informado."""
    resp = requests.get(url, headers={"User-Agent": "VesperaSci-Updater/1.1"}, stream=True, timeout=35)
    resp.raise_for_status()
    total_bytes = int(resp.headers.get("content-length", 0))
    baixados = 0
    hasher = hashlib.sha256()
    for chunk in resp.iter_content(chunk_size=65536):
        if not chunk:
            continue
        destino.write(chunk)
        hasher.update(chunk)
        baixados += len(chunk)
        if total_bytes > 0:
            pct = pct_ini + int((baixados / total_bytes) * (pct_fim - pct_ini))
            report(min(pct, pct_fim), f"Baixando pacote... ({baixados // 1024} KB)")
    if sha256_esperado and hasher.hexdigest().lower() != sha256_esperado.lower():
        raise ValueError(
            "O pacote baixado não confere com o SHA-256 publicado na release "
            "(download corrompido ou adulterado). A atualização foi cancelada."
        )


def _pasta_gravavel(pasta: str) -> bool:
    try:
        with tempfile.NamedTemporaryFile(dir=pasta, prefix=".vespera_teste_", delete=True):
            pass
        return True
    except OSError:
        return False


def _pasta_downloads() -> str:
    pasta = os.path.join(os.path.expanduser("~"), "Downloads")
    return pasta if os.path.isdir(pasta) else tempfile.gettempdir()


def _localizar_raiz_pacote(pasta: str, arquivo_marcador: str) -> str:
    """Procura, dentro do pacote extraído, a pasta que contém o arquivo marcador."""
    for atual, _dirs, arquivos in os.walk(pasta):
        if arquivo_marcador in arquivos:
            return atual
    raise ValueError(f"Pacote de atualização inválido: '{arquivo_marcador}' não encontrado.")


def _ler_arquivo(caminho: str) -> str:
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _aplicar_pacote_codigo_fonte(origem: str, raiz: str) -> list:
    """Copia o pacote de código-fonte por cima da instalação e remove módulos obsoletos."""
    removidos = []
    for pasta in PASTAS_GERENCIADAS:
        pasta_dst = os.path.join(raiz, pasta)
        pasta_src = os.path.join(origem, pasta)
        if not (os.path.isdir(pasta_dst) and os.path.isdir(pasta_src)):
            continue
        for atual, _dirs, arquivos in os.walk(pasta_dst):
            if "__pycache__" in atual:
                continue
            for nome in arquivos:
                if not nome.endswith(".py"):
                    continue
                caminho_dst = os.path.join(atual, nome)
                relativo = os.path.relpath(caminho_dst, raiz)
                if not os.path.exists(os.path.join(origem, relativo)):
                    os.remove(caminho_dst)
                    removidos.append(relativo)

    for item in os.listdir(origem):
        if item in ARQUIVOS_PRESERVADOS:
            continue
        src_path = os.path.join(origem, item)
        dst_path = os.path.join(raiz, item)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dst_path)
    return removidos


def _instalar_dependencias(raiz: str) -> str:
    res = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", os.path.join(raiz, "requirements.txt")],
        cwd=raiz,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if res.returncode != 0:
        logger.error("pip install falhou: %s", res.stderr)
        return (
            "Atenção: não foi possível instalar as novas dependências automaticamente. "
            "Execute 'Instalar_Vespera_Sci.bat' (ou pip install -r requirements.txt)."
        )
    return "Dependências atualizadas."


def _gerar_script_windows(origem: str, destino: str, pasta_temp: str) -> str:
    """Script que aguarda o Vespera Sci fechar, espelha a nova versão na instalação e reabre o app."""
    pid = os.getpid()
    exe = os.path.join(destino, "VesperaSci.exe")
    script = os.path.join(tempfile.gettempdir(), f"vespera_update_{pid}.bat")
    conteudo = f"""@echo off
chcp 65001 >NUL
setlocal
title Atualizando Vespera Sci
echo Aguardando o Vespera Sci fechar...
:aguardar
tasklist /FI "PID eq {pid}" 2>NUL | find "{pid}" >NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak >NUL
    goto aguardar
)
echo Instalando a nova versao...
robocopy "{origem}" "{destino}" /MIR /R:5 /W:1 /NFL /NDL /NJH /NJS >NUL
if errorlevel 8 (
    echo [ERRO] Falha ao copiar os arquivos da atualizacao. A versao anterior pode estar incompleta.
    echo Baixe a versao mais recente em https://github.com/{REPO_OWNER}/{REPO_NAME}/releases
    pause
    exit /b 1
)
rmdir /s /q "{pasta_temp}" >NUL 2>&1
start "" "{exe}"
(goto) 2>nul & del "%~f0"
"""
    with open(script, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(conteudo)
    return script


def executar_script_pendente(script: str) -> None:
    """Dispara o script de atualização do Windows desacoplado deste processo."""
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(["cmd.exe", "/c", script], creationflags=flags, close_fds=True)


def _atualizar_empacotado(download_url: str, sha256_esperado: str, report) -> dict:
    if not download_url:
        return {
            "sucesso": False,
            "erro": "A release não possui pacote para esta plataforma. Baixe manualmente pela página de releases.",
        }

    raiz = diretorio_instalacao()
    nome_arquivo = download_url.rsplit("/", 1)[-1] or "VesperaSci-atualizacao"

    if sys.platform == "win32" and download_url.lower().endswith(".zip") and _pasta_gravavel(raiz):
        pasta_temp = tempfile.mkdtemp(prefix="VesperaSci_update_")
        report(15, "Baixando pacote oficial do GitHub...")
        buffer_zip = io.BytesIO()
        _baixar(download_url, buffer_zip, report, sha256_esperado=sha256_esperado)

        report(70, "Extraindo pacote de atualização...")
        buffer_zip.seek(0)
        with zipfile.ZipFile(buffer_zip, "r") as zf:
            zf.extractall(pasta_temp)
        origem = _localizar_raiz_pacote(pasta_temp, "VesperaSci.exe")

        report(90, "Preparando a instalação...")
        script = _gerar_script_windows(origem, raiz, pasta_temp)
        report(100, "Atualização pronta. Ela será instalada ao reiniciar o Vespera Sci.")
        return {
            "sucesso": True,
            "metodo": "staging_windows",
            "acao_pos": ACAO_APLICAR_AO_FECHAR,
            "script": script,
            "detalhe": "A nova versão será instalada assim que o Vespera Sci fechar.",
        }

    # macOS (.dmg) ou instalação sem permissão de escrita: entrega o instalador ao usuário
    destino = os.path.join(_pasta_downloads(), nome_arquivo)
    report(15, "Baixando instalador oficial do GitHub...")
    with open(destino + ".part", "wb") as f:
        _baixar(download_url, f, report, pct_fim=95, sha256_esperado=sha256_esperado)
    os.replace(destino + ".part", destino)
    report(100, "Instalador baixado.")
    return {
        "sucesso": True,
        "metodo": "download_instalador",
        "acao_pos": ACAO_ABRIR_INSTALADOR,
        "arquivo": destino,
        "detalhe": f"Instalador salvo em {destino}. Feche o Vespera Sci e instale a nova versão.",
    }


def baixar_e_aplicar_atualizacao(
    canal: str = "stable",
    download_url: str = "",
    sha_remoto_full: str = "",
    progress_callback=None,
    sha256_esperado: str = "",
) -> dict:
    """
    Baixa e aplica a atualização conforme o tipo de instalação (ver docstring do módulo).
    O resultado traz "acao_pos": o que a interface deve fazer em seguida.
    """
    def report(pct: int, msg: str):
        if progress_callback:
            progress_callback(pct, msg)

    report(5, "Iniciando conexão de atualização...")

    try:
        if executando_empacotado():
            if canal != "stable":
                return {"sucesso": False, "erro": "O aplicativo instalado só pode ser atualizado pelo Canal Estável."}
            return _atualizar_empacotado(download_url, sha256_esperado, report)

        raiz = diretorio_codigo_fonte()
        requisitos_antes = _ler_arquivo(os.path.join(raiz, "requirements.txt"))

        if canal == "dev" and os.path.isdir(os.path.join(raiz, ".git")):
            report(20, "Sincronizando via Git (git pull --ff-only origin main)...")
            try:
                res = subprocess.run(
                    ["git", "pull", "--ff-only", "origin", BRANCH],
                    cwd=raiz,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            except (OSError, subprocess.SubprocessError) as e:
                return {"sucesso": False, "erro": f"Não foi possível executar o Git: {e}"}
            if res.returncode != 0:
                # Nunca cai para o download do zip: isso sobrescreveria alterações locais do repositório
                return {
                    "sucesso": False,
                    "erro": "O 'git pull' falhou (há alterações locais ou divergência com a main). "
                    "Resolva no terminal e tente novamente.\n\n" + (res.stderr or res.stdout).strip(),
                }
            detalhe = res.stdout.strip()
            if _ler_arquivo(os.path.join(raiz, "requirements.txt")) != requisitos_antes:
                report(80, "Instalando novas dependências...")
                detalhe += "\n" + _instalar_dependencias(raiz)
            report(100, "Atualização concluída com sucesso via Git!")
            return {"sucesso": True, "metodo": "git_pull", "acao_pos": ACAO_REINICIAR, "detalhe": detalhe}

        url_alvo = download_url or f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/{BRANCH}.zip"
        report(15, "Baixando pacote oficial do GitHub...")
        buffer_zip = io.BytesIO()
        _baixar(url_alvo, buffer_zip, report, sha256_esperado=sha256_esperado)

        report(70, "Extraindo pacote de atualização...")
        with tempfile.TemporaryDirectory(prefix="VesperaSci_update_") as pasta_temp:
            buffer_zip.seek(0)
            with zipfile.ZipFile(buffer_zip, "r") as zf:
                zf.extractall(pasta_temp)
            origem = _localizar_raiz_pacote(pasta_temp, "main.py")
            if not os.path.isdir(os.path.join(origem, "core")):
                raise ValueError("Pacote de atualização inválido: pasta 'core' ausente.")

            report(85, "Atualizando módulos do Vespera Sci (preservando seus projetos salvos)...")
            removidos = _aplicar_pacote_codigo_fonte(origem, raiz)

        if sha_remoto_full:
            with open(os.path.join(raiz, ".last_update_sha"), "w", encoding="utf-8") as f:
                f.write(sha_remoto_full)

        detalhe = "Arquivos atualizados via GitHub."
        if removidos:
            detalhe += f" Módulos obsoletos removidos: {', '.join(removidos)}."
        if _ler_arquivo(os.path.join(raiz, "requirements.txt")) != requisitos_antes:
            report(92, "Instalando novas dependências...")
            detalhe += " " + _instalar_dependencias(raiz)

        report(100, "Atualização concluída com sucesso!")
        return {"sucesso": True, "metodo": "zip_download", "acao_pos": ACAO_REINICIAR, "detalhe": detalhe}

    except Exception as e:
        logger.exception("Falha ao aplicar atualização")
        return {"sucesso": False, "erro": str(e)}
