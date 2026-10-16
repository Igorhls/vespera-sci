"""
Janela Modal de Verificação e Atualização Automática via GitHub para o Vespera Sci.
"""

import sys
from PySide6.QtCore import QProcess, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
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


class CheckUpdateWorker(QThread):
    """Thread em segundo plano para consultar a API do GitHub sem travar a janela."""

    finishedCheck = Signal(dict)

    def run(self):
        res = verificar_atualizacao_github()
        self.finishedCheck.emit(res)


class ApplyUpdateWorker(QThread):
    """Thread em segundo plano para baixar e aplicar os arquivos do GitHub."""

    progressUpdated = Signal(int, str)
    finishedApply = Signal(dict)

    def __init__(self, sha_remoto_full: str = ""):
        super().__init__()
        self.sha_remoto_full = sha_remoto_full

    def run(self):
        res = baixar_e_aplicar_atualizacao(
            sha_remoto_full=self.sha_remoto_full,
            progress_callback=lambda pct, msg: self.progressUpdated.emit(pct, msg),
        )
        self.finishedApply.emit(res)


class UpdateDialog(QDialog):
    """Modal interativo de atualização via GitHub (Igorhls/vespera-sci)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Atualizador Vespera Sci — GitHub Sync")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._sha_remoto_full = ""
        self._check_worker = None
        self._apply_worker = None

        self._build_ui()
        self._iniciar_verificacao()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        lbl_header = QLabel("<h3>🔄 Atualização Automática via GitHub</h3>")
        layout.addWidget(lbl_header)

        self.lbl_status_principal = QLabel("Consultando repositório oficial <b>Igorhls/vespera-sci</b>...")
        self.lbl_status_principal.setWordWrap(True)
        self.lbl_status_principal.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.lbl_status_principal)

        # Card de detalhes de versão
        self.frame_info = QFrame()
        self.frame_info.setFrameShape(QFrame.StyledPanel)
        info_layout = QVBoxLayout(self.frame_info)
        info_layout.setContentsMargins(12, 10, 12, 10)
        self.lbl_detalhes = QLabel("Verificando versão local e versão remota...")
        self.lbl_detalhes.setWordWrap(True)
        info_layout.addWidget(self.lbl_detalhes)
        layout.addWidget(self.frame_info)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.lbl_progresso_msg = QLabel("")
        self.lbl_progresso_msg.setStyleSheet("color: #555555; font-size: 11.5px;")
        self.lbl_progresso_msg.setVisible(False)
        layout.addWidget(self.lbl_progresso_msg)

        # Botões de ação
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_atualizar = QPushButton("⬇️ Baixar e Atualizar Agora")
        self.btn_atualizar.setCursor(Qt.PointingHandCursor)
        self.btn_atualizar.setMinimumHeight(34)
        self.btn_atualizar.setStyleSheet(
            "background-color: #216e39; color: white; font-weight: 600; padding: 6px 14px; border-radius: 5px;"
        )
        self.btn_atualizar.setVisible(False)
        self.btn_atualizar.clicked.connect(self._iniciar_aplicacao_update)

        self.btn_reiniciar = QPushButton("🚀 Reiniciar Vespera Sci Agora")
        self.btn_reiniciar.setCursor(Qt.PointingHandCursor)
        self.btn_reiniciar.setMinimumHeight(34)
        self.btn_reiniciar.setStyleSheet(
            "background-color: #1f5f8b; color: white; font-weight: 600; padding: 6px 14px; border-radius: 5px;"
        )
        self.btn_reiniciar.setVisible(False)
        self.btn_reiniciar.clicked.connect(self._reiniciar_app)

        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.setMinimumHeight(34)
        self.btn_fechar.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_atualizar)
        btn_layout.addWidget(self.btn_reiniciar)
        btn_layout.addWidget(self.btn_fechar)
        layout.addLayout(btn_layout)

    def _iniciar_verificacao(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Modo indeterminado durante a consulta
        self._check_worker = CheckUpdateWorker()
        self._check_worker.finishedCheck.connect(self._ao_terminar_verificacao)
        self._check_worker.start()

    def _ao_terminar_verificacao(self, res: dict):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)

        if not res.get("sucesso"):
            self.lbl_status_principal.setText("❌ <b>Não foi possível verificar atualizações no momento.</b>")
            self.lbl_detalhes.setText(res.get("erro", "Erro desconhecido de conexão."))
            return

        self._sha_remoto_full = res.get("sha_remoto_full", "")
        v_local = res.get("versao_local", "1.0.0")
        v_remota = res.get("versao_remota", "1.0.0")
        sha_l = res.get("sha_local", "N/D")
        sha_r = res.get("sha_remoto", "N/D")
        msg = res.get("mensagem_commit", "")
        data = res.get("data_remota", "")

        detalhes_html = (
            f"<b>Versão Instalada:</b> v{v_local} <code>({sha_l})</code><br>"
            f"<b>Versão no GitHub:</b> v{v_remota} <code>({sha_r})</code> — {data}<br>"
            f"<b>Última atualização no repositório:</b> <i>{msg}</i>"
        )
        self.lbl_detalhes.setText(detalhes_html)

        if res.get("tem_atualizacao"):
            self.lbl_status_principal.setText(
                "🎉 <b>Uma nova atualização está disponível no GitHub!</b><br>"
                "Seus projetos salvos continuarão intactos após a atualização."
            )
            self.btn_atualizar.setText("⬇️ Baixar e Atualizar Agora")
            self.btn_atualizar.setVisible(True)
        else:
            self.lbl_status_principal.setText("✅ <b>Seu Vespera Sci já está na versão mais recente!</b>")
            self.btn_atualizar.setText("🔄 Sincronizar Novamente com GitHub")
            self.btn_atualizar.setStyleSheet(
                "background-color: #f8f9fa; color: #333333; border: 1px solid #c4c9d0; padding: 6px 12px; border-radius: 5px;"
            )
            self.btn_atualizar.setVisible(True)

    def _iniciar_aplicacao_update(self):
        self.btn_atualizar.setEnabled(False)
        self.btn_fechar.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_progresso_msg.setVisible(True)

        self._apply_worker = ApplyUpdateWorker(self._sha_remoto_full)
        self._apply_worker.progressUpdated.connect(self._ao_atualizar_progresso)
        self._apply_worker.finishedApply.connect(self._ao_terminar_update)
        self._apply_worker.start()

    def _ao_atualizar_progresso(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.lbl_progresso_msg.setText(msg)

    def _ao_terminar_update(self, res: dict):
        self.btn_fechar.setEnabled(True)
        if res.get("sucesso"):
            self.progress_bar.setValue(100)
            self.lbl_status_principal.setText(
                "✅ <b>Atualização instalada com sucesso!</b><br>"
                "Clique no botão abaixo para reiniciar o Vespera Sci e carregar a nova versão."
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
