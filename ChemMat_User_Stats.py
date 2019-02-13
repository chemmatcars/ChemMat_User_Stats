from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QMainWindow, QFileDialog, QDialog, QInputDialog
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtTest import QTest
import pyqtgraph
import sys
import pandas as pd
from pandas import Timestamp
import os
import copy

class FilterRangeDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        loadUi('UI_Forms/filterRangeDialog.ui', self)

class FilterListDialog(QDialog):
    def __init__(self, parent=None,items=None):
        QDialog.__init__(self, parent)
        loadUi('UI_Forms/filterListDialog.ui', self)
        self.itemListWidget.addItems(items)

class ChemMatUserStats(QMainWindow):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi('UI_Forms/mainWindow.ui', self)

        self.initSignals()
        self.filterDict={}
        self.filterRangeItems=['Posted Date','Badge No','Experiment Id']
        self.userInstitute = pd.read_excel('./Data/institution_data.xlsx')
        self.countryState = self.userInstitute.set_index('Institution').to_dict()


    def initSignals(self):
        self.loadPushButton.clicked.connect(self.loadFile)
        self.addFilterPushButton.clicked.connect(self.addFilter)
        self.removePushButton.clicked.connect(self.removeFilterItem)
        self.duplicatePushButton.clicked.connect(self.removeDuplicates)
        self.blsPushButton.clicked.connect(self.removeBLS)
        self.calPushButton.clicked.connect(self.calStat)
        self.exportStatPushButton.clicked.connect(self.saveStat)
        self.exportDataPushButton.clicked.connect(self.saveFilterData)

    def readBLScientist(self):
        self.blSciData=pd.read_excel('./Data/BLscientist.xlsx')


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
            self.filterData=copy.copy(self.rawData)
            self.rawDataTableWidget.setData(self.rawData.transpose().to_dict())
            self.filteredDataTableWidget.setData(self.rawData.transpose().to_dict())
            self.filterComboBox.clear()
            self.filterComboBox.addItems(list(self.rawData.columns.values))
            self.rowColumnLabel.setText('Rows:%d; Columns:%d' % self.rawData.shape)
            self.calComboBox.clear()
            self.calComboBox.addItems(list(self.rawData.columns.values))
            self.calComboBox.addItem('Yearly Unique Users')
            self.calComboBox.addItem('US User Map')
            self.calComboBox.addItem('World User Map')

    def addFilter(self):
        self.filterText=self.filterComboBox.currentText()
        if self.filterText in self.filterRangeItems:
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
            if self.filterText=='Posted Date':
                self.fromValue=pd.to_datetime(dialog.fromLineEdit.text())
                self.toValue=pd.to_datetime(dialog.toLineEdit.text())
            else:
                self.fromValue = int(dialog.fromLineEdit.text())
                self.toValue = int(dialog.toLineEdit.text())

            if self.fromValue > self.toValue:
                QMessageBox.warning(self,'Value Error','Starting value is more than finishing value, please reenter!', QMessageBox.Ok)
            else:
                self.filterDict[self.filterText]=[self.fromValue,self.toValue]
                self.filterListWidget.addItem(self.filterText + '::' + str(self.filterDict[self.filterText]))
                #print(self.filterDict)
                self.processFilter()
        else:
            pass

    def addFilterList(self):
        dialog = FilterListDialog(parent=self,items=list(self.rawData[self.filterText].unique()))
        if dialog.exec_():
            self.filterList=[item.text() for item in dialog.itemListWidget.selectedItems()]
            #print(self.filterList)
            self.filterDict[self.filterText]=self.filterList
            self.filterListWidget.addItem(self.filterText + '::' + str(self.filterDict[self.filterText]))
            self.processFilter()
        else:
            pass

    def processFilter(self):
        self.filterData=copy.copy(self.rawData)
        self.readBLScientist()
        for i in range(self.filterListWidget.count()):
            filterKey,filterVal=str(self.filterListWidget.item(i).text()).split('::')
           # print(filterKey,filterVal)
            filterVal=eval(filterVal)
           # print(filterVal)
            if filterKey=='Remove Duplicates':
                self.filterData=self.filterData.drop_duplicates(self.duplicateList)
            elif filterKey=='Remove BL Scientists':
                blBadgeList=self.blSciData['Badge No'].tolist()
                self.filterData=self.filterData[~((self.filterData['Badge No'].isin(blBadgeList)) & (self.filterData['Institution']=='The University of Chicago'))]
            elif filterKey in self.filterRangeItems:
                self.filterData=self.filterData[(self.filterData[filterKey] >= filterVal[0]) & (self.filterData[filterKey] <= filterVal[1])]
                #self.filteredDataTableWidget.clear()
                #print(self.filterData.rows.count())

            else:
                self.filterData = self.filterData[self.filterData[filterKey].isin(filterVal)]
        self.rowColumnLabel.setText('Rows:%d; Columns:%d' % self.filterData.shape)
        self.filteredDataTableWidget.setData(self.filterData.transpose().to_dict())


    def removeFilterItem(self):
        if self.filterListWidget.count()!=0:
            selectedRows=[self.filterListWidget.row(item) for item in self.filterListWidget.selectedItems()]
            #print(sorted(selectedRows, reverse=True))
            selectedRows=sorted(selectedRows, reverse=True)
            for row in selectedRows:
                self.filterListWidget.takeItem(row)
            self.processFilter()

    def removeDuplicates(self):
        dialog = FilterListDialog(parent=self, items=list(self.rawData.columns.values))
        dialog.label.setText('Select the catagory for removing duplicates:')
        if dialog.exec_():
            self.duplicateList = [item.text() for item in dialog.itemListWidget.selectedItems()]
           # print(self.duplicateList)
            self.filterListWidget.addItem('Remove Duplicates' + '::' + str(self.duplicateList))
            self.processFilter()
        else:
            pass

    def removeBLS(self):
        self.filterListWidget.addItem('Remove BL Scientists::True')
        self.processFilter()

    def calStat(self):
        if self.calComboBox.currentText()=='Yearly Unique Users':
            pass
        elif self.calComboBox.currentText()=='US User Map':
            self.stateData = self.filterData.drop_duplicates(('Badge No', 'Institution'))[['Institution']]
            self.stateData['Country'] = self.stateData['Institution'].apply(lambda x: self.countryState['Country'][x] if x in self.countryState['Country'] else self.updateCSD(x))
            stateData=self.stateData[self.stateData['Country']=='USA']
            stateData['State']=stateData['Institution'].apply(lambda x: self.countryState['State'][x] if x in self.countryState['State'] else self.updateCSD(x))
            self.results = stateData['State'].value_counts().to_dict()
            self.resultsNorm = stateData['State'].value_counts(normalize=True).to_dict()
            self.showStat()
        elif self.calComboBox.currentText()=='World User Map':
            self.worldData = self.filterData.drop_duplicates(('Badge No', 'Institution'))[['Institution']]
            self.worldData['Country'] = self.worldData['Institution'].apply(lambda x: self.countryState['Country'][x] if x in self.countryState['Country'] else self.updateCSD(x))
            self.results=self.worldData['Country'].value_counts().to_dict()
            self.resultsNorm=self.worldData['Country'].value_counts(normalize=True).to_dict()
            self.showStat()
        else:
            self.results=self.filterData[self.calComboBox.currentText()].value_counts().to_dict()
            self.resultsNorm=self.filterData[self.calComboBox.currentText()].value_counts(normalize=True).to_dict()
            self.showStat()

    def showStat(self):
        self.resultTextBrowser.clear()
        for key in self.results.keys():
            self.resultTextBrowser.append('%s\t %d\t (%f%%)'%(key,self.results[key],self.resultsNorm[key]*100))

    def saveStat(self):
        filename=QFileDialog.getSaveFileName()[0]+'.xlsx'
        if filename!='':
            self.filterData[self.calComboBox.currentText()].value_counts().to_excel(filename)

    def saveFilterData(self):
        filename = QFileDialog.getSaveFileName()[0] + '.xlsx'
        if filename != '':
            self.filterData.to_excel(filename,index=False)


    def updateCSD(self,institute):
        x = QInputDialog.getText(self,'Enter Country','Please provide the country for %s' % institute)[0]
        self.countryState['Country'][institute] = x
        if x == 'USA':
            y = QInputDialog.getText(self,'Enter US State','Please provide the state for %s (e.g IL for Illinois)' % institute)[0]
            self.countryState['State'][institute] = y
        else:
            y=''
        df=pd.DataFrame([[institute, x, y]], columns=['Institution', 'Country', 'State' ])
        self.userInstitute=self.userInstitute.append(df, ignore_index=True)
        self.userInstitute.to_excel('./Data/institution_data.xlsx',index=False)
        return x

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = ChemMatUserStats()
    w.setWindowTitle('ChemMat User Stats')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())