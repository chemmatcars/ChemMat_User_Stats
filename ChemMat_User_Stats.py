from PyQt5.uic import loadUi 
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox, QMainWindow, QFileDialog, QDialog, QInputDialog, QProgressDialog, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator, QFont,QCursor
from PyQt5.QtTest import QTest
import pyqtgraph
import sys
import pandas as pd
from pandas import Timestamp
import os
import copy
import time
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
import shapely
from matplotlib.colors import hsv_to_rgb
from matplotlib import ticker
import numpy as np
import re


class PlotDialog(QDialog):
    def __init__(self,parent):
        QDialog.__init__(self,parent)
        loadUi('UI_Forms/mplPlot.ui',self)


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
        self.filterRangeItems=['Posted Date','Badge','Experiment Id']
        self.userInstitute = pd.read_excel('./Data/institution_data.xlsx')
        self.countryState = self.userInstitute.set_index('Inst Name').to_dict()
        self.CountryNames=pd.read_excel('./Data/Countries.xlsx').set_index('DB_Name').to_dict()
        self.msiList=pd.read_excel('./Data/MSI-master-list.xls',skiprows=1)

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
        skiprows,done=QInputDialog.getInt(self,'Input Dialog','No. of rows to skip')
        if not done:
            return
        self.fileName=QFileDialog.getOpenFileName(self,"Select data file",filter="Data files (*.xlsx *.csv)")[0]
        if self.fileName!='':
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.fileLabel.setText(self.fileName)
            extn=os.path.splitext(self.fileName)[1]
            if extn=='.xlsx':
                self.rawData=pd.read_excel(self.fileName,skiprows=skiprows)
            elif extn=='.csv':
                self.rawData=pd.read_csv(self.fileName,skiprows=skiprows)
            self.rawData.dropna(axis=1,how='all')
            self.rawData['Posted Date'] = pd.to_datetime(self.rawData['Posted Date'])
            self.rawData['MSI']=np.where(self.rawData['Inst Name'].isin(self.msiList['Name']),'True','False')
            Nrows,NCols=self.rawData.shape
            progress_dlg=QProgressDialog("Reading file","Stop",0,Nrows,self)
            progress_dlg.setWindowTitle('Loading file')
            progress_dlg.setMinimumDuration(0)
            progress_dlg.setWindowModality(Qt.WindowModal)
            progress_dlg.setValue(0)
            progress_dlg.show()
            for i in range(Nrows):
                try:
                    funding_sources=re.split(',\s*(?![^()]*\))',self.rawData['Funding Source'][i])
                    research_sub = re.split(',\s*(?![^()]*\))', self.rawData['Research Subject'][i])
                    if len(funding_sources)>1 or len(research_sub)>1:
                        line=self.rawData.iloc[i]
                        self.rawData.loc[i,'Funding Source']=funding_sources[0]
                        self.rawData.loc[i,'Research Subject']=research_sub[0]
                        for source in funding_sources:
                            for sub in research_sub[1:]:
                                line.loc['Funding Source']=source
                                line.loc['Research Subject']=sub
                                self.rawData=self.rawData.append(line,ignore_index=True)
                        for source in funding_sources[1:]:
                            line.loc['Funding Source'] = source
                            line.loc['Research Subject'] = research_sub[0]
                            self.rawData = self.rawData.append(line, ignore_index=True)
                    progress_dlg.setValue(i)
                    QApplication.processEvents()
                    if progress_dlg.wasCanceled():
                        break
                except:
                    QMessageBox.warning(self,'Line error','There is a problem at line %d'%i,QMessageBox.Ok)

            Nrows, NCols = self.rawData.shape
            self.filterData=copy.copy(self.rawData)
            self.filteredDataTableWidget.setData(self.rawData.transpose().to_dict())
            self.filterComboBox.clear()
            self.filterComboBox.addItems(list(self.rawData.columns.values))
            #self.filterComboBox.addItem('MSI')
            self.rowColumnLabel.setText('Rows:%d; Columns:%d' % self.rawData.shape)
            self.calComboBox.clear()
            self.calComboBox.addItems(list(self.rawData.columns.values))
            self.calComboBox.addItem('Yearly Unique Users')
            self.calComboBox.addItem('Yearly Unique Institutions')
            self.calComboBox.addItem('US User Map')
            self.calComboBox.addItem('World User Map')
            self.enableButtons(enable=True)
            self.exportStatPushButton.setEnabled(False)
            self.plotStatPushButton.setEnabled(False)
            progress_dlg.close()
            QApplication.restoreOverrideCursor()


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
                    self.processFilter()
        else:
            pass

    def addFilterList(self,selectedItems=None):
        items=list(self.rawData[self.filterText].unique())
        items=[str(item) for item in items]
        dialog = FilterListDialog(parent=self,items=items,selectedItems=selectedItems)
        if dialog.exec_():
            self.filterList=[item.text() for item in dialog.itemListWidget.selectedItems()]
            #print(self.filterList)
            self.filterDict[self.filterText]=self.filterList
            if selectedItems is None:
                self.filterListWidget.addItem(self.filterText + '::' + str(self.filterDict[self.filterText]))
                self.processFilter()

    def processFilter(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.filterData=copy.copy(self.rawData)
        self.readBLScientist()
        for i in range(self.filterListWidget.count()):
            filterKey,filterVal=str(self.filterListWidget.item(i).text()).split('::')
           # print(filterKey,filterVal)
            filterVal=eval(filterVal)
           # print(filterVal)
            if filterKey=='Remove Duplicates':
                print(self.duplicateList)
                self.filterData=self.filterData.drop_duplicates(self.duplicateList)
            elif filterKey=='Remove BL Scientists':
                blBadgeList=self.blSciData['Badge'].tolist()
                self.filterData=self.filterData[~((self.filterData['Badge'].isin(blBadgeList)) & (self.filterData['Inst Name']=='The University of Chicago'))]
            elif filterKey in self.filterRangeItems:
                self.filterData=self.filterData[(self.filterData[filterKey] >= filterVal[0]) & (self.filterData[filterKey] <= filterVal[1])]
                #self.filteredDataTableWidget.clear()
                #print(self.filterData.rows.count())
            else:
                self.filterData = self.filterData[self.filterData[filterKey].isin(filterVal)]
        self.rowColumnLabel.setText('Rows:%d; Columns:%d' % self.filterData.shape)
        self.filteredDataTableWidget.setData(self.filterData.transpose().to_dict())
        QApplication.restoreOverrideCursor()


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
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if self.calComboBox.currentText()=='Unique Users':
            pass
        elif self.calComboBox.currentText()=='US User Map':
            self.stateData = self.filterData.drop_duplicates(('Badge', 'Inst Name'))[['Inst Name']]
            self.stateData['Country'] = self.stateData['Inst Name'].apply(lambda x: self.countryState['Country'][x] if x in self.countryState['Country'] else self.updateCSD(x))
            stateData=self.stateData[self.stateData['Country']=='USA']
            y=stateData['Inst Name']
            stateData['State']=y.apply(lambda x: self.countryState['State'][x] if x in self.countryState['State'] else self.updateCSD(x))
            self.results = stateData['State'].value_counts().to_dict()
            self.resultsNorm = stateData['State'].value_counts(normalize=True).to_dict()
            self.showStat()
        elif self.calComboBox.currentText()=='World User Map':
            self.worldData = self.filterData.drop_duplicates(('Badge', 'Inst Name'))[['Inst Name']]
            self.worldData['Country'] = self.worldData['Inst Name'].apply(lambda x: self.countryState['Country'][x] if x in self.countryState['Country'] else self.updateCSD(x))
            self.results=self.worldData['Country'].value_counts().to_dict()
            self.resultsNorm=self.worldData['Country'].value_counts(normalize=True).to_dict()
            self.showStat()
        elif self.calComboBox.currentText()=="Yearly Unique Users":
            self.calcUniqueUsers()
            self.showStat()
        elif self.calComboBox.currentText()=="Yearly Unique Institutions":
            self.calcUniqueInstitutions()
            self.showStat()
        else:
            self.results=self.filterData[self.calComboBox.currentText()].value_counts().to_dict()
            self.resultsNorm=self.filterData[self.calComboBox.currentText()].value_counts(normalize=True).to_dict()
            self.showStat()
        QApplication.restoreOverrideCursor()


    def showStat(self):
        #self.resultTextEdit.clear()
        self.resultTextBrowser.clear()
        maxlen=max([len(str(key)) for key in self.results.keys()])
        for key in self.results.keys():
            try:
                #self.resultTextEdit.append('{:<{width}} {:10d} ({:5.3f}%)'.format(key,self.results[key],self.resultsNorm[key]*100,width=maxlen))
                self.resultTextBrowser.append(
                    '{:<{width}} {:>10d} ({:>5.3f}%)'.format(key, self.results[key], self.resultsNorm[key] * 100,
                                                           width=maxlen))
            except:
                #self.resultTextEdit.append('{:<{width}} {:10d}'.format(key, self.results[key],width=maxlen))
                self.resultTextBrowser.append('{:<{width}} {:10d}'.format(key, self.results[key], width=maxlen))
        self.resultTextBrowser.append('----------------------\n')
        self.resultTextBrowser.append('{:<{width}} {:10d}'.format('Total', np.sum(list(self.results.values())), width=maxlen))
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
            try:
                data.to_excel(filename,index=False)
            except:
                QMessageBox.warning(self,"File error","Please check the file is either open in MS Excel or used by some other programs. Try again after closing the file or the program using the file.",QMessageBox.Ok)

    def plotStat(self):
        data = pd.DataFrame.from_dict(self.results, orient='index', columns=[self.calComboBox.currentText()])
        if self.calComboBox.currentText()=='US User Map':
            self.create_us_map(data,usersCol=self.calComboBox.currentText())
        elif self.calComboBox.currentText()=='World User Map':
            self.create_world_map(data,usersCol=self.calComboBox.currentText())
        else:
            QMessageBox.information(self, "Information", "This function is not implemented yet", QMessageBox.Ok)

    def saveFilterData(self):
        filename = QFileDialog.getSaveFileName(self,"Save as Excel file",filter='Excel Files (*.xlsx)')[0]
        if filename != '':
            if os.path.splitext(filename)[1] == '':
                filename = filename + '.xlsx'
            try:
                self.filterData.to_excel(filename,index=False)
            except:
                QMessageBox.warning(self,"File error","Please check the file is either open in MS Excel or used by some other programs. Try again after closing the file or the program using the file.",QMessageBox.Ok)


    def updateCSD(self,institute):
        x = QInputDialog.getText(self,'Enter Country','Please provide the country for %s' % institute)[0]
        self.countryState['Country'][institute] = x
        if x == 'USA':
            y = QInputDialog.getText(self,'Enter US State','Please provide the state for %s (e.g IL for Illinois)' % institute)[0]
            self.countryState['State'][institute] = y
        else:
            y=''
        df=pd.DataFrame([[institute, x, y]], columns=['Inst Name', 'Country', 'State' ])
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
            self.filterListWidget.clear()
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
        """
        Calculate the frenquency of Unique Users per year
        :return:
        """
        #frequency=QInputDialog.getInt(self,"Input Frequency","Frequency of years at which you like to calculate Unique Users",value=1)[0]
        data_raw_sort = self.filterData.sort_values('Posted Date')
        startDate = '1/1/'+str(min(data_raw_sort['Posted Date']).date().year)
        endDate='1/1/'+str(max(data_raw_sort['Posted Date']).date().year+1)

        data_raw_sort = data_raw_sort.set_index(['Posted Date'])
        dates = pd.date_range(start=startDate,end=endDate, freq='AS')
        self.results = {}
        for i, date in enumerate(dates[:-1]):
            self.results[str(date.year)]=data_raw_sort.loc[date:dates[i + 1]].drop_duplicates(('Badge','Inst Name')).count()['Badge']

    def calcUniqueInstitutions(self):
        """
        Calculate the frenquency of Unique Insitutions per year
        :return:
        """
        #frequency=QInputDialog.getInt(self,"Input Frequency","Frequency of years at which you like to calculate Unique Users",value=1)[0]
        data_raw_sort = self.filterData.sort_values('Posted Date')
        startDate = '1/1/'+str(min(data_raw_sort['Posted Date']).date().year)
        endDate='1/1/'+str(max(data_raw_sort['Posted Date']).date().year+1)

        data_raw_sort = data_raw_sort.set_index(['Posted Date'])
        dates = pd.date_range(start=startDate,end=endDate, freq='AS')
        self.results = {}
        for i, date in enumerate(dates[:-1]):
            self.results[str(date.year)]=data_raw_sort.loc[date:dates[i + 1]].drop_duplicates(('Inst Name')).count()['Inst Name']


    def create_us_map(self,data,usersCol='users',mapType='Accent',textSize=8):
        self.mapPlotDlg = PlotDialog(self)
        self.maxu=max(data[usersCol])
        self.minu=0

        self.statesInfo = {
            'New Jersey':  ['NJ',[-74.48,40.16],[-72.36,39.46]],
            'Rhode Island':   ['RI',[-71.55,41.67],[-67.5,39.44]],
            'Massachusetts':   ['MA',[-71.9,42.4],[-67.9,42.4]],
            'Connecticut':    ['CT',[-72.7,41.9],[-69.7,38.9]],
            'Maryland':   ['MD',[-76.1,38.7],[-73.1,35.2]],
            'New York':    ['NY',[-75.3,42.9]],
            'Delaware':    ['DE',[-75.45,38.79],[-72.45,37.79]],
            'Florida':     ['FL',[-82.1,27.5]],
            'Ohio':  ['OH',[-83.2,40.1]],
            'Pennsylvania':  ['PA',[-78.6,40.7]],
            'Illinois':    ['IL',[-89.6,39.8]],
            'California':  ['CA',[-121.6,37.36]],
            'Virginia':    ['VA',[-79.3,37.4]],
            'Michigan':    ['MI',[-85.6,42.8]],
            'Indiana':    ['IN',[-86.9,39.3]],
            'North Carolina':  ['NC',[-78.8,35.1]],
            'Georgia':     ['GA',[-84,32.2]],
            'Tennessee':   ['TN',[-87.8,35.5]],
            'New Hampshire':   ['NH',[-71.5,43.5],[-72.2,48.5]],
            'South Carolina':  ['SC',[-81.2,33.6]],
            'Louisiana':   ['LA',[-93,30.4]],
            'Kentucky':   ['KY',[-85.5,37.3]],
            'Wisconsin':  ['WI',[-90.3,43.5]],
            'Washington':  ['WA',[-121.3,47.45]],
            'Alabama':     ['AL',[-87.7,32.4]],
            'Missouri':    ['MO',[-93.4,38.1]],
            'Texas':   ['TX',[-99.79,31.59]],
            'West Virginia':   ['WV',[-81.5,38.2]],
            'Vermont':     ['VT',[-72.1,44.1],[-76.1,47.1]],
            'Minnesota':  ['MN',[-95.3,45.63]],
            'Mississippi':   ['MS',[-90.3,32.2]],
            'Iowa':  ['IA',[-94.43,41.3]],
            'Arkansas':    ['AR',[-93.4,34.1]],
            'Oklahoma':    ['OK',[-98.26,35.24]],
            'Arizona':     ['AZ',[-112.7,33.93]],
            'Colorado':    ['CO',[-106.8,38.63]],
            'Maine':  ['ME',[-69.7,44.9]],
            'Oregon':  ['OR',[-122,43.6]],
            'Kansas':  ['KS',[-99.57,38.3]],
            'Utah':  ['UT',[-112.6,39.18]],
            'Nebraska':    ['NE',[-100.9,41.26]],
            'Nevada':  ['NV',[-117.3,39.24]],
            'Idaho':   ['ID',[-115.8,43.51]],
            'New Mexico':  ['NM',[-107.2,33.15]],
            'South Dakota':  ['SD',[-101.5,44.21]],
            'North Dakota':  ['ND',[-101.5,47.16]],
            'Montana':     ['MT',[-111.4,46.57]],
            'Wyoming':      ['WY',[-108.8,42.79]],
            'Hawaii': ['HI',[-107.4,25.02]],
            'Alaska': ['AK',[-117,27.57]]}

        shapename = 'admin_1_states_provinces_lakes'
        self.states_shp = shpreader.natural_earth(resolution='110m',
                                             category='cultural', name=shapename)
        self.mapPlotDlg.closePushButton.clicked.connect(self.mapPlotDlg.done)
        self.mapPlotDlg.savePlotPushButton.clicked.connect(self.mapPlotSave)
        self.mapPlotDlg.colorMapComboBox.addItems(plt.colormaps())
        self.mapPlotDlg.colorMapComboBox.currentIndexChanged.connect(lambda x: self.mapChanged(type='US'))
        self.mapPlotDlg.textSizeSpinBox.valueChanged.connect(lambda x: self.mapChanged(type='US'))
        self.mapPlotDlg.colorBinsSpinBox.valueChanged.connect(lambda x: self.mapChanged(type='US'))
        # self.mapPlotDlg.colorMapComboBox.setCurrentIndex(1)
        # self.mapPlotDlg.textSizeSpinBox.setValue(6)
        self.mapChanged()
        self.mapPlotDlg.exec_()

    def mapChanged(self,type='US'):
        colorMap=self.mapPlotDlg.colorMapComboBox.currentText()
        val = self.mapPlotDlg.textSizeSpinBox.value()
        nbins=self.mapPlotDlg.colorBinsSpinBox.value()
        data = pd.DataFrame.from_dict(self.results, orient='index', columns=[self.calComboBox.currentText()])
        if type=='US':
            self.updateUSMap(data,mapType=colorMap,textSize=val,nbins=nbins)
        else:
            self.updateWorldMap(data, mapType=colorMap,textSize=val,nbins=nbins)


    def mapPlotSave(self):
        fname=QFileDialog.getSaveFileName(self.mapPlotDlg,"Save image as",filter="Image Files (*.png *.tif)")[0]
        if fname!='':
            if os.path.splitext(fname)[1]=='':
                fname=fname+".png"
            self.mapPlotDlg.mplWidget.figure.savefig(fname,dpi=300)

    def updateUSMap(self,data,mapType='Accent',textSize=8,nbins=5):
        self.plotAxes = self.mapPlotDlg.mplWidget.figure.clear()
        self.plotAxes = self.mapPlotDlg.mplWidget.figure.add_axes([0, 0, 1, 1], projection=ccrs.PlateCarree())
        self.plotAxes.set_extent([-130, -60, 22, 45], ccrs.Geodetic())
        self.plotAxes.background_patch.set_visible(False)
        self.plotAxes.outline_patch.set_visible(False)
        self.plotAxes.set_title("US User Map")

        cmap = plt.cm.get_cmap(mapType,nbins)
        for astate in shpreader.Reader(self.states_shp).records():
            name=self.statesInfo[astate.attributes['name_en']][0]
            edgecolor = 'black'
            if name in data.index:
                user=data.loc[name].values[0]
            else:
                user=0.0
            facecolor=cmap(np.sqrt((user-self.minu)/(self.maxu-self.minu)))
            xoffset=0
            yoffset=0
            xfact=1.0
            yfact=1.0
            if astate.attributes['name_en']=='Alaska':
                xoffset=35
                yoffset=-36
                xfact=0.2
                yfact=0.4
            elif astate.attributes['name_en']=='Hawaii':
                xoffset=52
                yoffset=5
                xfact=1.2
                yfact=1.2

            self.plotAxes.add_geometries([shapely.affinity.translate(shapely.affinity.scale(astate.geometry,xfact=xfact,yfact=yfact),\
                                                           xoff=xoffset,yoff=yoffset)], ccrs.PlateCarree(), edgecolor=edgecolor,facecolor=facecolor)

            try:
                x,y=self.statesInfo[astate.attributes['name_en']][1]
                try:
                    xt,yt=self.statesInfo[astate.attributes['name_en']][2]
                    self.plotAxes.annotate(name,xy=(x,y),xycoords='data',xytext=(xt,yt),textcoords='data',arrowprops=dict(arrowstyle="-",
                                      connectionstyle="arc3,rad=0."),annotation_clip=True,size=textSize)
                except:
                    self.plotAxes.text(x,y,name,size=textSize)
            except:
                pass

        if 'DC' in data.index:
            user=data.loc['DC'].values[0]
        else:
            user=0.0
        facecolor=cmap(np.sqrt((user-self.minu)/(self.maxu-self.minu)))
        circle1=plt.Circle((-77.13,39.02),0.5,linewidth=1,edgecolor='k',facecolor=facecolor)
        plt.gcf().gca().add_artist(circle1)
        self.plotAxes.annotate('DC',xy=(-77.13,39.02),xycoords='data',xytext=(-74.13,34.02),textcoords='data',arrowprops=dict(arrowstyle="-",
                                      connectionstyle="arc3,rad=0."),annotation_clip=True,size=textSize)

        sm = plt.cm.ScalarMappable(cmap=cmap)
        sm._A = []
        cbar=plt.colorbar(sm,ax=self.plotAxes,shrink=0.25,pad=0.05)
        tick_locator=ticker.MaxNLocator(nbins=nbins)
        cbar.locator=tick_locator
        cbar.update_ticks()
        cbar.ax.set_yticklabels(['%.1f'%(self.minu+t**2*self.maxu) for t in cbar.ax.get_yticks()],size=textSize)
        self.mapPlotDlg.mplWidget.canvas.draw()

    def create_world_map(self,data,usersCol='users',mapType='Accent',textSize=8,nbins=5):
        self.mapPlotDlg = PlotDialog(self)
        self.maxu=max(data[usersCol])
        self.minu=0

        shapename = 'admin_0_countries'
        self.country_shp = shpreader.natural_earth(resolution='110m',
                                             category='cultural', name=shapename)
        #self.updateUSMap(data,mapType=mapType,textSize=textSize)
        self.mapPlotDlg.closePushButton.clicked.connect(self.mapPlotDlg.done)
        self.mapPlotDlg.savePlotPushButton.clicked.connect(self.mapPlotSave)
        self.mapPlotDlg.colorMapComboBox.addItems(plt.colormaps())
        self.mapPlotDlg.colorMapComboBox.currentIndexChanged.connect(lambda x:self.mapChanged(type='World'))
        self.mapPlotDlg.textSizeSpinBox.valueChanged.connect(lambda x:self.mapChanged(type='World'))
        self.mapPlotDlg.colorBinsSpinBox.valueChanged.connect(lambda x: self.mapChanged(type='World'))
        self.mapChanged(type='World')
        self.mapPlotDlg.exec_()

    def updateWorldMap(self,data,mapType='Accent',textSize=8,nbins=5):
        self.plotAxes = self.mapPlotDlg.mplWidget.figure.clear()
        self.plotAxes = self.mapPlotDlg.mplWidget.figure.add_axes([0, 0, 1, 1], projection=ccrs.PlateCarree())
        #self.plotAxes.set_extent([-130, -60, 22, 45], ccrs.Geodetic())
        self.plotAxes.background_patch.set_visible(False)
        self.plotAxes.outline_patch.set_visible(False)
        self.plotAxes.set_title('World User Map')

        cmap = plt.cm.get_cmap(mapType, nbins)
        for astate in shpreader.Reader(self.country_shp).records():
            name = self.CountryNames['APS_Name'][astate.attributes['NAME_EN']]
            edgecolor = 'black'
            if name in data.index:
                user = data.loc[name].values[0]
            else:
                user = 0.0
            facecolor = cmap(np.sqrt((user - self.minu) / (self.maxu - self.minu)))
            self.plotAxes.add_geometries([astate.geometry], ccrs.PlateCarree(), edgecolor=edgecolor,
                facecolor=facecolor)

        sm = plt.cm.ScalarMappable(cmap=cmap)
        sm._A = []
        cbar = plt.colorbar(sm, ax=self.plotAxes, shrink=0.25, pad=0.05)
        tick_locator = ticker.MaxNLocator(nbins=nbins)
        cbar.locator = tick_locator
        cbar.update_ticks()
        cbar.ax.set_yticklabels(['%.1f' % (self.minu + t ** 2 * self.maxu) for t in cbar.ax.get_yticks()],size=textSize)
        self.mapPlotDlg.mplWidget.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # poniFile='/home/epics/CARS5/Data/Data/saxs/2017-06/Alignment/agbh1.poni'
    w = ChemMatUserStats()
    w.setWindowTitle('ChemMat User Stats')
    # w.setGeometry(50,50,800,800)

    w.show()
    sys.exit(app.exec_())