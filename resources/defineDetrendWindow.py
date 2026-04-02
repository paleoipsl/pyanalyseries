from resources.qt_compat import *

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from .misc import *
from .interactivePlot import interactivePlot

import sys
import datetime
import numpy as np
import pandas as pd

import pyleoclim as pyleo
matplotlib.rcdefaults()

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineDetrendWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_detrendWindows, item, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_detrendWindows = open_detrendWindows
        self.item = item
        self.add_item_tree_widget = add_item_tree_widget

        self.seriesWidth = 0.8

        title = 'Define DETREND : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters')
        groupbox1.setFixedHeight(150)

        groupbox1_layout = QVBoxLayout()

        #-------------------------------
        form_layout = QFormLayout()
        
        self.method_dropdown = QComboBox()
        self.method_dropdown.addItems(["linear", "constant", "savitzky-golay", "emd"])
        self.method_dropdown.setCurrentText("emd")
        self.method_dropdown.setFixedWidth(200)
        self.method_dropdown.currentIndexChanged.connect(self.update_value)

        self.method = self.method_dropdown.currentText()

        form_layout.addRow("Detrend method :", self.method_dropdown)

        #-------------------------------
        groupbox1_layout.addLayout(form_layout)

        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()
        self.myplot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        style = "padding: 4px 12px;"
        self.saveDetrend_button = QPushButton("Save detrend", self)
        self.saveDetrend_button.setStyleSheet(style)
        self.saveDetrend_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.saveDetrendAndSeriesDetrended_button = QPushButton("Save detrend and series detrended", self)
        self.saveDetrendAndSeriesDetrended_button.setStyleSheet(style)
        self.close_button = QPushButton("Close", self)
        self.close_button.setStyleSheet(style)
        button_layout.addStretch()

        saveClose_layout = QVBoxLayout()
        saveClose_layout.addWidget(self.saveDetrend_button)
        saveCloseLine_layout = QHBoxLayout()
        saveCloseLine_layout.addWidget(self.saveDetrendAndSeriesDetrended_button)
        saveCloseLine_layout.addWidget(self.close_button)
        saveClose_layout.addLayout(saveCloseLine_layout)
        button_layout.addLayout(saveClose_layout)
        
        main_layout.addLayout(button_layout)

        self.saveDetrend_button.clicked.connect(self.saveDetrend)
        self.saveDetrendAndSeriesDetrended_button.clicked.connect(self.saveDetrendAndSeriesDetrended)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        self.status_bar.setSizeGripEnabled(False)

        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_shortcut.activated.connect(self.close)

        self.interactive_plot.fig.canvas.setFocus()

        self.status_bar.showMessage('Ready', 5000)

    #---------------------------------------------------------------------------------------------
    def update_value(self):
        self.method = self.method_dropdown.currentText()

        xlim = self.interactive_plot.axs[0].get_xlim()
        ylim = self.interactive_plot.axs[0].get_ylim()
        self.interactive_plot.axs[0].clear()
        self.myplot(limits=[xlim,ylim])

    #---------------------------------------------------------------------------------------------
    def myplot(self, limits=None):

        self.interactive_plot.reset()

        self.seriesDict = self.item.data(0, Qt.ItemDataRole.UserRole)
        self.xName = self.seriesDict['X']
        self.yName = self.seriesDict['Y']
        self.series = self.seriesDict['Series']
        self.series = self.series.groupby(self.series.index).mean()

        #self.series = pyleo.utils.load_dataset('NINO3').to_pandas(paleo_style=True)

        ax = self.interactive_plot.axs[0]

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)
        ax.autoscale()

        ts = pyleo.Series(time=self.series.index.to_numpy(), value=self.series.to_numpy(), verbose=False)
        ts_dt = ts.detrend(method=self.method, preserve_mean=True)
        #ts_dt = ts.standardize()
        #ts_dt = ts.gaussianize()
        self.seriesDetrended = pd.Series(ts_dt.value, index=ts_dt.time)
        seriesColor = self.seriesDict['Color']

        line1, = ax.plot(self.series.index, self.series.values, color=seriesColor, linewidth=self.seriesWidth, label='Original')
        points1 = ax.scatter(self.series.index, self.series.values, s=5, marker='o', color=seriesColor, visible=False)
        ax.line_points_pairs.append((line1, points1))
        
        line2, = ax.plot(self.seriesDetrended.index, self.seriesDetrended.values, color='black', linewidth=self.seriesWidth, alpha=0.4, label='Detrended')
        points2 = ax.scatter(self.seriesDetrended.index, self.seriesDetrended.values, s=5, marker='o', color='black', alpha=0.4, visible=False)
        ax.line_points_pairs.append((line2, points2))

        legend = ax.legend()
        for legend_line, ax_line in zip(legend.get_lines(), ax.get_lines()):
            legend_line.set_picker(5)
            ax.map_legend_to_line[legend_line] = ax_line

        if limits:
            ax.set_xlim(limits[0])
            ax.set_ylim(limits[1])

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def saveDetrend(self):
        detrend_Id = generate_Id()
        detrendDict = {
            'Id': detrend_Id,
            'Type': 'DETREND', 
            'Name': f'Detrend with method {self.method}', 
            'Parameters': f'{self.method}',
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'Comment': '',
            'History': f'DETREND <i><b>{detrend_Id}</i></b> with method : {self.method}'
        }
        try:
            self.add_item_tree_widget(self.item.parent(), detrendDict)
        except:
            pass

        return detrend_Id

    #---------------------------------------------------------------------------------------------
    def saveDetrendAndSeriesDetrended(self):
        detrend_Id = self.saveDetrend() 

        detrended_Id = generate_Id()
        detrended_seriesDict = self.seriesDict | {'Id': detrended_Id,
            'Type': 'Series detrended', 
            'Series': self.seriesDetrended,
            'Color': generate_color(exclude_color=self.seriesDict['Color']),
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'History': append_to_htmlText(self.seriesDict['History'], 
                f'Series <i><b>{self.seriesDict["Id"]}</i></b> detrended with DETREND <i><b>{detrend_Id}</i></b> with method {self.method}<BR>---> series <i><b>{detrended_Id}</b></i>'),
            'Comment': '',
        }

        try:
            position = self.item.parent().indexOfChild(self.item)
            self.add_item_tree_widget(self.item.parent(), detrended_seriesDict, position+1)
        except:
            pass

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.open_detrendWindows.pop(self.Id, None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(parent, item):
        print('handle', parent, item)

    app = QApplication([])

    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    series = pd.Series(y, index=x)

    seriesDict = {
            'Id': 'abcd', 
            'X': 'xName', 
            'Y': 'yName', 
            'Series': series, 
            'Color': 'darkorange', 
            'Date': '', 
            'Comment': 'A text', 
            'History': 'command1 ; command2'
    }
    item = QTreeWidgetItem()
    item.setData(0, Qt.ItemDataRole.UserRole, seriesDict)

    open_detrendWindows = {}
    Id_detrendWindow = '1234'
    detrendWindow = defineDetrendWindow(Id_detrendWindow, open_detrendWindows, item, handle_item)
    open_detrendWindows[Id_detrendWindow] = detrendWindow
    detrendWindow.show()

    sys.exit(app_exec(app))
