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

from .misc import *
from .CustomQTableWidget import CustomQTableWidget 
from .interactivePlot import interactivePlot
from .defineInterpolationWindow import defineInterpolationWindow

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class displaySingleSeriesWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_displayWindows, item):
        super().__init__()

        self.Id = Id
        self.open_displayWindows = open_displayWindows
        self.item = item

        self.seriesWidth = 0.8

        self.seriesDict = self.item.data(0, Qt.UserRole)

        self.xName = self.seriesDict['X']
        self.yName = self.seriesDict['Y']
        series = self.seriesDict['Series']

        title = 'Display series : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        self.tabs = QTabWidget()
        
        #----------------------------------------------
        data_tab = QWidget()
        data_layout = QVBoxLayout()
        self.data_table = CustomQTableWidget()
        self.data_table.setRowCount(len(series))
        self.data_table.setColumnCount(2)
        self.data_table.setHorizontalHeaderLabels([self.xName, self.yName])
        duplicates = series.index.duplicated()
        missing_values = series.isna().to_numpy()
        series = series.sort_index()

        for i in range(len(series)):
            self.data_table.setItem(i, 0, QTableWidgetItem(str(f'{series.index[i]:.6f}')))
            self.data_table.setItem(i, 1, QTableWidgetItem(str(f'{series.values[i]:.6f}')))
            if missing_values[i]:
                base = QColor('peachpuff')
                alt = QColor('white') if i % 2 == 0 else QColor('whitesmoke')
                background_color = blend_colors(base, alt, ratio=0.6)
            elif duplicates[i]:
                base = QColor('lemonchiffon')
                alt = QColor('white') if i % 2 == 0 else QColor('whitesmoke')
                background_color = blend_colors(base, alt, ratio=0.6)
            else:
                background_color = QColor('white') if i % 2 == 0 else QColor('whitesmoke')
            self.data_table.item(i, 0).setBackground(background_color)
            self.data_table.item(i, 1).setBackground(background_color)
        self.data_table.resizeColumnsToContents()
        self.data_table.set_italic_headers()

        data_layout.addWidget(self.data_table)
        data_tab.setLayout(data_layout)
        
        #----------------------------------------------
        stats_tab = QWidget()
        stats_layout = QVBoxLayout()
        stats_table = CustomQTableWidget()
        stats_table.setRowCount(6)
        stats_table.setColumnCount(2)
        stats_table.setHorizontalHeaderLabels(["Stat", "Value"])
        stats = {
            "Number of points": (len(series), 'd'),
            "Number of duplicates": ((series.index.value_counts() > 1).sum(), 'd'),
            "Number of missing": (series.isna().sum(), 'd'),
            "Mean": (series.mean(), '.2f'),
            "Maximum": (series.max(), '.2f'),
            "Minimum": (series.min(), '.2f'),
        }
        for i, (key, value) in enumerate(stats.items()):
            stats_table.setItem(i, 0, QTableWidgetItem(key))
            stats_table.setItem(i, 1, QTableWidgetItem(f"{value[0]:{value[1]}}"))
            if i%2 == 0:
                stats_table.item(i, 0).setBackground(QColor(250, 250, 250))
                stats_table.item(i, 1).setBackground(QColor(250, 250, 250))
        stats_table.resizeColumnsToContents()

        stats_layout.addWidget(stats_table)
        stats_tab.setLayout(stats_layout)
        
        #----------------------------------------------
        plot_tab = QWidget()
        plot_layout = QVBoxLayout()
   
        self.interactive_plot = interactivePlot()
        canvas = FigureCanvas(self.interactive_plot.fig)
        plot_layout.addWidget(canvas)
        self.myplot()
        
        plot_tab.setLayout(plot_layout)

        #----------------------------------------------
        info_tab = QWidget()
        info_layout = QVBoxLayout()

        self.textName = QLabel(f"Name : <b>{self.seriesDict['Name']}</b>")

        self.textDate = QLabel(f"Date : {self.seriesDict['Date']}")

        labelHistory = QLabel("History :")
        self.textHistory = QTextEdit()
        self.textHistory.setFixedHeight(self.textHistory.fontMetrics().lineSpacing() * 10)
        self.textHistory.setText(self.seriesDict['History'])
        self.textHistory.setReadOnly(True)
        self.textHistory.setStyleSheet("""
            QTextEdit[readOnly="true"] {
                background-color: #f8f8f8;
                border: 1px solid lightgray;
                font-family: Courier New;
            }
        """)

        labelComment = QLabel("Comment :")
        self.textComment = QTextEdit()
        self.textComment.setFixedHeight(self.textComment.fontMetrics().lineSpacing() * 10)
        self.textComment.setText(self.seriesDict['Comment'])

        info_layout.addWidget(self.textName)
        info_layout.addWidget(self.textDate)
        info_layout.addWidget(labelHistory)
        info_layout.addWidget(self.textHistory)
        info_layout.addWidget(labelComment)
        info_layout.addWidget(self.textComment)
        info_layout.addStretch()

        info_tab.setLayout(info_layout)

        #----------------------------------------------
        self.tabs.addTab(data_tab, "Data")
        self.tabs.addTab(stats_tab, "Stats")
        self.tabs.addTab(plot_tab, "Plot")
        self.tabs.addTab(info_tab, "Info")
        self.tabs.setCurrentIndex(2)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        self.close_button = QPushButton("Close", self)
        button_layout.addStretch()

        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.close_button.clicked.connect(self.close)

        #----------------------------------------------
        self.setLayout(main_layout)

        menu_bar = QMenuBar(self)
        main_layout.setMenuBar(menu_bar)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

    #---------------------------------------------------------------------------------------------

        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def myplot(self, limits=None):
       
        self.interactive_plot.reset()

        ax = self.interactive_plot.axs[0]

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)
        ax.autoscale()
        seriesDict = self.item.data(0, Qt.UserRole)
        series = seriesDict['Series']
        series = series.groupby(series.index).mean()           # sort on index by default
        seriesColor = seriesDict['Color']

        line, = ax.plot(series.index, series.values, color=seriesColor, linewidth=self.seriesWidth)
        points = ax.scatter(series.index, series.values, s=5, marker='o', color=seriesColor, visible=False)
        ax.line_points_pairs.append((line, points))

        if 'InterpolationMode' in seriesDict:
            interpolationMode = seriesDict['InterpolationMode']
            XOriginal = seriesDict['XOriginal']
            X1Coords = seriesDict['X1Coords']
            X2Coords = seriesDict['X2Coords']
            (f_1to2, f_2to1) = defineInterpolationWindow.defineInterpolationFunctions(X1Coords, X2Coords, interpolationMode=interpolationMode)

            second_xaxis = ax.secondary_xaxis('top', functions=(f_1to2, f_2to1))
            second_xaxis.tick_params(labelrotation=30)
            second_xaxis.set_xlabel(XOriginal)
            plt.setp(second_xaxis.get_xticklabels(), horizontalalignment='left')

            self.interactive_plot.top_margin = 100

        if limits:
            ax.set_xlim(limits[0])
            ax.set_ylim(limits[1])

        ax.figure.canvas.draw()
        ax.figure.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def sync_with_item(self, item):
        if item != self.item: return

        self.raise_()

        self.seriesDict = self.item.data(0, Qt.UserRole)
        self.textName.setText(f"Name : <b>{self.seriesDict['Name']}</b>")
        self.xName = self.seriesDict['X']
        self.yName = self.seriesDict['Y']
        self.data_table.setHorizontalHeaderLabels([self.xName, self.yName])
        self.data_table.resizeColumnsToContents()
        xlim = self.interactive_plot.axs[0].get_xlim()
        ylim = self.interactive_plot.axs[0].get_ylim()
        self.interactive_plot.axs[0].clear()
        self.myplot(limits=[xlim,ylim])

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.seriesDict['Comment'] = self.textComment.toPlainText()
        # if WS has been removed while a Display is active 
        try:
            self.item.setData(0, Qt.UserRole, self.seriesDict)
        except:
            #print("item not available to be updated")
            pass 
        self.open_displayWindows.pop(self.Id, None)
        event.accept()

#=========================================================================================

# Example usage
if __name__ == "__main__":

    app = QApplication(sys.argv)

    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    series = pd.Series(y, index=x)

    itemDict = {
        'Id': 'abcd',
        'Name': 'A name',
        'X': 'xName',
        'Y': 'yName',
        'Series': series, 
        'Color': 'darkorange',
        'Date': '',
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }

    item = QTreeWidgetItem()
    item.setData(0, Qt.UserRole, itemDict)

    open_displayWindows = {}
    Id_displayWindow = '1234'
    displayWindow = displaySingleSeriesWindow(Id_displayWindow, open_displayWindows, item)
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app.exec_())
