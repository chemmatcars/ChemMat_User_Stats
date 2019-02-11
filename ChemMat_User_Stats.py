from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QMainWindow
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtTest import QTest
import sys

class ChemMatUserStats(QMainWindow):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi('UI_Forms/mainWindow.ui', self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = ChemMatUserStats()
    w.setWindowTitle('ChemMat User Stats')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())