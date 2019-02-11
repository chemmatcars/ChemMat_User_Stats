from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QMainWindow, QFileDialog, QDialog
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtTest import QTest
import pyqtgraph
import sys
import pandas as pd
import os

class FilterRangeDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        loadUi('UI_Forms/filterRangeDialog.ui', self)

class ChemMatUserStats(QMainWindow):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi('UI_Forms/mainWindow.ui', self)

        self.initSignals()


    def initSignals(self):
        self.loadPushButton.clicked.connect(self.loadFile)
        self.addFilterPushButton.clicked.connect(self.addFilter)

    def loadFile(self):
        self.fileName=QFileDialog.getOpenFileName(self,"Select data file",filter="Data files (*.xlsx *.csv)")[0]
        if self.fileName!='':
            self.fileLabel.setText(self.fileName)
            extn=os.path.splitext(self.fileName)[1]
            if extn=='.xlsx':
                self.rawData=pd.read_excel(self.fileName)
            elif extn=='.csv':
                self.rawData=pd.read_csv(self.fileName)
            self.rawData.dropna(axis=1,how='all')
            self.rawData['Posted Date'] = pd.to_datetime(self.rawData['Posted Date'])
            self.rawDataTableWidget.setData(self.rawData.transpose().to_dict())
            self.filteredDataTableWidget.setData(self.rawData.transpose().to_dict())
            self.filterComboBox.clear()
            self.filterComboBox.addItems(list(self.rawData.columns.values))

    def addFilter(self):
        self.filterText=self.filterComboBox.currentText()
        if self.filterText in ['Posted Date','Badge No','Experiment Id']:
            self.addFilterRange()
        else:
            self.addFilterList()

    def addFilterRange(self):
        dialog=FilterRangeDialog(parent=self)
        frommin=str(min(self.rawData[self.filterText]))
        tomax=str(max(self.rawData[self.filterText]))
        dialog.fromLineEdit.setText(frommin)
        dialog.toLineEdit.setText(tomax)
        if dialog.exec_():
            print('I m here 1')
            print(dialog.fromLineEdit.text(),dialog.toLineEdit.text())
        else:
            pass






if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = ChemMatUserStats()
    w.setWindowTitle('ChemMat User Stats')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())