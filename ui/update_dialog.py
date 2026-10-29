"""
Janela Modal de Verificação e Atualização Automática via GitHub para o Vespera Sci.
Permite alternar entre o Canal Oficial Estável (Releases) e o Canal de Desenvolvimento (Commits da branch main).
Totalmente em português, sem emojis e com identidade visual acadêmica e profissional.
"""

import sys
import webbrowser
from PySide6.QtCore import QProcess, QSettings, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from core.paths import executando_empacotado
from core.updater import (
    ACAO_ABRIR_INSTALADOR,
    ACAO_APLICAR_AO_FECHAR,
    baixar_e_aplicar_atualizacao,
    executar_script_pendente,
    verificar_atualizacao_github,
)
from ui.icons import get_icon


class CheckUpdateWorker(QThread):
    """Thread em segundo plano para consultar a API do GitHub sem travar a interface."""

    finishedCheck = Signal(dict)

    def __init__(self, canal: str = "stable"):
        super().__init__()
        self.canal = canal

    def run(self):
        res = verificar_atualizacao_github(canal=self.canal)
        self.finishedCheck.emit(res)


class ApplyUpdateWorker(QThread):
    """Thread em segundo plano para baixar e aplicar os arquivos do GitHub."""

    progressUpdated = Signal(int, str)
    finishedApply = Signal(dict)

    def __init__(self, canal: str = "stable", download_url: str = "", sha_remoto_full: str = "", sha256_esperado: str = ""):
        super().__init__()
        self.canal = canal
        self.download_url = download_url
        self.sha_remoto_full = sha_remoto_full
        self.sha256_esperado = sha256_esperado

    def run(self):
        res = baixar_e_aplicar_atualizacao(
            canal=self.canal,
            download_url=self.download_url,
            sha_remoto_full=self.sha_remoto_full,
            sha256_esperado=self.sha256_esperado,
            progress_callback=lambda pct, msg: self.progressUpdated.emit(pct, msg),
        )
        self.finishedApply.emit(res)


