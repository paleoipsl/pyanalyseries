from PyQt6.QtWidgets import * 
from PyQt6.QtCore import * 
from PyQt6.QtGui import *

import sys
import datetime
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import LogLocator, FuncFormatter

from .misc import *
from .interactivePlot import interactivePlot

import pyleoclim as pyleo
matplotlib.rcdefaults()

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class computeSpectralEstimationWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_spectralEstimationWindows, item, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_spectralEstimationWindows = open_spectralEstimationWindows
        self.item = item
        self.add_item_tree_widget = add_item_tree_widget

        title = 'Compute Spectral Estimation'
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters :')
        groupbox1.setFixedHeight(200)

        groupbox1_layout = QVBoxLayout()

        #-------------------------------
        form_layout = QFormLayout()
        
        self.NW_sb = QDoubleSpinBox(self)
        self.NW_sb.setRange(2.0, 4.0)
        self.NW_sb.setSingleStep(0.5)
        self.NW_sb.setValue(4)
        self.NW_sb.setFixedWidth(100)
        self.NW_sb.valueChanged.connect(self.delayed_update)

        form_layout.addRow("NW :", self.NW_sb)

        #-------------------------------
        groupbox1_layout.addLayout(form_layout)

        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1)

        #----------------------------------------------
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.myplot)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        style = "padding: 4px 12px;"
        self.compute_button = QPushButton("Compute", self)
        self.compute_button.setStyleSheet(style)
        self.save_button = QPushButton("Save Spectral Estimation", self)
        self.save_button.setStyleSheet(style)
        self.close_button = QPushButton("Close", self)
        self.close_button.setStyleSheet(style)
        button_layout.addStretch()

        button_layout.addWidget(self.compute_button)
        button_layout.addWidget(self.save_button)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.compute_button.clicked.connect(self.myplot)
        self.save_button.clicked.connect(self.save_series)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        #self.myplot()

    #---------------------------------------------------------------------------------------------
    def delayed_update(self):

        self.status_bar.showMessage('Waiting', 1000)
        self.update_timer.start(1000)

    #---------------------------------------------------------------------------------------------
    def myplot(self):

        self.seriesDict = self.item.data(0, Qt.ItemDataRole.UserRole)
        self.xName = self.seriesDict['X']
        self.yName = self.seriesDict['Y']
        self.series = self.seriesDict['Series']
        self.series = self.series.groupby(self.series.index).mean()

        self.status_bar.showMessage('Computing...', 0)
        QApplication.processEvents()

        self.NW =  self.NW_sb.value()

        #ts = pyleo.utils.load_dataset('LR04')
        ts = pyleo.Series(time=self.series.index.to_numpy(), value=self.series.to_numpy(), verbose=False)

        # Power Spectral Density
        PSD = ts.standardize().interp().spectral(method='periodogram')
        f = PSD.frequency
        Sf = PSD.amplitude
        mask = f > 0
        f = f[mask]
        Sf = Sf[mask]
        period = 1 / f

        series_PSD = pd.Series(Sf, index=period)
        self.index = series_PSD.index
        self.values = series_PSD.values

        ax = self.interactive_plot.axs[0]
        ax.clear()
        self.interactive_plot.reset()

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)

        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.xaxis.set_major_locator(LogLocator(base=10, subs=[1, 2, 5]))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda val, pos: f"{val:g}"))
        ax.invert_xaxis()

        color = "darkorange"
        line1, = ax.plot(self.index, self.values, linewidth=0.5, color=color, label='Periodogram')
        points1 = ax.scatter(self.index, self.values, s=5, marker='o', color=color, visible=False)
        ax.line_points_pairs.append((line1, points1))

        #----------------------
        #PSD = ts.standardize().spectral(method='lomb_scargle', freq='lomb_scargle')
        PSD = ts.standardize().interp().spectral(method='mtm', settings={'NW': self.NW})

        f = PSD.frequency
        Sf = PSD.amplitude
        mask = f > 0
        f = f[mask]
        Sf = Sf[mask]
        period = 1 / f
        color = "steelblue"
        line2, = ax.plot(period, Sf, linewidth=0.5, color=color, label='Lomb Scargle')
        points2 = ax.scatter(period, Sf, s=5, marker='o', color=color, visible=False)
        ax.line_points_pairs.append((line2, points2))

        #----------------------
        legend = ax.legend()
        for legend_line, ax_line in zip(legend.get_lines(), ax.get_lines()):
            legend_line.set_picker(5)
            ax.map_legend_to_line[legend_line] = ax_line

        #----------------------
        ax.set_xlabel('Period')
        ax.set_ylabel('PSD')
        ax.autoscale()

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

        self.status_bar.showMessage('Done', 1000)
        QApplication.processEvents()

    #---------------------------------------------------------------------------------------------
    def save_series(self):

        series_Id = generate_Id() 

        history = f'Spectral Estimation parameters : xxxx'
        history += f'---> series <i><b>{series_Id}</b></i>'

        PSD_seriesDict = {
            'Id': series_Id, 
            'Type': 'Series PSD', 
            'Name': '', 
            'X': 'Period',
            'Y': 'PSD',
            'Color': generate_color(exclude_color=self.seriesDict['Color']),
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'History': history,
            'Comment': '',
            'Series': pd.Series(self.values, index=self.index),
            }

        try:
            position = self.item.parent().indexOfChild(self.item)
            self.add_item_tree_widget(self.item.parent(), PSD_seriesDict, position+1)
        except:
            pass

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.open_spectralEstimationWindows.pop('123456', None)
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
            'Color': generate_color(),
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'Comment': '',
            'History': ''
    }
    item = QTreeWidgetItem()
    item.setData(0, Qt.ItemDataRole.UserRole, seriesDict)

    Id_spectralEstimationWindow = '1234'
    open_spectralEstimationWindows = {}

    spectralEstimationWindow = computeSpectralEstimationWindow(open_spectralEstimationWindows, item, handle_item)
    open_spectralEstimationWindows[Id_spectralEstimationWindow] = computeSpectralEstimationWindow
    spectralEstimationWindow.show()

    sys.exit(app.exec())

