from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QDesktopWidget
from MainWindow import Ui_MainWindow
from ModParser import parse


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.parseButton.clicked.connect(self.parse_music)
        self.soundlevelSpinBox.setMaximum(7)
        self.soundlevelSpinBox.setMinimum(1)
        self._to_center()

    def parse_music(self):
        url = self.urlLineEdit.text()
        level = self.soundlevelSpinBox.value()
        self.outputBrowser.setText(parse(url, level)[0])

    def _to_center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.width()) // 2
        )


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
