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
class defineSinusoidalSeriesWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, open_sinusoidalSeriesWindow, add_item_tree_widget):
        super().__init__()

        self.open_sinusoidalSeriesWindow = open_sinusoidalSeriesWindow
        self.add_item_tree_widget = add_item_tree_widget

        self.setWindowTitle('Define Sinusoidal series')
        self.resize(1200, 750)
        
        main_layout = QVBoxLayout(self)

        #========================================================
        # === PARAMETER PANEL (horizontal layout)
        #========================================================
        groupbox1 = QGroupBox('Parameters :')
        groupbox1_layout = QHBoxLayout()
        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1)

        validator = QDoubleValidator()
        validator.setDecimals(4)
        validator.setLocale(QLocale("en_US"))

        #==== Column 1 : X-domain and noise
        domain_layout = QFormLayout()
        self.xstart_sb = QSpinBox()
        self.xstart_sb.setRange(0, 100000)
        self.xstart_sb.setValue(0)
        self.xend_sb   = QSpinBox()
        self.xend_sb.setRange(1, 100000)
        self.xend_sb.setValue(1000)
        self.nbPts_sb  = QSpinBox()
        self.nbPts_sb.setRange(10, 10000)
        self.nbPts_sb.setValue(1000)
        self.noise_input = QLineEdit("0.2")
        self.noise_input.setValidator(validator)
        for w in [self.xstart_sb, self.xend_sb, self.nbPts_sb, self.noise_input]:
            w.setFixedWidth(100)
            if isinstance(w, QSpinBox):
                w.valueChanged.connect(self.delayed_update)
            else:
                w.editingFinished.connect(self.delayed_update)
        domain_layout.addRow("Start :", self.xstart_sb)
        domain_layout.addRow("End :", self.xend_sb)
        domain_layout.addRow("Nb points :", self.nbPts_sb)
        domain_layout.addRow("Noise σ :", self.noise_input)
        groupbox1_layout.addLayout(domain_layout)

        #==== Column 2 : Sinusoid #1
        box1 = QFormLayout()
        self.period1_input = QLineEdit("200") 
        self.amp1_input = QLineEdit("3.0") 
        self.phase1_input = QLineEdit("0.0")
        for w in [self.period1_input, self.amp1_input, self.phase1_input]:
            w.setValidator(validator); w.setFixedWidth(100); w.editingFinished.connect(self.delayed_update)
        box1.addRow(QLabel("<b>Sinusoid #1</b>"))
        box1.addRow("Period1 :", self.period1_input)
        box1.addRow("Amp1 :", self.amp1_input)
        box1.addRow("Phase1 (rad) :", self.phase1_input)
        groupbox1_layout.addLayout(box1)

        #==== Column 3 : Sinusoid #2
        box2 = QFormLayout()
        self.period2_input = QLineEdit("10") 
        self.amp2_input = QLineEdit("0.5") 
        self.phase2_input = QLineEdit("0.0")
        for w in [self.period2_input, self.amp2_input, self.phase2_input]:
            w.setValidator(validator); w.setFixedWidth(100); w.editingFinished.connect(self.delayed_update)
        box2.addRow(QLabel("<b>Sinusoid #2</b>"))
        box2.addRow("Period2 :", self.period2_input)
        box2.addRow("Amp2 :", self.amp2_input)
        box2.addRow("Phase2 (rad) :", self.phase2_input)
        groupbox1_layout.addLayout(box2)

        main_layout.addWidget(groupbox1)

        #========================================================
        # === FORMULA DISPLAY (HTML)
        #========================================================
        self.formula_label = QLabel()
        self.formula_label.setStyleSheet("""
            color: #222;
            padding: 6px;
            border-top: 1px solid #ccc;
        """)
        self.formula_label.setFont(QFont("Courier New"))
        self.formula_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        main_layout.addWidget(self.formula_label)

        #========================================================
        # === PLOT AREA
        #========================================================
        self.interactive_plot = interactivePlot()
        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #========================================================
        # === CONTROL BUTTONS
        #========================================================
        button_layout = QHBoxLayout()
        style = "padding: 4px 12px;"
        self.shuffle_button = QPushButton("Generate")
        self.import_button  = QPushButton("Import series")
        self.close_button   = QPushButton("Close")
        for b in [self.shuffle_button, self.import_button, self.close_button]:
            b.setStyleSheet(style)
        button_layout.addStretch()
        button_layout.addWidget(self.shuffle_button)
        button_layout.addWidget(self.import_button)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        #========================================================
        # === STATUS BAR
        #========================================================
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        self.status_bar.setSizeGripEnabled(False)

        main_layout.addWidget(self.status_bar)

        #========================================================
        # === CONNECTIONS
        #========================================================
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.myplot)

        self.shuffle_button.clicked.connect(self.myplot)
        self.import_button.clicked.connect(self.import_series)
        self.close_button.clicked.connect(self.close)

        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_shortcut.activated.connect(self.close)

        self.myplot()

    #---------------------------------------------------------------------------------------------
    def delayed_update(self):
        self.status_bar.showMessage('Waiting', 1000)
        self.update_timer.start(800)

    #---------------------------------------------------------------------------------------------
    def myplot(self):
        self.xstart = self.xstart_sb.value()
        self.xend   = self.xend_sb.value()
        self.nbPts  = self.nbPts_sb.value()

        QLineEdit_check(self.period1_input, 200)
        period1 = float(self.period1_input.text())
        if period1 <= 0:
            raise ValueError("Period1 must be > 0.")
        f1 = 1.0 / period1
        
        QLineEdit_check(self.amp1_input, 3.0)
        a1 = float(self.amp1_input.text())
        QLineEdit_check(self.phase1_input, 0.0)
        p1 = float(self.phase1_input.text())
        
        QLineEdit_check(self.period2_input, 10)
        period2 = float(self.period2_input.text())
        if period2 <= 0:
            raise ValueError("Period2 must be > 0.")
        f2 = 1.0 / period2
        
        QLineEdit_check(self.amp2_input, 0.5)
        a2 = float(self.amp2_input.text())
        QLineEdit_check(self.phase2_input, 0.0)
        p2 = float(self.phase2_input.text())

        QLineEdit_check(self.noise_input, 0.2)
        noise = float(self.noise_input.text())

        x = np.linspace(self.xstart, self.xend, self.nbPts)
        y = a1*np.sin(2*np.pi*f1*x + p1) + a2*np.sin(2*np.pi*f2*x + p2)
        if noise > 0:
            y += np.random.normal(0, noise, len(x))

        series = pd.Series(y, index=x)
        self.index, self.values = series.index, series.values

        #=== Update HTML formula
        self.formula_label.setText(
            f"<b>Formula:</b><br>"
            f"y = A<sub>1</sub>·sin(2π·x / P<sub>1</sub> + φ<sub>1</sub>)"
            f" + A<sub>2</sub>·sin(2π·x / P<sub>2</sub> + φ<sub>2</sub>)"
            f" + N(0,σ)"
            f"<br>"
            f"&nbsp; = {a1:.2f}·sin(2π·x / {period1:.2f} + {p1:.2f})"
            f" + {a2:.2f}·sin(2π·x / {period2:.2f} + {p2:.2f})"
            f" + N(0,{noise:.2f})"
        )

        #=== Update main plot
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
        self.interactive_plot.fig.canvas.draw()
        self.status_bar.showMessage('Updated', 1000)

    #---------------------------------------------------------------------------------------------
    def import_series(self):
    
        series_Id = generate_Id()
    
        xstart = self.xstart_sb.value()
        xend = self.xend_sb.value()
        nbPts = self.nbPts_sb.value()
        noise = float(self.noise_input.text())
    
        period1 = float(self.period1_input.text())
        a1 = float(self.amp1_input.text())
        p1 = float(self.phase1_input.text())
    
        period2 = float(self.period2_input.text())
        a2 = float(self.amp2_input.text())
        p2 = float(self.phase2_input.text())
    
        #----------------------------------------------
        # Short, user-friendly name
        name = f"Sinusoidal | P=[{period1:g},{period2:g}] | A=[{a1:g},{a2:g}] | noise={noise:g}"
    
        #----------------------------------------------
        # Detailed history (traceability)
        history = (
            "Sinusoidal series generated with parameters: "
            f"x_start={xstart}; x_end={xend}; nb_points={nbPts}; noise_sigma={noise}; "
            f"period1={period1}; amp1={a1}; phase1={p1}; "
            f"period2={period2}; amp2={a2}; phase2={p2}"
        )
        history += f"<BR>---> series <i><b>{series_Id}</b></i>"

        #----------------------------------------------
        seriesDict = {
            'Id': series_Id,
            'Type': 'Series',
            'Name': name,
            'X': 'X',
            'Y': 'Y',
            'Color': generate_color(),
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'History': history,
            'Comment': '',
            'Series': pd.Series(self.values, index=self.index),
        }
    
        try:
            self.add_item_tree_widget(None, seriesDict)
        except:
            pass

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.open_sinusoidalSeriesWindow.pop('123456', None)
        event.accept()


#=========================================================================================
# Example usage
if __name__ == "__main__":
    def handle_item(parent, item):
        print('handle', parent, item)

    app = QApplication([])
    open_sinusoidalSeriesWindow = {}
    win = defineSinusoidalSeriesWindow(open_sinusoidalSeriesWindow, handle_item)
    open_sinusoidalSeriesWindow['sin'] = defineSinusoidalSeriesWindow
    win.show()
    sys.exit(app.exec())

