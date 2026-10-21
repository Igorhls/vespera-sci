"""
Janela Modal de Verificação e Atualização Automática via GitHub para o Vespera Sci.
Permite alternar entre o Canal Oficial Estável (Releases) e o Canal de Desenvolvimento (Commits da branch main).
Totalmente em português, sem emojis e com identidade visual acadêmica e profissional.
"""

import sys
import webbrowser
from PySide6.QtCore import QProcess, QSettings, Qt, QThread, Signal
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
    QVBoxLayout,
)

from core.updater import baixar_e_aplicar_atualizacao, verificar_atualizacao_github
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

    def __init__(self, canal: str = "stable", download_url: str = "", sha_remoto_full: str = ""):
        super().__init__()
        self.canal = canal
        self.download_url = download_url
        self.sha_remoto_full = sha_remoto_full

    def run(self):
        res = baixar_e_aplicar_atualizacao(
            canal=self.canal,
            download_url=self.download_url,
            sha_remoto_full=self.sha_remoto_full,
            progress_callback=lambda pct, msg: self.progressUpdated.emit(pct, msg),
        )
        self.finishedApply.emit(res)


class UpdateDialog(QDialog):
    """Modal de gerenciamento de atualizações com suporte a canais Estável e Dev."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atualizador de Software — Vespera Sci")
        self.setMinimumWidth(560)
        self.setModal(True)

        self.settings = QSettings("VesperaSci", "VesperaSci")
        self._canal_atual = str(self.settings.value("update_channel", "stable"))
        if self._canal_atual not in ("stable", "dev"):
            self._canal_atual = "stable"

        self._sha_remoto_full = ""
        self._download_url = ""
        self._html_url = ""
        self._check_worker = None
        self._apply_worker = None

        self._build_ui()
        self._iniciar_verificacao()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Cabeçalho
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_icon("github", size=24).pixmap(24, 24))
        header_layout.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        lbl_header = QLabel("<b>Atualizações e Sincronização com o GitHub</b>")
        lbl_header.setStyleSheet("font-size: 15px;")
        lbl_sub = QLabel("Gerenciamento de versões estáveis e experimentais do Vespera Sci.")
        lbl_sub.setStyleSheet("color: #64748b; font-size: 11.5px;")
        title_box.addWidget(lbl_header)
        title_box.addWidget(lbl_sub)
        header_layout.addLayout(title_box, stretch=1)
        layout.addLayout(header_layout)

        # Seletor de Canal de Atualização
        channel_card = QFrame()
        channel_card.setObjectName("cardPanel")
        channel_card.setStyleSheet(
            "QFrame#cardPanel { background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.1); "
            "border-radius: 8px; padding: 6px; }"
        )
        ch_layout = QHBoxLayout(channel_card)
        ch_layout.setContentsMargins(12, 8, 12, 8)
        ch_layout.setSpacing(10)

        lbl_canal_tit = QLabel("<b>Canal de Atualização:</b>")
        ch_layout.addWidget(lbl_canal_tit)

        self.cmb_canal = QComboBox()
        self.cmb_canal.addItem("Oficial Estável (Recomendado — Releases Oficiais)", "stable")
        self.cmb_canal.addItem("Desenvolvimento (Commits da branch main — Dev)", "dev")
        if self._canal_atual == "dev":
            self.cmb_canal.setCurrentIndex(1)
        else:
            self.cmb_canal.setCurrentIndex(0)
        self.cmb_canal.currentIndexChanged.connect(self._on_canal_changed)
        ch_layout.addWidget(self.cmb_canal, stretch=1)

        layout.addWidget(channel_card)

        # Status Principal
        self.lbl_status_principal = QLabel("Consultando repositório oficial <b>Igorhls/vespera-sci</b> no GitHub...")
        self.lbl_status_principal.setWordWrap(True)
        self.lbl_status_principal.setStyleSheet("font-size: 13px; line-height: 1.4;")
        layout.addWidget(self.lbl_status_principal)

        # Card de Detalhes da Versão
        self.frame_info = QFrame()
        self.frame_info.setObjectName("cardPanel")
        self.frame_info.setStyleSheet(
            "QFrame#cardPanel { background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.1); "
            "border-radius: 8px; padding: 10px; }"
        )
        info_layout = QVBoxLayout(self.frame_info)
        info_layout.setContentsMargins(12, 10, 12, 10)
        info_layout.setSpacing(6)

        self.lbl_detalhes = QLabel("Verificando versão instalada e repositório remoto...")
        self.lbl_detalhes.setWordWrap(True)
        self.lbl_detalhes.setStyleSheet("font-size: 12px; line-height: 1.5;")
        info_layout.addWidget(self.lbl_detalhes)
        layout.addWidget(self.frame_info)

        # Barra de Progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { min-height: 14px; text-align: center; }")
        layout.addWidget(self.progress_bar)

        self.lbl_progresso_msg = QLabel("")
        self.lbl_progresso_msg.setStyleSheet("color: #64748b; font-size: 11.5px;")
        self.lbl_progresso_msg.setVisible(False)
        layout.addWidget(self.lbl_progresso_msg)

        # Rodapé de Ações
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_abrir_browser = QPushButton("Ver Release no GitHub")
        self.btn_abrir_browser.setIcon(get_icon("external-link", size=14))
        self.btn_abrir_browser.setCursor(Qt.PointingHandCursor)
        self.btn_abrir_browser.setVisible(False)
        self.btn_abrir_browser.clicked.connect(self._abrir_no_navegador)
        btn_layout.addWidget(self.btn_abrir_browser)

        btn_layout.addStretch()

        self.btn_atualizar = QPushButton("Baixar e Atualizar Agora")
        self.btn_atualizar.setIcon(get_icon("download", color="#ffffff", size=15))
        self.btn_atualizar.setObjectName("btnPrimary")
        self.btn_atualizar.setCursor(Qt.PointingHandCursor)
        self.btn_atualizar.setMinimumHeight(34)
        self.btn_atualizar.setVisible(False)
        self.btn_atualizar.clicked.connect(self._iniciar_aplicacao_update)

        self.btn_reiniciar = QPushButton("Reiniciar Vespera Sci")
        self.btn_reiniciar.setIcon(get_icon("refresh-cw", color="#ffffff", size=15))
        self.btn_reiniciar.setObjectName("btnSuccess")
        self.btn_reiniciar.setCursor(Qt.PointingHandCursor)
        self.btn_reiniciar.setMinimumHeight(34)
        self.btn_reiniciar.setVisible(False)
        self.btn_reiniciar.clicked.connect(self._reiniciar_app)

        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.setMinimumHeight(34)
        self.btn_fechar.setCursor(Qt.PointingHandCursor)
        self.btn_fechar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_atualizar)
        btn_layout.addWidget(self.btn_reiniciar)
        btn_layout.addWidget(self.btn_fechar)
        layout.addLayout(btn_layout)

    def _on_canal_changed(self, index: int):
        canal_selecionado = self.cmb_canal.itemData(index)
        if canal_selecionado != self._canal_atual:
            self._canal_atual = canal_selecionado
            self.settings.setValue("update_channel", canal_selecionado)
            self._iniciar_verificacao()

    def _iniciar_verificacao(self):
        self.btn_atualizar.setVisible(False)
        self.btn_abrir_browser.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        canal_nome = "Oficial Estável" if self._canal_atual == "stable" else "Desenvolvimento (Dev)"
        self.lbl_status_principal.setText(f"Consultando <b>Canal {canal_nome}</b> no repositório GitHub...")
        self.lbl_detalhes.setText("Aguarde a resposta da API do GitHub...")

        self._check_worker = CheckUpdateWorker(canal=self._canal_atual)
        self._check_worker.finishedCheck.connect(self._ao_terminar_verificacao)
        self._check_worker.start()

    def _ao_terminar_verificacao(self, res: dict):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)

        if not res.get("sucesso"):
            self.lbl_status_principal.setText("<b>Não foi possível verificar atualizações no momento.</b>")
            self.lbl_detalhes.setText(f"Erro: {res.get('erro', 'Falha de conexão.')}")
            return

        self._sha_remoto_full = res.get("sha_remoto_full", "")
        self._download_url = res.get("download_url", "")
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
            notas = res.get("notas_versao", "")
            detalhes_html = (
                f"<b>Canal:</b> Oficial Estável (Releases do GitHub)<br>"
                f"<b>Versão Instalada:</b> v{v_local}<br>"
                f"<b>Última Release Publicada:</b> {titulo} {f'({data_pub})' if data_pub else ''}<br><br>"
                f"<b>Notas da Versão:</b><br><span style='color: #475569;'>{notas}</span>"
            )
            self.lbl_detalhes.setText(detalhes_html)

            if tem_update:
                self.lbl_status_principal.setText(
                    f"<b>Uma nova versão estável (v{v_remota}) está disponível no GitHub!</b><br>"
                    f"<span style='color: #64748b; font-size: 11.5px;'>"
                    f"Seus projetos salvos continuarão intactos após a atualização.</span>"
                )
                self.btn_atualizar.setText("Baixar e Atualizar Agora")
                self.btn_atualizar.setVisible(True)
            else:
                self.lbl_status_principal.setText(
                    f"<b>Seu Vespera Sci já está na versão estável mais recente (v{v_local}).</b><br>"
                    f"<span style='color: #64748b; font-size: 11.5px;'>"
                    f"Nenhuma nova release oficial foi publicada desde a sua instalação.</span>"
                )

        else:
            # Canal de Desenvolvimento (Dev)
            sha_l = res.get("sha_local", "N/D")
            sha_r = res.get("sha_remoto", "N/D")
            msg = res.get("mensagem_commit", "")
            data_com = res.get("data_remota", "")

            detalhes_html = (
                f"<b>Canal:</b> Desenvolvimento (Commits da branch <code>main</code>)<br>"
                f"<b>Commit Local:</b> <code>{sha_l}</code><br>"
                f"<b>Último Commit no GitHub:</b> <code>{sha_r}</code> {f'({data_com})' if data_com else ''}<br>"
                f"<b>Mensagem:</b> <i>{msg}</i>"
            )
            self.lbl_detalhes.setText(detalhes_html)

            if tem_update:
                self.lbl_status_principal.setText(
                    "<b>Novos commits de desenvolvimento estão disponíveis no repositório!</b><br>"
                    "<span style='color: #64748b; font-size: 11.5px;'>"
                    "Este canal permite testar alterações recentes antes da publicação da release oficial.</span>"
                )
                self.btn_atualizar.setText("Sincronizar com a Branch Main")
                self.btn_atualizar.setVisible(True)
            else:
                self.lbl_status_principal.setText(
                    "<b>Sua instalação está sincronizada com o último commit da branch main.</b>"
                )

    def _abrir_no_navegador(self):
        if self._html_url:
            webbrowser.open(self._html_url)

    def _iniciar_aplicacao_update(self):
        self.btn_atualizar.setEnabled(False)
        self.btn_fechar.setEnabled(False)
        self.cmb_canal.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_progresso_msg.setVisible(True)

        self._apply_worker = ApplyUpdateWorker(
            canal=self._canal_atual,
            download_url=self._download_url,
            sha_remoto_full=self._sha_remoto_full,
        )
        self._apply_worker.progressUpdated.connect(self._ao_atualizar_progresso)
        self._apply_worker.finishedApply.connect(self._ao_terminar_update)
        self._apply_worker.start()

    def _ao_atualizar_progresso(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_progresso_msg.setText(msg)

    def _ao_terminar_update(self, res: dict):
        self.btn_fechar.setEnabled(True)
        self.cmb_canal.setEnabled(True)
        if res.get("sucesso"):
            self.progress_bar.setValue(100)
            self.lbl_status_principal.setText(
                "<b>Atualização instalada com sucesso!</b><br>"
                "Reinicie o Vespera Sci para carregar as alterações."
            )
            self.btn_atualizar.setVisible(False)
            self.btn_reiniciar.setVisible(True)
        else:
            self.btn_atualizar.setEnabled(True)
            QMessageBox.critical(
                self,
                "Erro na Atualização",
                f"Ocorreu um erro ao atualizar o Vespera Sci:\n{res.get('erro')}",
            )

    def _reiniciar_app(self):
        QProcess.startDetached(sys.executable, sys.argv)
        QApplication.quit()
