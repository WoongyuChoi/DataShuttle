from PyQt5.QtWidgets import (
    QGridLayout,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QTableWidget,
    QHBoxLayout,
    QGroupBox,
    QToolButton,
    QLineEdit,
)


def init_ui(app_instance):
    layout = QVBoxLayout()

    # 상단 바: [↺ 초기화] [⚙ 설정]
    topbar = QHBoxLayout()
    topbar.addStretch(1)

    app_instance.top_reset_btn = QToolButton()
    app_instance.top_reset_btn.setText("↺ 초기화")
    app_instance.top_reset_btn.clicked.connect(app_instance.reset_ui)
    topbar.addWidget(app_instance.top_reset_btn)

    app_instance.settings_btn = QToolButton()
    app_instance.settings_btn.setText("⚙ 설정")
    app_instance.settings_btn.clicked.connect(app_instance.open_settings)
    topbar.addWidget(app_instance.settings_btn)

    layout.addLayout(topbar)

    # ─────────────────────────────────
    header_col = QGridLayout()

    # Origin
    origin_box = QGroupBox("Origin")
    ov = QVBoxLayout()
    app_instance.schema_input = QLineEdit()
    app_instance.schema_input.setPlaceholderText("예: PRD_PUBLIC …")
    app_instance.table_input = QLineEdit()
    app_instance.table_input.setPlaceholderText("예: JOB_TABLE …")
    ov.addWidget(QLabel("SCHEMA"))
    ov.addWidget(app_instance.schema_input)
    ov.addWidget(QLabel("TABLE"))
    ov.addWidget(app_instance.table_input)
    origin_box.setLayout(ov)
    header_col.addWidget(origin_box, 0, 0)

    # Destination
    dest_box = QGroupBox("Destination")
    dv = QVBoxLayout()
    app_instance.dest_schema_input = QLineEdit()
    app_instance.dest_schema_input.setPlaceholderText("예: DEV_PUBLIC … (미입력 시 Origin과 동일)")
    app_instance.dest_table_input = QLineEdit()
    app_instance.dest_table_input.setPlaceholderText("예: JOB_TABLE_DST … (미입력 시 Origin과 동일)")
    dv.addWidget(QLabel("SCHEMA"))
    dv.addWidget(app_instance.dest_schema_input)
    dv.addWidget(QLabel("TABLE"))
    dv.addWidget(app_instance.dest_table_input)
    dest_box.setLayout(dv)
    header_col.addWidget(dest_box, 0, 1)

    layout.addLayout(header_col)
    # ─────────────────────────────────

    # ─────────────────────────────────
    # WHERE 조건
    where_box = QGroupBox("WHERE")
    wv = QVBoxLayout()

    app_instance.where_input = QTextEdit()
    app_instance.where_input.setPlaceholderText(
        "-- 주의: WHERE 키워드는 빼고 조건만 작성 \n"
        "예)\n"
        "  START_DATE >= DATE '2025-09-01'\n"
        "  AND STATUS = 'COMPLETED'"
    )
    app_instance.where_input.setAcceptRichText(False)
    app_instance.where_input.setWordWrapMode(0)      # NoWrap
    app_instance.where_input.setFixedHeight(90)
    wv.addWidget(app_instance.where_input)

    where_box.setLayout(wv)
    layout.addWidget(where_box)
    # ─────────────────────────────────

    # ─────────────────────────────────
    app_instance.console_output = QTextEdit()
    app_instance.console_output.setReadOnly(True)
    app_instance.console_output.setMaximumHeight(120)
    layout.addWidget(QLabel("Console Output:"))
    layout.addWidget(app_instance.console_output)
    # ─────────────────────────────────

    # ─────────────────────────────────
    buttom_layout = QHBoxLayout()
    app_instance.migrate_button = QPushButton("Start Migration")
    app_instance.migrate_button.setDefault(True)
    if hasattr(app_instance, "start_migration"):
        app_instance.migrate_button.clicked.connect(app_instance.start_migration)
    buttom_layout.addWidget(app_instance.migrate_button)
    layout.addLayout(buttom_layout)
    # ─────────────────────────────────

    # ─────────────────────────────────
    app_instance.result_table = QTableWidget()
    app_instance.result_table.setMinimumHeight(200)
    layout.addWidget(QLabel("Result:"))
    layout.addWidget(app_instance.result_table)
    # ─────────────────────────────────

    app_instance.setLayout(layout)
    app_instance.setWindowTitle("DataShuttle")

    # 화면 해상도에 따른 윈도우 크기 조정 & 중앙 배치
    adjust_window_size(app_instance)
    center(app_instance)


def adjust_window_size(app_instance):
    """해상도에 따라 윈도우 크기를 조정하는 함수"""
    screen_geometry = app_instance.screen().availableGeometry()
    screen_width = screen_geometry.width()
    screen_height = screen_geometry.height()

    # 기본 비율 설정 (화면 크기의 50%)
    width_ratio = 0.5
    height_ratio = 0.5

    # 전체 화면 크기의 비율로 윈도우 크기 설정
    window_width = int(screen_width * width_ratio)
    window_height = int(screen_height * height_ratio)

    # 최소 크기 설정
    min_width = 900
    min_height = 600

    # 최소 크기보다 작은 경우, 최소 크기로 설정
    window_width = max(window_width, min_width)
    window_height = max(window_height, min_height)

    app_instance.resize(window_width, window_height)


def center(app_instance):
    """화면 중앙에 윈도우를 배치하는 함수"""
    qr = app_instance.frameGeometry()
    cp = app_instance.screen().availableGeometry().center()
    qr.moveCenter(cp)
    app_instance.move(qr.topLeft())


def log_to_console(app_instance, message: str):
    """콘솔 창에 로그 메시지를 출력하는 함수"""
    app_instance.console_output.append(message)