class UpdateDialog(QDialog):
    """Modal de gerenciamento de atualizações com suporte a canais Estável e Dev."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atualizações e Sincronização — Vespera Sci")
        self.resize(640, 560)
        self.setMinimumSize(560, 480)
        self.setModal(True)

        self.settings = QSettings("VesperaSci", "VesperaSci")
        self._canal_atual = str(self.settings.value("update_channel", "stable"))
        if self._canal_atual not in ("stable", "dev"):
            self._canal_atual = "stable"

        self._sha_remoto_full = ""
        self._download_url = ""
        self._sha256_esperado = ""
        self._html_url = ""
        self._script_pendente = ""
        self._check_worker = None
        self._apply_worker = None

        self._build_ui()
        self._iniciar_verificacao()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        # 1. Cabeçalho com Ícone e Descrição
        header = QHBoxLayout()
        header.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("github", color="#2563eb", size=28).pixmap(28, 28))
        header.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_tit = QLabel("<b>Atualização e Sincronização com o GitHub</b>")
        lbl_tit.setStyleSheet("font-size: 15px;")
        lbl_sub = QLabel("Gerenciamento de versões do Vespera Sci via repositório oficial Igorhls/vespera-sci.")
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("font-size: 11.5px;")
        title_box.addWidget(lbl_tit)
        title_box.addWidget(lbl_sub)
        header.addLayout(title_box, stretch=1)
        root.addLayout(header)

        # 2. Card de Seleção de Canal (Estável vs Dev)
        card_canal = QFrame()
        card_canal.setObjectName("cardPanel")
        canal_layout = QHBoxLayout(card_canal)
        canal_layout.setContentsMargins(12, 10, 12, 10)
        canal_layout.setSpacing(10)

        lbl_canal_rotulo = QLabel("<b>Canal de Atualização:</b>")
        canal_layout.addWidget(lbl_canal_rotulo)

        self.cmb_canal = QComboBox()
        self.cmb_canal.addItem("Oficial Estável (Releases Oficiais — Recomendado)", "stable")
        self.cmb_canal.addItem("Desenvolvimento (Commits da branch main — Dev)", "dev")
        if self._canal_atual == "dev":
            self.cmb_canal.setCurrentIndex(1)
        else:
            self.cmb_canal.setCurrentIndex(0)
        self.cmb_canal.currentIndexChanged.connect(self._on_canal_changed)
        canal_layout.addWidget(self.cmb_canal, stretch=1)

        root.addWidget(card_canal)

        # 3. Card de Status e Resumo
        self.card_status = QFrame()
        self.card_status.setObjectName("cardPanel")
        status_layout = QHBoxLayout(self.card_status)
        status_layout.setContentsMargins(14, 12, 14, 12)
        status_layout.setSpacing(12)

        self.lbl_status_icon = QLabel()
        self.lbl_status_icon.setPixmap(get_icon("info", color="#2563eb", size=24).pixmap(24, 24))
        status_layout.addWidget(self.lbl_status_icon, alignment=Qt.AlignTop)

        info_box = QVBoxLayout()
        info_box.setSpacing(4)
        self.lbl_status_titulo = QLabel("<b>Consultando repositório oficial no GitHub...</b>")
        self.lbl_status_titulo.setStyleSheet("font-size: 13.5px;")
        self.lbl_status_desc = QLabel("Verificando se há novas versões disponíveis para o canal selecionado.")
        self.lbl_status_desc.setWordWrap(True)
        self.lbl_status_desc.setStyleSheet("font-size: 12px;")
        info_box.addWidget(self.lbl_status_titulo)
        info_box.addWidget(self.lbl_status_desc)
        status_layout.addLayout(info_box, stretch=1)

        root.addWidget(self.card_status)

        # 4. Painel de Metadados e Notas da Versão (Changelog)
        card_detalhes = QFrame()
        card_detalhes.setObjectName("cardPanel")
        det_layout = QVBoxLayout(card_detalhes)
        det_layout.setContentsMargins(12, 10, 12, 10)
        det_layout.setSpacing(8)

        self.lbl_metadados = QLabel("Versão instalada: Carregando...")
        self.lbl_metadados.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_metadados.setStyleSheet("font-size: 12px;")
        det_layout.addWidget(self.lbl_metadados)

        lbl_notas_tit = QLabel("<b>Notas da Versão e Registro de Alterações:</b>")
        lbl_notas_tit.setStyleSheet("font-size: 12px;")
        det_layout.addWidget(lbl_notas_tit)

        self.txt_notas = QTextBrowser()
        self.txt_notas.setMinimumHeight(130)
        self.txt_notas.setOpenExternalLinks(True)
        det_layout.addWidget(self.txt_notas)

        root.addWidget(card_detalhes, stretch=1)

        # 5. Barra de Progresso de Download/Instalação
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        self.lbl_progresso_msg = QLabel("")
        self.lbl_progresso_msg.setStyleSheet("font-size: 11.5px;")
        self.lbl_progresso_msg.setVisible(False)
        root.addWidget(self.lbl_progresso_msg)

        # 6. Rodapé de Ações Unificado
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(8)

        # Ações à Esquerda
        self.btn_verificar = QPushButton("Verificar Novamente")
        self.btn_verificar.setIcon(get_icon("refresh", size=14))
        self.btn_verificar.setCursor(Qt.PointingHandCursor)
        self.btn_verificar.clicked.connect(self._iniciar_verificacao)
        footer_layout.addWidget(self.btn_verificar)

        self.btn_abrir_browser = QPushButton("Ver no GitHub")
        self.btn_abrir_browser.setIcon(get_icon("external-link", size=14))
        self.btn_abrir_browser.setCursor(Qt.PointingHandCursor)
        self.btn_abrir_browser.setVisible(False)
        self.btn_abrir_browser.clicked.connect(self._abrir_no_navegador)
        footer_layout.addWidget(self.btn_abrir_browser)

        footer_layout.addStretch()

        # Ações à Direita
        self.btn_atualizar = QPushButton("Baixar e Atualizar Agora")
        self.btn_atualizar.setIcon(get_icon("download", color="#ffffff", size=14))
        self.btn_atualizar.setObjectName("btnPrimary")
        self.btn_atualizar.setCursor(Qt.PointingHandCursor)
        self.btn_atualizar.setVisible(False)
        self.btn_atualizar.clicked.connect(self._iniciar_aplicacao_update)
        footer_layout.addWidget(self.btn_atualizar)

        self.btn_reiniciar = QPushButton("Reiniciar Vespera Sci")
        self.btn_reiniciar.setIcon(get_icon("refresh", color="#ffffff", size=14))
        self.btn_reiniciar.setObjectName("btnSuccess")
        self.btn_reiniciar.setCursor(Qt.PointingHandCursor)
        self.btn_reiniciar.setVisible(False)
        self.btn_reiniciar.clicked.connect(self._reiniciar_app)
        footer_layout.addWidget(self.btn_reiniciar)

        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.setCursor(Qt.PointingHandCursor)
        self.btn_fechar.clicked.connect(self.reject)
        footer_layout.addWidget(self.btn_fechar)

        root.addLayout(footer_layout)

    def _on_canal_changed(self, index: int):
        canal_selecionado = self.cmb_canal.itemData(index)
        if canal_selecionado != self._canal_atual:
            self._canal_atual = canal_selecionado
            self.settings.setValue("update_channel", canal_selecionado)
            self._iniciar_verificacao()

    def _iniciar_verificacao(self):
        self.btn_atualizar.setVisible(False)
        self.btn_abrir_browser.setVisible(False)
        self.btn_verificar.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        canal_nome = "Oficial Estável" if self._canal_atual == "stable" else "Desenvolvimento (Dev)"
        self.lbl_status_icon.setPixmap(get_icon("info", color="#2563eb", size=24).pixmap(24, 24))
        self.lbl_status_titulo.setText(f"<b>Consultando Canal {canal_nome}...</b>")
        self.lbl_status_desc.setText("Aguarde a resposta do repositório oficial no GitHub.")
        self.lbl_metadados.setText("Versão instalada: Consultando...")
        self.txt_notas.setPlainText("Consultando notas de versão no GitHub...")

        self._check_worker = CheckUpdateWorker(canal=self._canal_atual)
        self._check_worker.finishedCheck.connect(self._ao_terminar_verificacao)
        self._check_worker.start()

    def _ao_terminar_verificacao(self, res: dict):
        self.btn_verificar.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)

        if not res.get("sucesso"):
            self.lbl_status_icon.setPixmap(get_icon("alert-circle", color="#dc2626", size=24).pixmap(24, 24))
            self.lbl_status_titulo.setText("<b>Não foi possível verificar atualizações.</b>")
            self.lbl_status_desc.setText(res.get("erro", "Erro de conexão com o GitHub."))
            self.txt_notas.setPlainText(
                "Certifique-se de que o computador está conectado à internet e tente novamente."
            )
            return

        self._sha_remoto_full = res.get("sha_remoto_full", "")
        self._download_url = res.get("download_url", "")
        self._sha256_esperado = res.get("sha256_esperado", "")
        self._html_url = res.get("html_url", "")

        v_local = res.get("versao_local", "1.0.0")
        v_remota = res.get("versao_remota", "1.0.0")
        canal = res.get("canal", "stable")
        tem_update = res.get("tem_atualizacao", False)

        if self._html_url:
            self.btn_abrir_browser.setVisible(True)

        if canal == "stable":
            titulo = res.get("titulo_release", f"v{v_remota}")
            data_pub = res.get("data_remota", "")
            notas = res.get("notas_versao", "Nenhuma nota de versão cadastrada.")

            self.lbl_metadados.setText(
                f"<b>Versão Instalada:</b> v{v_local} &nbsp;|&nbsp; "
                f"<b>Última Release Oficial:</b> {titulo} {f'({data_pub})' if data_pub else ''}"
            )
            self.txt_notas.setMarkdown(notas)

            if tem_update:
                self.lbl_status_icon.setPixmap(get_icon("download", color="#2563eb", size=24).pixmap(24, 24))
                self.lbl_status_titulo.setText(f"<b>Uma nova versão oficial (v{v_remota}) está disponível!</b>")
                self.lbl_status_desc.setText(
                    "Clique em 'Baixar e Atualizar Agora' para atualizar sua instalação. "
                    "Seus projetos salvos serão preservados."
                )
                self.btn_atualizar.setText("Baixar e Atualizar Agora")
                self.btn_atualizar.setVisible(True)
            else:
                self.lbl_status_icon.setPixmap(get_icon("check-circle", color="#16a34a", size=24).pixmap(24, 24))
                self.lbl_status_titulo.setText(f"<b>Seu Vespera Sci está na versão estável mais recente (v{v_local}).</b>")
                self.lbl_status_desc.setText(
                    "Nenhuma nova release foi publicada desde sua última atualização. "
                    "O canal estável protege sua instalação de alterações intermediárias de desenvolvimento."
                )

        else:
            sha_l = res.get("sha_local", "N/D")
            sha_r = res.get("sha_remoto", "N/D")
            msg = res.get("mensagem_commit", "")
            data_com = res.get("data_remota", "")

            self.lbl_metadados.setText(
                f"<b>Commit Local:</b> <code>{sha_l}</code> &nbsp;|&nbsp; "
                f"<b>Último Commit no GitHub (main):</b> <code>{sha_r}</code> {f'({data_com})' if data_com else ''}"
            )
            self.txt_notas.setPlainText(
                f"Mensagem do Commit:\n{msg}\n\n"
                f"Repositório: https://github.com/Igorhls/vespera-sci/commits/main"
            )

            if tem_update:
                self.lbl_status_icon.setPixmap(get_icon("download", color="#2563eb", size=24).pixmap(24, 24))
                self.lbl_status_titulo.setText("<b>Novos commits de desenvolvimento disponíveis na branch main.</b>")
                self.lbl_status_desc.setText(
                    "Você está no Canal de Desenvolvimento (Dev). Clique abaixo para sincronizar com as alterações mais recentes."
                )
                self.btn_atualizar.setText("Sincronizar com a Branch Main")
                self.btn_atualizar.setVisible(True)
            else:
                self.lbl_status_icon.setPixmap(get_icon("check-circle", color="#16a34a", size=24).pixmap(24, 24))
                self.lbl_status_titulo.setText("<b>Sua instalação já está sincronizada com o último commit da branch main.</b>")
                self.lbl_status_desc.setText("Não há novos commits pendentes no repositório.")

    def _abrir_no_navegador(self):
        if self._html_url:
            webbrowser.open(self._html_url)

    def _iniciar_aplicacao_update(self):
        self.btn_atualizar.setEnabled(False)
        self.btn_fechar.setEnabled(False)
        self.btn_verificar.setEnabled(False)
        self.cmb_canal.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_progresso_msg.setVisible(True)

        self._apply_worker = ApplyUpdateWorker(
            canal=self._canal_atual,
            download_url=self._download_url,
            sha_remoto_full=self._sha_remoto_full,
            sha256_esperado=self._sha256_esperado,
        )
        self._apply_worker.progressUpdated.connect(self._ao_atualizar_progresso)
        self._apply_worker.finishedApply.connect(self._ao_terminar_update)
        self._apply_worker.start()

    def _ao_atualizar_progresso(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_progresso_msg.setText(msg)

    def _ao_terminar_update(self, res: dict):
        self.btn_fechar.setEnabled(True)
        self.btn_verificar.setEnabled(True)
        self.cmb_canal.setEnabled(True)
        if res.get("sucesso"):
            self.progress_bar.setValue(100)
            self.lbl_status_icon.setPixmap(get_icon("check-circle", color="#16a34a", size=24).pixmap(24, 24))
            self.btn_atualizar.setVisible(False)
            acao = res.get("acao_pos")
            if acao == ACAO_ABRIR_INSTALADOR:
                arquivo = res.get("arquivo", "")
                self.lbl_status_titulo.setText("<b>Instalador da nova versão baixado.</b>")
                self.lbl_status_desc.setText(
                    f"O instalador foi salvo em:\n{arquivo}\n"
                    "Feche o Vespera Sci e instale a nova versão (no macOS, arraste o app para Applications)."
                )
                if arquivo:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(arquivo))
                return
            self._script_pendente = res.get("script", "") if acao == ACAO_APLICAR_AO_FECHAR else ""
            self.lbl_status_titulo.setText(
                "<b>Atualização pronta para instalar.</b>" if self._script_pendente else "<b>Atualização concluída com sucesso!</b>"
            )
            detalhe = res.get("detalhe", "")
            self.lbl_status_desc.setText(
                "Clique em 'Reiniciar Vespera Sci' para carregar a nova versão." + (f"\n{detalhe}" if detalhe else "")
            )
            self.btn_reiniciar.setVisible(True)
        else:
            self.btn_atualizar.setEnabled(True)
            QMessageBox.critical(
                self,
                "Erro na Atualização",
                f"Ocorreu um erro ao atualizar o Vespera Sci:\n{res.get('erro')}",
            )

    def _reiniciar_app(self):
        if self._script_pendente:
            # O script aguarda este processo encerrar, instala a nova versão e reabre o app
            executar_script_pendente(self._script_pendente)
        elif executando_empacotado():
            QProcess.startDetached(sys.executable, sys.argv[1:])
        else:
            QProcess.startDetached(sys.executable, sys.argv)
        QApplication.quit()
