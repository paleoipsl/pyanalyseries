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
class computeDetrendWindow(QWidget):

    DOC_DETREND = "https://pyleoclim-util.readthedocs.io/en/latest/core/api.html#pyleoclim.core.series.Series.detrend"

    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_detrendWindows, item, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_detrendWindows = open_detrendWindows
        self.item = item
        self.add_item_tree_widget = add_item_tree_widget

        self.seriesWidth = 0.8

        title = 'Compute DETREND : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(900, 650)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters')

        groupbox1_layout = QVBoxLayout()

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
        groupbox1_layout.addSpacing(8)

        #-------------------------------
        
        # ===============================
        # Main form layout
        # ===============================
        
        form_layout = QFormLayout()
        
        form_layout.setFormAlignment(AlignTop | AlignLeft)
        form_layout.setLabelAlignment(AlignLeft)

        self.method_dropdown = QComboBox()
        self.method_dropdown.addItems(["linear", "constant", "savitzky-golay", "emd"])
        self.method_dropdown.setCurrentText("linear")
        self.method_dropdown.setFixedWidth(200)
        self.method_dropdown.currentIndexChanged.connect(self.update_method)
        
        form_layout.addRow("Detrend method:", self.method_dropdown)
        
        groupbox1_layout.addLayout(form_layout)
       
        # ===============================
        # Preserve mean + EMD n on same line
        # ===============================
        
        options_layout = QHBoxLayout()
        
        self.preserve_mean_checkbox = QCheckBox("Preserve mean")
        self.preserve_mean_checkbox.setChecked(True)
        self.preserve_mean_checkbox.setToolTip(
            "If enabled, the detrended series keeps the original mean value."
        )
        self.preserve_mean_checkbox.stateChanged.connect(self.update_method)
        
        options_layout.addWidget(self.preserve_mean_checkbox)
        
        self.emd_n_label = QLabel("Remove n slowest IMFs:")
        options_layout.addWidget(self.emd_n_label)
        
        self.emd_n_spinbox = QSpinBox()
        self.emd_n_spinbox.setMinimum(1)
        self.emd_n_spinbox.setMaximum(10)  # arbitrary safe default
        self.emd_n_spinbox.setFixedWidth(60)
        self.emd_n_spinbox.setValue(1)
        self.emd_n_spinbox.valueChanged.connect(self.update_method)
        self.emd_n_spinbox.setToolTip(
            "EMD decomposes the signal into Intrinsic Mode Functions (IMFs).\n"
            "The last IMFs correspond to the lowest-frequency components.\n\n"
            "n = 1 removes only the slowest mode (main trend).\n"
            "Higher n removes more low-frequency variability."
        )
        self.emd_n_label.setToolTip(self.emd_n_spinbox.toolTip())
        
        options_layout.addWidget(self.emd_n_spinbox)
        options_layout.addStretch()
        
        groupbox1_layout.addLayout(options_layout)

        #-------------------------------
        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1, stretch=1)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas, stretch=3)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        style = "padding: 4px 12px;"
        self.saveSeriesDetrended_button = QPushButton("Save series detrended", self)
        self.saveSeriesDetrended_button.setStyleSheet(style)
        self.close_button = QPushButton("Close", self)
        self.close_button.setStyleSheet(style)
        button_layout.addStretch()

        saveClose_layout = QVBoxLayout()
        saveCloseLine_layout = QHBoxLayout()
        saveCloseLine_layout.addWidget(self.saveSeriesDetrended_button)
        saveCloseLine_layout.addWidget(self.close_button)
        saveClose_layout.addLayout(saveCloseLine_layout)
        button_layout.addLayout(saveClose_layout)
        
        main_layout.addLayout(button_layout)

        self.saveSeriesDetrended_button.clicked.connect(self.saveSeriesDetrended)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        self.status_bar.setSizeGripEnabled(False)

        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        close_shortcut = QShortcut(QKeySequenceClose, self)
        close_shortcut.activated.connect(self.close)

        self.interactive_plot.fig.canvas.setFocus()
        self.update_method()

        self.status_bar.showMessage('Ready', 5000)

    #---------------------------------------------------------------------------------------------
    def update_method_info(self):

        method = self.method_dropdown.currentText()
        preserve_mean = self.preserve_mean_checkbox.isChecked()

        if method == "linear":
            html = f"""
            <b>linear</b><br>
            Subtracts the result of an ordinary least-squares straight-line fit from the series.<br><br>

            <b>PyAnalySeries call</b><br>
            <code>ts.detrend(method="linear", preserve_mean={preserve_mean})</code><br><br>

            <b>Documentation</b><br>
            <a href="{self.DOC_DETREND}">pyleoclim.core.series.Series.detrend</a>
            """

        elif method == "constant":
            html = f"""
            <b>constant</b><br>
            Subtracts only the mean of the data.<br><br>

            <b>PyAnalySeries call</b><br>
            <code>ts.detrend(method="constant", preserve_mean={preserve_mean})</code><br><br>

            <b>Documentation</b><br>
            <a href="{self.DOC_DETREND}">pyleoclim.core.series.Series.detrend</a>
            """

        elif method == "savitzky-golay":
            html = f"""
            <b>savitzky-golay</b><br>
            Filters the series with a Savitzky-Golay filter, then subtracts the filtered series from the original data.<br><br>

            <b>PyAnalySeries call</b><br>
            <code>ts.detrend(method="savitzky-golay", preserve_mean={preserve_mean}, ...)</code><br><br>

            <b>UI note</b><br>
            This window does not currently expose the additional Savitzky-Golay keyword arguments.<br><br>

            <b>Documentation</b><br>
            <a href="{self.DOC_DETREND}">pyleoclim.core.series.Series.detrend</a>
            """

        elif method == "emd":
            n = self.emd_n_spinbox.value()
            html = f"""
            <b>emd</b><br>
            Empirical Mode Decomposition detrending.<br>
            Pyleoclim documents this method as removing the last mode, assumed to be the trend.<br><br>

            <b>PyAnalySeries call</b><br>
            <code>ts.detrend(method="emd", preserve_mean={preserve_mean}, n={n})</code><br><br>

            <b>UI parameter</b><br>
            <code>n={n}</code>: number of slowest IMFs removed in this interface.<br><br>

            <b>Documentation</b><br>
            <a href="{self.DOC_DETREND}">pyleoclim.core.series.Series.detrend</a>
            """

        else:
            html = ""

        self.method_info_browser.setHtml(html)

    #---------------------------------------------------------------------------------------------
    def update_method(self):
    
        method = self.method_dropdown.currentText()
    
        is_emd = (method == "emd")
    
        self.emd_n_spinbox.setVisible(is_emd)
        self.emd_n_label.setVisible(is_emd)
   
        self.update_method_info()

        self.interactive_plot.axs[0].clear()
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def myplot(self, limits=None):

        self.interactive_plot.reset()

        self.seriesDict = self.item.data(0, Qt.ItemDataRole.UserRole)
        self.xName = self.seriesDict['X']
        self.yName = self.seriesDict['Y']

        self.series_raw = self.seriesDict['Series']
        self.series = self.series_raw.groupby(self.series_raw.index).mean()

        ax = self.interactive_plot.axs[0]

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)
        ax.autoscale()

        ts = pyleo.Series(time=self.series.index.to_numpy(), value=self.series.to_numpy(), verbose=False)

        # Get values from UI
        self.method = self.method_dropdown.currentText()
        preserve_mean = self.preserve_mean_checkbox.isChecked()
        
        params = [f"preserve_mean={preserve_mean}"]
        
        kwargs = {}
        if self.method == "emd":
            n = self.emd_n_spinbox.value()
            params.append(f"n={n}")
            kwargs["n"] = n
        
        # Final parameter string
        self.parameters = "; ".join(params)

        ts_dt = ts.detrend(
            method=self.method,
            preserve_mean=preserve_mean,
            **kwargs
        )

        self.seriesDetrended = pd.Series(ts_dt.value, index=ts_dt.time)

        mean_raw_aligned = self.series.reindex(self.series_raw.index)
        mean_dt_aligned = self.seriesDetrended.reindex(self.series_raw.index)

        self.seriesDetrended_raw = self.series_raw - mean_raw_aligned + mean_dt_aligned

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
    def saveSeriesDetrended(self):

        detrended_Id = generate_Id()

        history = f'Series <i><b>{self.seriesDict["Id"]}</i></b> detrended with method {self.method} ({self.parameters})'
        history += f'<BR>---> series <i><b>{detrended_Id}</b></i>'

        detrended_seriesDict = self.seriesDict | {'Id': detrended_Id,
            'Type': 'Series detrended', 
            'Series': self.seriesDetrended_raw,
            'Color': generate_color(exclude_color=self.seriesDict['Color']),
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'History': append_to_htmlText(self.seriesDict['History'], history),
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
            'Color': generate_color(),
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'Comment': '', 
            'History': ''
    }
    item = QTreeWidgetItem()
    item.setData(0, Qt.ItemDataRole.UserRole, seriesDict)

    open_detrendWindows = {}
    Id_detrendWindow = '1234'
    detrendWindow = computeDetrendWindow(Id_detrendWindow, open_detrendWindows, item, handle_item)
    open_detrendWindows[Id_detrendWindow] = detrendWindow
    detrendWindow.show()

    sys.exit(app_exec(app))
