from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QMainWindow, QFileDialog, QDialog, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont
from PyQt5.QtTest import QTest
import pyqtgraph
import sys
import pandas as pd
from pandas import Timestamp
import os
import copy
import time

class FilterRangeDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        loadUi('UI_Forms/filterRangeDialog.ui', self)

class FilterListDialog(QDialog):
    def __init__(self, parent=None,items=None,selectedItems=None):
        QDialog.__init__(self, parent)
        loadUi('UI_Forms/filterListDialog.ui', self)
        self.itemListWidget.addItems(items)
        if selectedItems is not None:
            for txt in selectedItems:
                item=self.itemListWidget.findItems(txt,Qt.MatchExactly)
                item[0].setSelected(True)


class ChemMatUserStats(QMainWindow):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        loadUi('UI_Forms/mainWindow.ui', self)

        font=QFont('Monospace')
        font.setStyleHint(QFont.TypeWriter)
        font.setPointSize(8)
        #self.resultTextEdit.setCurrentFont(font)
        self.resultTextBrowser.setCurrentFont(font)
        #self.resultTextEdit.append('Mrinal is good')


        self.initSignals()
        self.filterDict={}
        self.filterRangeItems=['Posted Date','Badge No','Experiment Id']
        self.userInstitute = pd.read_excel('./Data/institution_data.xlsx')
        self.countryState = self.userInstitute.set_index('Institution').to_dict()

        self.enableButtons(enable=False)

    def enableButtons(self,enable=True):
        #Disabling some of the buttons to start with
        self.addFilterPushButton.setEnabled(enable)
        self.saveFilterPushButton.setEnabled(enable)
        self.loadFilterPushButton.setEnabled(enable)
        self.duplicatePushButton.setEnabled(enable)
        self.blsPushButton.setEnabled(enable)
        self.upPushButton.setEnabled(enable)
        self.downPushButton.setEnabled(enable)
        self.removePushButton.setEnabled(enable)
        self.calPushButton.setEnabled(enable)
        self.exportStatPushButton.setEnabled(enable)
        self.exportDataPushButton.setEnabled(enable)
        self.plotStatPushButton.setEnabled(enable)




    def initSignals(self):
        self.loadPushButton.clicked.connect(self.loadFile)
        self.addFilterPushButton.clicked.connect(self.addFilter)
        self.removePushButton.clicked.connect(self.removeFilterItem)
        self.duplicatePushButton.clicked.connect(lambda x: self.removeDuplicates(selectedItems=None))
        self.blsPushButton.clicked.connect(self.removeBLS)
        self.calPushButton.clicked.connect(self.calStat)
        self.exportStatPushButton.clicked.connect(self.saveStat)
        self.exportDataPushButton.clicked.connect(self.saveFilterData)
        self.saveFilterPushButton.clicked.connect(self.saveFilter)
        self.loadFilterPushButton.clicked.connect(self.loadFilter)
        self.upPushButton.clicked.connect(self.moveFilterUp)
        self.downPushButton.clicked.connect(self.moveFilterDown)
        self.plotStatPushButton.clicked.connect(self.plotStat)
        self.filterListWidget.itemDoubleClicked.connect(self.editFilter)

    def readBLScientist(self):
        self.blSciData=pd.read_excel('./Data/BLscientist.xlsx')

    def moveFilterUp(self):
        QMessageBox.information(self,"Information","This function is not implemented yet",QMessageBox.Ok)

    def moveFilterDown(self):
        QMessageBox.information(self, "Information", "This function is not implemented yet", QMessageBox.Ok)

    def loadFile(self):
        self.filterListWidget.clear()
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
            #self.rawDataTableWidget.setData(self.rawData.transpose().to_dict())
            self.filteredDataTableWidget.setData(self.rawData.transpose().to_dict())
            self.filterComboBox.clear()
            self.filterComboBox.addItems(list(self.rawData.columns.values))
            self.rowColumnLabel.setText('Rows:%d; Columns:%d' % self.rawData.shape)
            self.calComboBox.clear()
            self.calComboBox.addItems(list(self.rawData.columns.values))
            self.calComboBox.addItem('Unique Users')
            self.calComboBox.addItem('US User Map')
            self.calComboBox.addItem('World User Map')
            self.enableButtons(enable=True)
            self.exportStatPushButton.setEnabled(False)
            self.plotStatPushButton.setEnabled(False)


    def addFilter(self):
        self.filterText=self.filterComboBox.currentText()
        if self.filterText in self.filterRangeItems:
            self.addFilterRange()
        else:
            self.addFilterList()

    def addFilterRange(self,fromtxt=None,totxt=None):
        dialog=FilterRangeDialog(parent=self)
        if fromtxt is None:
            frommin=str(min(self.rawData[self.filterText]))
        else:
            frommin=fromtxt
        if totxt is None:
            tomax=str(max(self.rawData[self.filterText]))
        else:
            tomax=totxt
        dialog.fromLineEdit.setText(str(frommin))
        dialog.toLineEdit.setText(str(tomax))
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
                if fromtxt is None and totxt is None:
                    self.filterListWidget.addItem(self.filterText + '::' + str(self.filterDict[self.filterText]))
                    #print(self.filterDict)
                    self.processFilter()
        else:
            pass

    def addFilterList(self,selectedItems=None):
        dialog = FilterListDialog(parent=self,items=list(self.rawData[self.filterText].unique()),selectedItems=selectedItems)
        if dialog.exec_():
            self.filterList=[item.text() for item in dialog.itemListWidget.selectedItems()]
            #print(self.filterList)
            self.filterDict[self.filterText]=self.filterList
            if selectedItems is None:
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

    def removeDuplicates(self,selectedItems=None):
        dialog = FilterListDialog(parent=self, items=list(self.rawData.columns.values),selectedItems=selectedItems)
        dialog.label.setText('Select the category for removing duplicates:')
        if dialog.exec_():
            self.duplicateList = [item.text() for item in dialog.itemListWidget.selectedItems()]
           # print(self.duplicateList)
            if selectedItems is None:
                self.filterListWidget.addItem('Remove Duplicates' + '::' + str(self.duplicateList))
                self.processFilter()


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
        elif self.calComboBox.currentText()=="Unique Users":
            self.calcUniqueUsers()
            self.showStat()
        else:
            self.results=self.filterData[self.calComboBox.currentText()].value_counts().to_dict()
            self.resultsNorm=self.filterData[self.calComboBox.currentText()].value_counts(normalize=True).to_dict()
            self.showStat()


    def showStat(self):
        #self.resultTextEdit.clear()
        self.resultTextBrowser.clear()
        maxlen=max([len(key) for key in self.results.keys()])
        for key in self.results.keys():
            try:
                #self.resultTextEdit.append('{:<{width}} {:10d} ({:5.3f}%)'.format(key,self.results[key],self.resultsNorm[key]*100,width=maxlen))
                self.resultTextBrowser.append(
                    '{:<{width}} {:10d} ({:5.3f}%)'.format(key, self.results[key], self.resultsNorm[key] * 100,
                                                           width=maxlen))
            except:
                #self.resultTextEdit.append('{:<{width}} {:10d}'.format(key, self.results[key],width=maxlen))
                self.resultTextBrowser.append('{:<{width}} {:10d}'.format(key, self.results[key], width=maxlen))
        self.exportStatPushButton.setEnabled(True)
        self.plotStatPushButton.setEnabled(True)

    def saveStat(self):
        filename=QFileDialog.getSaveFileName(self,"Save as Excel file",filter='Excel Files (*.xlsx)')[0]
        if filename!='':
            if os.path.splitext(filename)[1] == '':
                filename = filename + '.xlsx'
            #self.filterData[self.calComboBox.currentText()].value_counts().to_excel(filename)
            data=pd.DataFrame.from_dict(self.results,orient='index').reset_index()
            data.columns = ['Categories', self.calComboBox.currentText()]
            data.to_excel(filename,index=False)

    def plotStat(self):
        QMessageBox.information(self, "Information", "This function is not implemented yet", QMessageBox.Ok)

    def saveFilterData(self):
        filename = QFileDialog.getSaveFileName(self,"Save as Excel file",filter='Excel Files (*.xlsx)')[0]
        if filename != '':
            if os.path.splitext(filename)[1] == '':
                filename = filename + '.xlsx'
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

    def saveFilter(self):
        if self.filterListWidget.count()!=0:
            filename=QFileDialog.getSaveFileName(self,'Save Filter as',filter='Filter file (*.fil)')[0]
            if os.path.splitext(filename)[1]=='':
                filename=filename+'.fil'
            if filename!='':
                fh=open(filename,'w')
                fh.write('# Filter file created on '+time.asctime()+'\n')
                for i in range(self.filterListWidget.count()):
                    fh.write(self.filterListWidget.item(i).text()+'\n')
        else:
            QMessageBox.warning(self,'Filter Error','No filter to save. Please add some filters before saving.',QMessageBox.Ok)

    def loadFilter(self):
        filename=QFileDialog.getOpenFileName(self,'Select Filter file',filter='Filter file (*.fil)')[0]
        if filename!='':
            fh=open(filename,'r')
            lines=fh.readlines()
            for line in lines:
                if line[0]!='#':
                    self.filterListWidget.addItem(line[:-1])
                    filterKey,filterVal=line[:-1].split('::')
                    filterVal=eval(filterVal)
                    if filterKey=='Remove Duplicates':
                        self.duplicateList=filterVal
            self.processFilter()

    def editFilter(self,item):
        filterKey,filterVal=item.text().split('::')
        filterVal=eval(filterVal)
        self.filterText = filterKey
        if filterKey=='Remove Duplicates':
            self.removeDuplicates(selectedItems=filterVal)
            item.setText('Remove Duplicates' + '::' + str(self.duplicateList))
        elif filterKey in self.filterRangeItems:
            self.addFilterRange(fromtxt=filterVal[0],totxt=filterVal[1])
            item.setText(self.filterText + '::' + str(self.filterDict[self.filterText]))
        elif filterKey=='Remove BL Scientists':
            QMessageBox.warning(self,"Restricted Filter","This filter cannot be edited. Please change the BLscientist.xlsx file to edit/add/remove the information about the beamline scientists.",QMessageBox.Ok)
            return
        else:
            self.addFilterList(selectedItems=filterVal)
            item.setText(self.filterText + '::' + str(self.filterDict[self.filterText]))
        self.processFilter()

    def calcUniqueUsers(self):
        #frequency=QInputDialog.getInt(self,"Input Frequency","Frequency of years at which you like to calculate Unique Users",value=1)[0]
        data_raw_sort = self.filterData.sort_values('Posted Date')
        startDate = min(data_raw_sort['Posted Date'])
        endDate=max(data_raw_sort['Posted Date'])
        data_raw_sort = data_raw_sort.set_index(['Posted Date'])
        dates = pd.date_range(start=startDate,end=endDate, freq='AS')
        self.results = {}
        for i, date in enumerate(dates[:-1]):
            self.results[str(date.year)]=data_raw_sort.loc[date:dates[i + 1]].drop_duplicates(('Badge No','Institution')).count()['Badge No']






if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = ChemMatUserStats()
    w.setWindowTitle('ChemMat User Stats')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())