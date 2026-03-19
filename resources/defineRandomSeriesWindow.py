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

from .misc import *
from .interactivePlot import interactivePlot

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineRandomSeriesWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, open_randomSeriesWindow, add_item_tree_widget):
        super().__init__()

        self.open_randomSeriesWindow = open_randomSeriesWindow
        self.add_item_tree_widget = add_item_tree_widget

        title = 'Define Random series'
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
        
        self.xstart_sb = QSpinBox(self)
        self.xstart_sb.setRange(-100000, 10000)
        self.xstart_sb.setSingleStep(100)
        self.xstart_sb.setValue(0)
        self.xstart_sb.setFixedWidth(100)
        self.xstart_sb.valueChanged.connect(self.delayed_update)

        self.xend_sb = QSpinBox(self)
        self.xend_sb.setRange(-100000, 10000)
        self.xend_sb.setSingleStep(100)
        self.xend_sb.setValue(100)
        self.xend_sb.setFixedWidth(100)
        self.xend_sb.valueChanged.connect(self.delayed_update)

        self.nbPts_sb = QSpinBox(self)
        self.nbPts_sb.setRange(10, 1000)
        self.nbPts_sb.setSingleStep(100)
        self.nbPts_sb.setValue(101)
        self.nbPts_sb.setFixedWidth(100)
        self.nbPts_sb.valueChanged.connect(self.delayed_update)

        validator = QDoubleValidator()
        validator.setDecimals(2) 
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        validator.setLocale(QLocale("en_US"))

        self.minVal_input = QLineEdit()
        self.minVal_input.setValidator(validator)
        self.minVal_input.setFixedWidth(100)
        self.minVal_input.setText('0.0')
        self.minVal_input.editingFinished.connect(self.delayed_update)

        self.maxVal_input = QLineEdit()
        self.maxVal_input.setValidator(validator)
        self.maxVal_input.setFixedWidth(100)
        self.maxVal_input.setText('10.0')
        self.maxVal_input.editingFinished.connect(self.delayed_update)

        form_layout.addRow("Start point :", self.xstart_sb)
        form_layout.addRow("End point :", self.xend_sb)
        form_layout.addRow("Nb of points :", self.nbPts_sb)
        form_layout.addRow("Min value:", self.minVal_input)
        form_layout.addRow("Max value:", self.maxVal_input)

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
        self.shuffle_button = QPushButton("Shuffle", self)
        self.shuffle_button.setStyleSheet(style)
        self.import_button = QPushButton("Import series", self)
        self.import_button.setStyleSheet(style)
        self.close_button = QPushButton("Close", self)
        self.close_button.setStyleSheet(style)
        button_layout.addStretch()

        button_layout.addWidget(self.shuffle_button)
        button_layout.addWidget(self.import_button)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.shuffle_button.clicked.connect(self.myplot)
        self.import_button.clicked.connect(self.import_series)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        self.status_bar.setSizeGripEnabled(False)

        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        self.myplot()

    #---------------------------------------------------------------------------------------------
    def delayed_update(self):

        self.status_bar.showMessage('Waiting', 1000)
        self.update_timer.start(1000)

    #---------------------------------------------------------------------------------------------
    def myplot(self):

        self.xstart =  self.xstart_sb.value()
        self.xend =  self.xend_sb.value()
        self.nbPts =  self.nbPts_sb.value()

        QLineEdit_check(self.minVal_input, 0.0)
        self.minVal =  float(self.minVal_input.text())
        QLineEdit_check(self.maxVal_input, 10.0)
        self.maxVal =  float(self.maxVal_input.text())

        x = np.linspace(self.xstart, self.xend, self.nbPts)
        y = np.random.uniform(self.minVal,self.maxVal, self.nbPts)

        series = pd.Series(y, index=x)

        self.index = series.index
        self.values = series.values

        ax = self.interactive_plot.axs[0]
        ax.clear()
        self.interactive_plot.reset()

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)

        color = "darkorange"
        line1, = ax.plot(self.index, self.values, linewidth=0.5, color=color)
        points1 = ax.scatter(self.index, self.values, s=5, marker='o', color=color, visible=False)
        ax.line_points_pairs.append((line1, points1))

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.autoscale()

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()
        self.status_bar.showMessage('Updated', 1000)

    #---------------------------------------------------------------------------------------------
    def import_series(self):

        series_Id = generate_Id()
        history = f'Random series with parameters :' + \
                   '<ul>' + \
                   f'<li>Start point : {self.xstart}' + \
                   f'<li>End point : {self.xend}' + \
                   f'<li>Nb of points : {self.nbPts}' + \
                   f'<li>Min value : {self.maxVal}' + \
                   f'<li>Max value : {self.minVal}' + \
                   '</ul>'
        history += f'---> series <i><b>{series_Id}</b></i>'

        seriesDict = {
            'Id': series_Id, 
            'Type': 'Series', 
            'Name': '', 
            'X': 'X',
            'Y': 'Y',
            'Color': generate_color(),
            'History': history,
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'Comment': '',
            'Series': pd.Series(self.values, index=self.index),
            }

        try:
            self.add_item_tree_widget(None, seriesDict)          # will be added on parent from current index
        except:
            pass

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.open_randomSeriesWindow.pop('123456', None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(parent, item):
        print('handle', parent, item)

    app = QApplication([])

    Id_randomSeriesWindow = '1234'
    open_randomSeriesWindow = {}

    randomSeriesWindow = defineRandomSeriesWindow(open_randomSeriesWindow, handle_item)
    open_randomSeriesWindow[Id_randomSeriesWindow] = defineRandomSeriesWindow
    randomSeriesWindow.show()

    sys.exit(app.exec())

