from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QTabWidget,
    QWidget,
    QFormLayout,
    QVBoxLayout,
    QLineEdit,
    QComboBox,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QSizePolicy
from data_shuttle import utils


class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setModal(True)
        self.resize(560, 360)
        self.settings = settings or {"connection_1": {}, "connection_2": {}}

        self.tabs = QTabWidget()
        self.first_tab = self._build_env_tab("connection_1")
        self.second_tab = self._build_env_tab("connection_2")
        self.tabs.addTab(self.first_tab, "Connection 1")
        self.tabs.addTab(self.second_tab, "Connection 2")

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            orientation=Qt.Horizontal,
            parent=self,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

        bottom_bar = QHBoxLayout()
        self.test_btn = QPushButton("Test Connection…")
        self.test_btn.clicked.connect(self._on_test_connection)
        bottom_bar.addWidget(self.test_btn)
        bottom_bar.addStretch(1)
        bottom_bar.addWidget(self.buttons)

        root.addLayout(bottom_bar)

        self._load_values("connection_1")
        self._load_values("connection_2")

    def _build_env_tab(self, env_key: str) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setLabelAlignment(Qt.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        db_type = QComboBox(); db_type.addItems(["Oracle", "PostgreSQL"])
        protocol = QComboBox(); protocol.addItems(["TCP", "TCPS/SSL"])
        host = QLineEdit(); host.setPlaceholderText("예: 10.10.10.10 또는 db.example.com")
        port = QLineEdit(); port.setPlaceholderText("예: 1521 / 5432")

        svc_label = QLabel("Service/DB")
        svc = QLineEdit(); svc.setPlaceholderText("Oracle: SERVICE_NAME / PG: 데이터베이스명")
       
        user = QLineEdit(); user.setPlaceholderText("계정 ID")
        pw = QLineEdit(); pw.setPlaceholderText("비밀번호"); pw.setEchoMode(QLineEdit.Password)

        lbl_dbtype   = QLabel("DB 타입")
        lbl_proto    = QLabel("프로토콜")
        lbl_host     = QLabel("Host")
        lbl_port     = QLabel("Port")
        lbl_user     = QLabel("ID")
        lbl_pw       = QLabel("Password")

        def _max_label_width(label: QLabel, samples, extra_px: int = 16) -> int:
            fm = QFontMetrics(label.font())
            return max(fm.horizontalAdvance(s) for s in samples) + extra_px

        def _apply_fixed_label(label: QLabel, width: int):
            label.setFixedWidth(width)
            label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
        label_samples = ["DB 타입", "프로토콜", "Host", "Port", "SERVICE_NAME/SID", "DB 이름", "ID", "Password"]
        common_width = _max_label_width(lbl_dbtype, label_samples)

        for lab in (lbl_dbtype, lbl_proto, lbl_host, lbl_port, svc_label, lbl_user, lbl_pw):
            _apply_fixed_label(lab, common_width)
        
        form.addRow(lbl_dbtype, db_type)
        form.addRow(lbl_proto, protocol)
        form.addRow(lbl_host, host)
        form.addRow(lbl_port, port)
        form.addRow(svc_label, svc)
        form.addRow(lbl_user, user)
        form.addRow(lbl_pw, pw)

        setattr(self, f"{env_key}_db_type", db_type)
        setattr(self, f"{env_key}_protocol", protocol)
        setattr(self, f"{env_key}_host", host)
        setattr(self, f"{env_key}_port", port)
        setattr(self, f"{env_key}_svc_label", svc_label)
        setattr(self, f"{env_key}_svc", svc)
        setattr(self, f"{env_key}_user", user)
        setattr(self, f"{env_key}_pw", pw)

        db_type.currentTextChanged.connect(lambda _: self._apply_db_type(env_key))
        return w
    
    def _on_test_connection(self):
        idx = self.tabs.currentIndex()
        env_key = "connection_1" if idx == 0 else "connection_2"
        tab_name = "Connection 1" if idx == 0 else "Connection 2"
        cfg = {
            "db_type": getattr(self, f"{env_key}_db_type").currentText(),
            "protocol": getattr(self, f"{env_key}_protocol").currentText(),
            "host": getattr(self, f"{env_key}_host").text().strip(),
            "port": self._to_int(getattr(self, f"{env_key}_port").text()),
            "service_or_db": getattr(self, f"{env_key}_svc").text().strip(),
            "user": getattr(self, f"{env_key}_user").text().strip(),
            "password": getattr(self, f"{env_key}_pw").text(),
        }

        ok, detail = utils.test_connection(cfg, timeout=5)
        if ok:
            QMessageBox.information(self, "Test Connection", f"[{tab_name}] 연결에 성공했습니다.\n{detail}")
        else:
            QMessageBox.warning(self, "Test Connection", f"[{tab_name}] 연결에 실패했습니다.\n{detail}")

    def _load_values(self, env_key: str):
        data = self.settings.get(env_key, {})
        getattr(self, f"{env_key}_db_type").setCurrentText(data.get("db_type", "Oracle"))
        getattr(self, f"{env_key}_protocol").setCurrentText(data.get("protocol", "TCP"))
        getattr(self, f"{env_key}_host").setText(data.get("host", ""))
        getattr(self, f"{env_key}_port").setText(str(data.get("port", "")))
        getattr(self, f"{env_key}_svc").setText(data.get("service_or_db", ""))
        getattr(self, f"{env_key}_user").setText(data.get("user", ""))
        getattr(self, f"{env_key}_pw").setText(data.get("password", ""))

        self._apply_db_type(env_key)

    def _apply_db_type(self, env_key: str):
        dbt = getattr(self, f"{env_key}_db_type").currentText()
        svc_label = getattr(self, f"{env_key}_svc_label")
        svc_edit  = getattr(self, f"{env_key}_svc")

        if dbt == "PostgreSQL":
            svc_label.setText("DB 이름")
            svc_edit.setPlaceholderText("예: mydb")
            getattr(self, f"{env_key}_port").setPlaceholderText("예: 5432")
        else:
            # Oracle
            svc_label.setText("SERVICE_NAME/SID")
            svc_edit.setPlaceholderText("예: ORCL / PROD (SERVICE_NAME 또는 SID)")
            getattr(self, f"{env_key}_port").setPlaceholderText("예: 1521")
        
        self._set_default_port(env_key, dbt)

    def _set_default_port(self, env_key: str, db_type_text: str):
        """포트 입력칸이 비어있거나 기존 기본값이면, DB 타입에 맞는 기본 포트로 설정."""
        port_edit = getattr(self, f"{env_key}_port")
        cur = (port_edit.text() or "").strip()

        defaults = {
            "oracle": "1521",
            "postgresql": "5432",
        }
        new_db = (db_type_text or "").lower()
        new_default = defaults.get(new_db)
        if not new_default:
            return
        if (not cur) or (cur in defaults.values()):
            port_edit.setText(new_default)

    def values(self) -> dict:
        return {
            "connection_1": {
                "db_type": self.connection_1_db_type.currentText(),
                "protocol": self.connection_1_protocol.currentText(),
                "host": self.connection_1_host.text().strip(),
                "port": self._to_int(self.connection_1_port.text()),
                "service_or_db": self.connection_1_svc.text().strip(),
                "user": self.connection_1_user.text().strip(),
                "password": self.connection_1_pw.text(),
            },
            "connection_2": {
                "db_type": self.connection_2_db_type.currentText(),
                "protocol": self.connection_2_protocol.currentText(),
                "host": self.connection_2_host.text().strip(),
                "port": self._to_int(self.connection_2_port.text()),
                "service_or_db": self.connection_2_svc.text().strip(),
                "user": self.connection_2_user.text().strip(),
                "password": self.connection_2_pw.text(),
            },
        }
    
    @staticmethod
    def _to_int(s: str):
        try:
            return int(s)
        except Exception:
            return None
