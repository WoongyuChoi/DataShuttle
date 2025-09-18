from PyQt5.QtWidgets import QWidget, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
from data_shuttle import ui_setup, utils
from data_shuttle.dialog.settings_dialog import SettingsDialog

class MigrationWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int, int)   # inserted, total
    error = pyqtSignal(int, str)      # row_index, error_message
    done = pyqtSignal(int, int)       # inserted_total, source_total

    def __init__(self, settings: dict, src_schema: str, src_tables_csv: str, where_text: str,
                 dst_schema: str, dst_tables: str | None = None, chunk_size: int = 10_000):
        super().__init__()
        self.settings = settings
        self.src_schema = src_schema
        self.src_tables_csv = src_tables_csv
        self.where_text = where_text
        self.dst_schema = dst_schema
        self.dst_tables = dst_tables or ""
        self.chunk_size = chunk_size

    def run(self):
        try:
            src_tables = [t.strip() for t in self.src_tables_csv.split(',') if t.strip()]
            dst_names  = [t.strip() for t in self.dst_tables.split(',')] if self.dst_tables else []
            # 목적지 테이블 매핑: 개수 같으면 페어 매핑, 아니면 동일명
            table_pairs = []
            for i, s in enumerate(src_tables):
                d = dst_names[i] if i < len(dst_names) and dst_names[i] else s
                table_pairs.append((s, d))

            # 엔진 생성
            src_engine = utils.create_engine_from_config(self.settings.get("connection_1", {}))
            dst_engine = utils.create_engine_from_config(self.settings.get("connection_2", {}))

            total_inserted = 0
            total_source = 0

            for src_tbl, dst_tbl in table_pairs:
                self.log.emit(f"[실행] 테이블 매핑: {self.src_schema}.{src_tbl}  →  {self.dst_schema}.{dst_tbl}")

                cnt = utils.count_rows(src_engine, self.src_schema, src_tbl, self.where_text)
                total_source += cnt
                self.log.emit(f"[진행] 전체 조회 {cnt}건 진행 예정 (소스: {src_tbl})")

                inserted_for_table = 0
                for event in utils.run_migration_stream(
                    src_engine, dst_engine,
                    src_schema=self.src_schema, src_table=src_tbl,
                    dst_schema=self.dst_schema, dst_table=dst_tbl,
                    where_text=self.where_text, chunk_size=self.chunk_size,
                ):
                    et = event.get("type")
                    if et == "log":
                        self.log.emit(event["message"])
                    elif et == "progress":
                        inserted_for_table += event["inserted_delta"]
                        total_inserted += event["inserted_delta"]
                        self.progress.emit(total_inserted, total_source)
                    elif et == "error":
                        self.error.emit(event.get("row_index", -1), event.get("error", ""))

                self.log.emit(f"[완료] {src_tbl} → {dst_tbl}: {inserted_for_table}/{cnt}건")
            self.done.emit(total_inserted, total_source)
        except Exception as e:
            self.log.emit(f"[오류] 워커 실행 실패: {e}")
            self.done.emit(0, 0)

class DataShuttleApp(QWidget):
    def __init__(self):
        super().__init__()
        ui_setup.init_ui(self)
        if not hasattr(self, "settings"):
            self.settings = {
                "connection_1": {"db_type":"Oracle","protocol":"TCP","host":"127.0.0.1","port":1521,"service_or_db":"","user":"","password":""},
                "connection_2": {"db_type":"PostgreSQL","protocol":"TCP","host":"127.0.0.1","port":5432,"service_or_db":"","user":"","password":""},
            }
        self._worker = None

    # ─────────────────────────────────
    def log_to_console(self, message: str) -> None:
        ui_setup.log_to_console(self, message)
    
    def _append_result(self, step: str, detail: str) -> None:
        table = self.result_table
        if table.columnCount() == 0:
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Step", "Detail"])
        r = table.rowCount()
        table.insertRow(r)
        table.setItem(r, 0, QTableWidgetItem(step))
        table.setItem(r, 1, QTableWidgetItem(detail))
        table.scrollToBottom()
    # ─────────────────────────────────

    # ─────────────────────────────────
    def reset_ui(self) -> None:
        """상단 '↺ 초기화'"""
        try:
            self.schema_input.clear()
            self.table_input.clear()
            self.where_input.clear()
            self.result_table.clear()
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            self.console_output.clear()
            if hasattr(self, "dest_schema_input"): self.dest_schema_input.clear()
            if hasattr(self, "dest_table_input"):  self.dest_table_input.clear()
            self.log_to_console("[초기화] 입력값과 결과를 초기화했습니다.")
        except Exception as e:
            self.log_to_console(f"초기화 오류: {str(e)}")

    def open_settings(self) -> None:
        try:
            dlg = SettingsDialog(parent=self, settings=self.settings)
            if dlg.exec_():
                self.settings = dlg.values()
                self.log_to_console("[설정] 연결 정보가 업데이트되었습니다.")
            else:
                self.log_to_console("[설정] 변경 없이 닫았습니다.")
        except Exception as e:
            self.log_to_console(f"설정 열기 오류: {str(e)}")

    def start_migration(self) -> None:
        try:
            src_schema = self.schema_input.text().strip()
            src_tables = self.table_input.text().strip()
            where  = self.where_input.toPlainText().strip() if hasattr(self.where_input, 'toPlainText') else self.where_input.text().strip()

            if not src_schema or not src_tables:
                self.log_to_console("Origin의 Schema와 Table은 필수입니다.")
                return

            # 목적지: 비어 있으면 Origin과 동일하게 대체
            dst_schema = self.dest_schema_input.text().strip() if hasattr(self, "dest_schema_input") else ""
            dst_table  = self.dest_table_input.text().strip()  if hasattr(self, "dest_table_input")  else ""
            if not dst_schema:
                dst_schema = src_schema
            # 테이블은 콤마 다중 입력을 고려 → 빈 경우 각 소스 테이블명으로 매핑
            # (Worker에서 비어있으면 소스 테이블 동일명으로 처리)
            dst_tables = dst_table  # 그대로 전달 (워커에서 매핑)

            self.log_to_console(
                f"[실행] Origin=({src_schema}, {src_tables}), "
                f"Destination=({dst_schema}, {dst_tables or '(동일명)'}), WHERE={where or '(없음)'}"
            )
            self._append_result("실행", "Connection 1 → Connection 2 마이그레이션을 시작합니다…")

            self._worker = MigrationWorker(
                self.settings, src_schema, src_tables, where,
                dst_schema=dst_schema, dst_tables=dst_tables, chunk_size=10_000
            )
            self._worker.log.connect(self.log_to_console)
            self._worker.progress.connect(self._on_progress)
            self._worker.error.connect(self._on_error)
            self._worker.done.connect(self._on_done)
            self._worker.start()
        except Exception as e:
            self.log_to_console(f"마이그레이션 오류: {str(e)}")
    # ─────────────────────────────────

    # ─────────────────────────────────
    def _on_progress(self, inserted: int, total: int):
        self._append_result("진행", f"누적 {inserted}/{total}건 마이그레이션 성공")

    def _on_error(self, row_index: int, err: str):
        idx_text = f"row {row_index}" if row_index >= 0 else "row ?"
        self._append_result("에러", f"{idx_text}: {err}")

    def _on_done(self, inserted_total: int, source_total: int):
        self._append_result("완료", f"총 {source_total}건 중 {inserted_total}건 마이그레이션 완료")
        self.log_to_console("[완료] 마이그레이션이 종료되었습니다.")
    # ─────────────────────────────────
