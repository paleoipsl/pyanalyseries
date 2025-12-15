from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import sys
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from .interactivePlot import interactivePlot

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class displayStackedSeriesWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Ids, open_displayWindows, items):
        super().__init__()

        self.Ids = Ids
        self.open_displayWindows = open_displayWindows
        self.items = items 

        self.seriesWidth = 0.8
        self.sharex = True

        title = 'Display stacked series : ' + ', '.join(self.Ids)
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1000, 800)
        self.setMinimumSize(800, 600)
        
        #----------------------------------------------
        self.interactive_plot = interactivePlot(rows=len(items), cols=1)
        self.myplot()
        
        main_layout = QVBoxLayout()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        sharex_label = QLabel('Shared horizontal axis :')
        self.sharex_cb = QCheckBox()
        self.sharex_cb.setChecked(self.sharex)

        self.close_button = QPushButton("Close", self)

        button_layout.addStretch()
        button_layout.addWidget(sharex_label)
        button_layout.addWidget(self.sharex_cb)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)

        main_layout.addLayout(button_layout)

        self.sharex_cb.stateChanged.connect(self.update)
        self.close_button.clicked.connect(self.close)

        self.setLayout(main_layout)

        #----------------------------------------------
        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def update(self):

        self.sharex = self.sharex_cb.isChecked()

        self.myplot()

    #---------------------------------------------------------------------------------------------
    def myplot(self):

        #-----------------------------------
        for ax in self.interactive_plot.axs:
            ax.remove()
        self.interactive_plot.axs = list(self.interactive_plot.fig.subplots(len(self.items), sharex=False))
        self.interactive_plot.fig.subplots_adjust(hspace=0.5)

        #-----------------------------------
        for n, item in enumerate(self.items):

            ax = self.interactive_plot.axs[n]
            ax.twins = []                           # replace because ax.remove() has deleted those attributs 
            ax.twins_orientation = None

            seriesDict = item.data(0, Qt.UserRole)

            ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
            ax.set_xlabel(seriesDict['X'])
            ax.set_ylabel(seriesDict['Y'])
            ax.autoscale()

            series = seriesDict['Series']
            series = series.groupby(series.index).mean()
            seriesColor = seriesDict['Color']
            Y_axisInverted = seriesDict['Y axis inverted']

            ax.line_points_pairs = []
            line, = ax.plot(series.index, series.values, color=seriesColor, linewidth=self.seriesWidth)
            points = ax.scatter(series.index, series.values, s=5, marker='o', color=seriesColor, visible=False)
            ax.line_points_pairs.append((line, points))

            ax.yaxis.set_inverted(Y_axisInverted)

        #-----------------------------------
        if self.sharex:
            XDict = {}
            for n, item in enumerate(self.items):
                seriesDict = item.data(0, Qt.UserRole)
                if seriesDict['X'] not in XDict:
                    XDict[seriesDict['X']] = []
                XDict[seriesDict['X']].append(n)

            sharexLists = [n for n in XDict.values() if len(n) > 1]
            #print(sharexLists)
            for sharexList in sharexLists:
                base_ax = self.interactive_plot.axs[sharexList[0]]
                for n in sharexList[1:]:
                    #print("sharex", sharexList[0], n)
                    self.interactive_plot.axs[n].sharex(base_ax) 

        #-----------------------------------
        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def sync_with_item(self, item):
        if not item in self.items: return

        self.raise_()

        self.myplot()

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.open_displayWindows.pop(self.Ids, None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    app = QApplication(sys.argv)

    x1 = np.linspace(0, 10, 100)
    y1 = np.sin(x1)
    series1 = pd.Series(y1, index=x1)

    series1Dict = {
        'Id': '111',
        'X': 'x1Name',
        'Y': 'y1Name',
        'Series': series1,
        'Color': 'steelblue',
        'Y axis inverted': True,
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }
    item1 = QTreeWidgetItem()
    item1.setData(0, Qt.UserRole, series1Dict)

    x2 = np.linspace(5, 15, 100)
    y2 = np.cos(x2)
    series2 = pd.Series(y2, index=x2)

    series2Dict = {
        'Id': '222',
        'X': 'x2Name',
        'Y': 'y2Name',
        'Series': series2,
        'Color': 'darkorange',
        'Y axis inverted': True,
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }
    item2 = QTreeWidgetItem()
    item2.setData(0, Qt.UserRole, series2Dict)

    open_displayWindows = {}
    Id_displayWindow = tuple([series1Dict['Id'], series2Dict['Id']])
    displayWindow = displayStackedSeriesWindow(Id_displayWindow, open_displayWindows, [item1, item2])
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app.exec_())
