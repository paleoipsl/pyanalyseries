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
class computeFrequencyFilterWindow(QWidget):

    METHOD_BUTTER = "Butterworth"
    METHOD_LANCZOS = "Lanczos"
    METHOD_FIR = "FIR"
    METHOD_SAVGOL = "Savitzky-Golay"

    BUTTER_MODE_LONG = "Long periods"
    BUTTER_MODE_BAND = "Period band"

    DOC_BUTTER = "https://pyleoclim-util.readthedocs.io/en/latest/utils/introduction.html#pyleoclim.utils.filter.butterworth"
    DOC_LANCZOS = "https://pyleoclim-util.readthedocs.io/en/latest/utils/introduction.html#pyleoclim.utils.filter.lanczos"
    DOC_FIR = "https://pyleoclim-util.readthedocs.io/en/latest/utils/introduction.html#pyleoclim.utils.filter.firwin"
    DOC_SAVGOL = "https://pyleoclim-util.readthedocs.io/en/latest/utils/introduction.html#pyleoclim.utils.filter.savitzky_golay"

    # ---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_frequencyFilterWindows, item, add_item_tree_widget):

        super().__init__()

        self.Id = Id
        self.open_frequencyFilterWindows = open_frequencyFilterWindows
        self.item = item
        self.add_item_tree_widget = add_item_tree_widget

        self.seriesWidth = 0.8

        self.filter_results = []
        self.original_result = None

        self.seriesDict = self.item.data(0, Qt.ItemDataRole.UserRole)
        self.xName = self.seriesDict['X']
        self.yName = self.seriesDict['Y']

        title = "Compute Frequency Filter : " + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(900, 650)

        main_layout = QVBoxLayout(self)

        #----------------------------------------------
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.compute_filter)

        #----------------------------------------------
        groupbox1 = QGroupBox("Parameters :")
        groupbox1_layout = QVBoxLayout()

        top_layout = QHBoxLayout()

        self.method_combo = QComboBox(self)
        self.method_combo.addItems([
            self.METHOD_BUTTER,
            self.METHOD_LANCZOS,
            self.METHOD_FIR,
            self.METHOD_SAVGOL
        ])
        self.method_combo.setFixedWidth(180)

        self.compute_button = QPushButton("Compute", self)
        self.remove_button = QPushButton("Remove last", self)
        self.compute_button.setStyleSheet('padding: 4px 12px;')
        self.remove_button.setStyleSheet('padding: 4px 12px;')

        top_layout.addWidget(QLabel("Method:"))
        top_layout.addWidget(self.method_combo)
        top_layout.addSpacing(20)
        top_layout.addWidget(self.compute_button)
        top_layout.addWidget(self.remove_button)
        top_layout.addStretch()

        groupbox1_layout.addLayout(top_layout)

        #----------------------------------------------
        self.method_info_browser = QTextBrowser(self)
        self.method_info_browser.setOpenExternalLinks(True)
        self.method_info_browser.setMinimumHeight(100)
        self.method_info_browser.setStyleSheet("""
            QTextBrowser {
                background: #fafafa;
                border: 1px solid #d0d0d0;
                padding: 6px;
            }
        """)

        groupbox1_layout.addWidget(self.method_info_browser)

        #----------------------------------------------
        self.params_stack = QStackedWidget(self)

        self.params_stack.addWidget(self._build_butter_page())
        self.params_stack.addWidget(self._build_lanczos_page())
        self.params_stack.addWidget(self._build_fir_page())
        self.params_stack.addWidget(self._build_savgol_page())

        groupbox1_layout.addWidget(self.params_stack)

        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1, stretch=1)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()
        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas, stretch=3)

        #----------------------------------------------
        save_layout = QHBoxLayout()

        self.saved_filter_combo = QComboBox(self)
        self.saved_filter_combo.setMinimumWidth(360)

        self.save_button = QPushButton("Save filtered series", self)
        self.close_button = QPushButton("Close", self)
        self.save_button.setStyleSheet('padding: 4px 12px;')
        self.close_button.setStyleSheet('padding: 4px 12px;')

        save_layout.addStretch()
        save_layout.addWidget(QLabel("Filter to save:"))
        save_layout.addWidget(self.saved_filter_combo)
        save_layout.addSpacing(12)
        save_layout.addWidget(self.save_button)
        save_layout.addSpacing(40)
        save_layout.addWidget(self.close_button)

        main_layout.addLayout(save_layout)

        #----------------------------------------------
        self.method_combo.currentTextChanged.connect(self.update_parameter_page)
        self.method_combo.currentTextChanged.connect(self.update_method_info)
        self.method_combo.currentTextChanged.connect(self.delayed_update)

        self.butter_mode_combo.currentTextChanged.connect(self.delayed_update)
        self.butter_mode_combo.currentTextChanged.connect(self.update_butter_mode)
        self.butter_cutoff1_sb.valueChanged.connect(self.delayed_update)
        self.butter_cutoff2_sb.valueChanged.connect(self.delayed_update)
        self.butter_order_sb.valueChanged.connect(self.delayed_update)
        self.lanczos_cutoff_scale_sb.valueChanged.connect(self.delayed_update)
        self.fir_cutoff_sb.valueChanged.connect(self.delayed_update)
        self.fir_numtaps_sb.valueChanged.connect(self.delayed_update)
        self.fir_window_combo.currentTextChanged.connect(self.delayed_update)
        self.sg_cutoff_scale_sb.valueChanged.connect(self.delayed_update)
        self.sg_window_sb.valueChanged.connect(self.delayed_update)
        self.sg_poly_sb.valueChanged.connect(self.delayed_update)

        self.compute_button.clicked.connect(self.compute_filter)
        self.remove_button.clicked.connect(self.remove_last_filter)
        self.save_button.clicked.connect(self.save_series)
        self.close_button.clicked.connect(self.close)

        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_shortcut.activated.connect(self.close)

        self.update_parameter_page(self.method_combo.currentText())
        self.update_method_info(self.method_combo.currentText())
        self.update_butter_mode()
        self._update_original_series()
        self._redraw_plot()

    #---------------------------------------------------------------------------------------------
    def _update_original_series(self):
    
        ts = self._get_series()
    
        self.original_result = {
            "x": ts.time,
            "y": ts.value,
            "label": "Original series",
            "color": self.seriesDict.get("Color", "black")
        }

    #---------------------------------------------------------------------------------------------
    def delayed_update(self):
        self.update_timer.start(250)

    #---------------------------------------------------------------------------------------------
    def update_parameter_page(self, method):

        mapping = {
            self.METHOD_BUTTER: 0,
            self.METHOD_LANCZOS: 1,
            self.METHOD_FIR: 2,
            self.METHOD_SAVGOL: 3
        }

        self.params_stack.setCurrentIndex(mapping.get(method, 0))

    #---------------------------------------------------------------------------------------------
    def update_method_info(self, method):

        if method == self.METHOD_BUTTER:
            html = f"""
            <b>Butterworth filter</b><br>

            <b>Backend call</b><br>
            <code>ts.interp().filter(method="butterworth", cutoff_scale=..., filter_order=...)</code><br><br>

            <b>Backend defaults</b><br>
            <code>fs=1</code>, <code>filter_order=3</code>,
            <code>pad='reflect'</code>, <code>reflect_type='odd'</code>,
            <code>params=(1, 0, 0)</code>, <code>padFrac=0.1</code><br>

            <b>Documentation</b><br>
            <a href="{self.DOC_BUTTER}">pyleoclim.utils.filter.butterworth</a>
            """

        elif method == self.METHOD_LANCZOS:
            html = f"""
            <b>Lanczos filter</b><br>

            <b>Backend call</b><br>
            <code>ts.interp().filter(method="lanczos", cutoff_scale=...)</code><br><br>

            <b>Backend defaults</b><br>
            <code>fs=1</code>, <code>pad='reflect'</code>,
            <code>reflect_type='odd'</code>, <code>params=(1, 0, 0)</code>,
            <code>padFrac=0.1</code><br><br>

            <b>Documentation</b><br>
            <a href="{self.DOC_LANCZOS}">pyleoclim.utils.filter.lanczos</a>
            """

        elif method == self.METHOD_FIR:
            html = f"""
            <b>FIR window filter</b><br>

            <b>Backend call</b><br>
            <code>ts.interp().filter(method="firwin", cutoff_scale=..., numtaps=..., window=...)</code><br><br>

            <b>Backend defaults</b><br>
            <code>numtaps=None</code>, <code>fs=1</code>,
            <code>pad='reflect'</code>, <code>window='hamming'</code>,
            <code>reflect_type='odd'</code>, <code>params=(1, 0, 0)</code>,
            <code>padFrac=0.1</code><br><br>

            <b>Documentation</b><br>
            <a href="{self.DOC_FIR}">pyleoclim.utils.filter.firwin</a>
            """

        elif method == self.METHOD_SAVGOL:
            html = f"""
            <b>Savitzky-Golay filter</b><br>

            <b>Backend call</b><br>
            <code>ts.interp().filter(method="savitzky-golay", cutoff_scale=..., window_length=..., polyorder=...)</code><br><br>

            <b>Backend defaults</b><br>
            <code>window_length=None</code>, <code>polyorder=2</code>,
            <code>deriv=0</code>, <code>delta=1</code>, <code>axis=-1</code>,
            <code>mode='mirror'</code>, <code>cval=0</code><br><br>

            <b>Documentation</b><br>
            <a href="{self.DOC_SAVGOL}">pyleoclim.utils.filter.savitzky_golay</a>
            """

        else:
            html = ""

        self.method_info_browser.setHtml(html)

    #---------------------------------------------------------------------------------------------
    def _build_butter_page(self):
    
        page = QWidget()
        layout = QFormLayout(page)

        #layout.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        #layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.butter_mode_combo = QComboBox()
        self.butter_mode_combo.addItems([self.BUTTER_MODE_LONG, self.BUTTER_MODE_BAND])
        self.butter_mode_combo.setFixedWidth(120)

        self.butter_cutoff1_sb = QDoubleSpinBox()
        self.butter_cutoff1_sb.setDecimals(2)
        self.butter_cutoff1_sb.setRange(2, 1000000)
        self.butter_cutoff1_sb.setValue(5)
        self.butter_cutoff1_sb.setSingleStep(5)
        self.butter_cutoff1_sb.setFixedWidth(120)

        self.butter_cutoff2_sb = QDoubleSpinBox()
        self.butter_cutoff2_sb.setDecimals(2)
        self.butter_cutoff2_sb.setRange(2, 1000000)
        self.butter_cutoff2_sb.setValue(50)
        self.butter_cutoff2_sb.setSingleStep(5)
        self.butter_cutoff2_sb.setFixedWidth(120)
    
        self.butter_order_sb = QSpinBox()
        self.butter_order_sb.setRange(1, 1000)
        self.butter_order_sb.setValue(4)
        self.butter_order_sb.setFixedWidth(120)
   
        layout.addRow("Selection:", self.butter_mode_combo)
        layout.addRow("Period 1:", self.butter_cutoff1_sb)
        layout.addRow("Period 2:", self.butter_cutoff2_sb)
        layout.addRow("Filter order:", self.butter_order_sb)
    
        return page

    #---------------------------------------------------------------------------------------------
    def update_butter_mode(self):
    
        is_bandpass = (self.butter_mode_combo.currentText() == self.BUTTER_MODE_BAND)
        self.butter_cutoff2_sb.setEnabled(is_bandpass)

    #---------------------------------------------------------------------------------------------
    def _build_lanczos_page(self):

        page = QWidget()
        layout = QFormLayout(page)

        layout.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.lanczos_cutoff_scale_sb = QDoubleSpinBox()
        self.lanczos_cutoff_scale_sb.setDecimals(2)
        self.lanczos_cutoff_scale_sb.setRange(2, 1000000)
        self.lanczos_cutoff_scale_sb.setValue(20)
        self.lanczos_cutoff_scale_sb.setSingleStep(10)
        self.lanczos_cutoff_scale_sb.setFixedWidth(120)

        layout.addRow("Period threshold:", self.lanczos_cutoff_scale_sb)

        return page

    #---------------------------------------------------------------------------------------------
    def _build_fir_page(self):
    
        page = QWidget()
        layout = QFormLayout(page)
    
        layout.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.fir_cutoff_sb = QDoubleSpinBox()
        self.fir_cutoff_sb.setDecimals(2)
        self.fir_cutoff_sb.setRange(2, 1000000)
        self.fir_cutoff_sb.setValue(20)
        self.fir_cutoff_sb.setSingleStep(10)
        self.fir_cutoff_sb.setFixedWidth(120)
    
        self.fir_numtaps_sb = QSpinBox()
        self.fir_numtaps_sb.setRange(3, 1000000)
        self.fir_numtaps_sb.setValue(21)
        self.fir_numtaps_sb.setSingleStep(10)
        self.fir_numtaps_sb.setFixedWidth(120)
    
        self.fir_window_combo = QComboBox()
        self.fir_window_combo.addItems([
            "hamming",
            "hann",
            "blackman",
            "bartlett",
            "boxcar"
        ])
        self.fir_window_combo.setCurrentText("hamming")
        self.fir_window_combo.setFixedWidth(120)
    
        layout.addRow("Period cutoff:", self.fir_cutoff_sb)
        layout.addRow("Number of taps:", self.fir_numtaps_sb)
        layout.addRow("Window:", self.fir_window_combo)
    
        return page

    #---------------------------------------------------------------------------------------------
    def _build_savgol_page(self):

        page = QWidget()
        layout = QFormLayout(page)

        layout.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.sg_cutoff_scale_sb = QDoubleSpinBox()
        self.sg_cutoff_scale_sb.setDecimals(2)
        self.sg_cutoff_scale_sb.setRange(0.1, 1000)
        self.sg_cutoff_scale_sb.setSingleStep(1)
        self.sg_cutoff_scale_sb.setSingleStep(10)
        self.sg_cutoff_scale_sb.setFixedWidth(120)

        self.sg_window_sb = QSpinBox()
        self.sg_window_sb.setRange(3, 1000000)
        self.sg_window_sb.setSingleStep(2)
        self.sg_window_sb.setValue(11)
        self.sg_window_sb.setFixedWidth(120)

        self.sg_poly_sb = QSpinBox()
        self.sg_poly_sb.setRange(1, 1000)
        self.sg_poly_sb.setValue(2)
        self.sg_poly_sb.setSingleStep(1)
        self.sg_poly_sb.setFixedWidth(120)

        layout.addRow("Smoothing scale:", self.sg_cutoff_scale_sb)
        layout.addRow("Window length:", self.sg_window_sb)
        layout.addRow("Polynomial order:", self.sg_poly_sb)

        return page

    #---------------------------------------------------------------------------------------------
    def _get_series(self):

        self.seriesDict = self.item.data(0, Qt.ItemDataRole.UserRole)
        self.xName = self.seriesDict['X']
        self.yName = self.seriesDict['Y']

        series = self.seriesDict['Series']
        series = series.groupby(series.index).mean()

        return pyleo.Series(
            time=series.index.to_numpy(),
            value=series.to_numpy(),
            verbose=False
        )

    #---------------------------------------------------------------------------------------------
    def compute_filter(self):
    
        try:
            ts = self._get_series()
            self._update_original_series()
    
            method = self.method_combo.currentText()

            #-------------------------------
            if method == self.METHOD_BUTTER:
            
                mode = self.butter_mode_combo.currentText()
                cutoff1 = self.butter_cutoff1_sb.value()
                cutoff2 = self.butter_cutoff2_sb.value()
                order = self.butter_order_sb.value()
            
                ts_reg = ts.interp()
            
                if mode == self.BUTTER_MODE_LONG:
           
                    MIN_PERIOD = 2.1  # marge de sécurité
                    
                    if cutoff1 <= MIN_PERIOD:
                        raise ValueError(
                            f"Cutoff period must be > {MIN_PERIOD} sampling steps (Nyquist limit)."
                        )
                    
                    fc = 1.0 / cutoff1
                    
                    if not (0 < fc < 0.5):
                        raise ValueError(
                            f"Invalid cutoff: P={cutoff1} → f={fc:.6g}. Must satisfy 0 < f < 0.5."
                        )
                    
                    filtered = ts_reg.filter(
                        method="butterworth",
                        cutoff_scale=cutoff1,
                        filter_order=order
                    )
           
                    label = f"Butterworth | long periods | P={cutoff1} | order={order}"
           
                elif mode == self.BUTTER_MODE_BAND:
          

                    MIN_PERIOD = 2.1
                    
                    p_short = min(cutoff1, cutoff2)
                    p_long = max(cutoff1, cutoff2)
                    
                    if p_short <= MIN_PERIOD or p_long <= MIN_PERIOD:
                        raise ValueError(
                            f"Cutoff periods must be > {MIN_PERIOD} sampling steps (Nyquist limit)."
                        )
                    
                    if p_short == p_long:
                        raise ValueError("The two periods must be different.")
                    
                    f1 = 1.0 / p_long   # basse fréquence
                    f2 = 1.0 / p_short  # haute fréquence
                    
                    if not (0 < f1 < f2 < 0.5):
                        raise ValueError(
                            f"Invalid band: P=[{p_short}, {p_long}] → f=[{f1:.6g}, {f2:.6g}] "
                            "Must satisfy 0 < f1 < f2 < 0.5."
                        )
                    
                    filtered = ts_reg.filter(
                        method="butterworth",
                        cutoff_scale=[p_short, p_long],
                        filter_order=order
                    )
          
                    label = f"Butterworth | period band | P=[{p_short}, {p_long}] | order={order}"

            #-------------------------------
            elif method == self.METHOD_LANCZOS:
    
                cutoff = self.lanczos_cutoff_scale_sb.value()
    
                filtered = ts.interp().filter(
                    method="lanczos",
                    cutoff_scale=cutoff
                )
   
                label = f"Lanczos | long periods | P={cutoff}"
    
            #-------------------------------
            elif method == self.METHOD_FIR:
            
                period = self.fir_cutoff_sb.value()
                numtaps = self.fir_numtaps_sb.value()
                window = self.fir_window_combo.currentText()
            
                if period <= 2:
                    raise ValueError("Cutoff period must be > 2 sampling steps.")
            
                filtered = ts.interp().filter(
                    method="firwin",
                    cutoff_scale=period,
                    numtaps=numtaps,
                    window=window
                )
            
                label = f"FIR | long periods | P={period} | numtaps={numtaps} | window={window}"

            #-------------------------------
            elif method == self.METHOD_SAVGOL:
    
                cutoff = self.sg_cutoff_scale_sb.value()
                window = self.sg_window_sb.value()
                poly = self.sg_poly_sb.value()
    
                if window % 2 == 0:
                    window += 1
                if poly >= window:
                    poly = window - 1
    
                filtered = ts.interp().filter(
                    method="savitzky-golay",
                    cutoff_scale=cutoff,
                    window_length=window,
                    polyorder=poly
                )
   
                label = f"Savitzky-Golay | smoothing scale={cutoff} | window={window} | poly={poly}"
    
            #-------------------------------
            else:
                return
    
            result = {
                "x": filtered.time,
                "y": filtered.value,
                "label": label,
                "color": generate_color()
            }
    
            self.filter_results.append(result)
            self.saved_filter_combo.addItem(label)
            self.saved_filter_combo.setCurrentIndex(len(self.filter_results) - 1)
    
            self._redraw_plot()
    
        except Exception as e:
            self._redraw_plot()
            QMessageBox.warning(self, "Frequency filter", str(e))

    #---------------------------------------------------------------------------------------------
    def _redraw_plot(self):
    
        ax = self.interactive_plot.axs[0]
        ax.clear()
        self.interactive_plot.reset()
    
        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)

        # Original series: always displayed, never saved
        if self.original_result is not None:
            line1, = ax.plot(
                self.original_result["x"],
                self.original_result["y"],
                linewidth=self.seriesWidth,
                color=self.original_result["color"],
                label=self.original_result["label"]
            )
            points1 = ax.scatter(
                self.original_result["x"],
                self.original_result["y"],
                color=self.original_result["color"],
                s=6,
                marker='o',
                visible=False
            )
            ax.line_points_pairs.append((line1, points1))
    
        # Filtered results
    
        # Filtered results
        for result in self.filter_results:
            line, = ax.plot(
                result["x"],
                result["y"],
                linewidth=self.seriesWidth,
                color=result["color"],
                label=result["label"]
            )
            points = ax.scatter(
                result["x"],
                result["y"],
                s=6,
                marker='o',
                color=result["color"],
                visible=False
            )
            ax.line_points_pairs.append((line, points))            
    
        legend = ax.legend()
        for legend_line, ax_line in zip(legend.get_lines(), ax.get_lines()):
            legend_line.set_picker(5)
            ax.map_legend_to_line[legend_line] = ax_line
    
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)
        ax.autoscale()
    
        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def remove_last_filter(self):

        if not self.filter_results:
            return

        self.filter_results.pop()

        self.saved_filter_combo.clear()
        for result in self.filter_results:
            self.saved_filter_combo.addItem(result["label"])

        self._redraw_plot()

    #---------------------------------------------------------------------------------------------
    def save_series(self):

        index = self.saved_filter_combo.currentIndex()

        if index < 0:
            return

        result = self.filter_results[index]

        series_Id = generate_Id()

        history = f"Frequency filter: {result['label']}"
        history += f'<BR>---> series <i><b>{series_Id}</b></i>'

        filtered_seriesDict = {
            "Id": series_Id,
            "Type": "Series freq. filtered",
            "Name": result["label"],
            "X": self.xName,
            "Y": self.yName,
            "Color": result["color"],
            "Date": datetime.datetime.now().strftime("Created %Y/%m/%d %H:%M:%S"),
            'History': append_to_htmlText(self.seriesDict['History'], history),
            'Comment': '',
            "Series": pd.Series(result["y"], index=result["x"])
        }

        position = self.item.parent().indexOfChild(self.item)

        self.add_item_tree_widget(
            self.item.parent(),
            filtered_seriesDict,
            position + 1
        )

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):

        self.open_frequencyFilterWindows.pop(self.Id, None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == '__main__':

    def handle_item(parent, item, position=None):
        print('handle', parent, item, position)

    app = QApplication([])

    x = np.linspace(1, 200, 400)
    y = np.sin(2 * np.pi * x / 20) + 0.4 * np.sin(2 * np.pi * x / 50)
    series = pd.Series(y, index=x)

    seriesDict = {
        'Id': 'abcd',
        'Type': 'Serie',
        'Name': 'Test',
        'X': 'Time',
        'Y': 'Signal',
        'Series': series,
        'Color': generate_color(),
        'Date': datetime.datetime.now().strftime('Created %Y/%m/%d at %H:%M:%S'),
        'Comment': '',
        'History': ''
    }
    item = QTreeWidgetItem()
    item.setData(0, Qt.ItemDataRole.UserRole, seriesDict)

    parent_item = QTreeWidgetItem()
    parent_item.addChild(item)

    Id_frequencyFilterWindow = '1234'
    open_frequencyFilterWindows = {}

    frequencyFilterWindow = computeFrequencyFilterWindow(
        Id_frequencyFilterWindow,
        open_frequencyFilterWindows,
        item,
        handle_item,
    )
    open_frequencyFilterWindows[Id_frequencyFilterWindow] = frequencyFilterWindow
    frequencyFilterWindow.show()

    sys.exit(app.exec())
