import sys
import os

# 현재 디렉터리를 Python 모듈 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from data_shuttle.gui import DataShuttleApp


def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("favicon.ico"))

    window = DataShuttleApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
