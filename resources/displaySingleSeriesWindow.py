from resources.qt_compat import *

import sys
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.ticker import LogLocator, FuncFormatter

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
    def format_limit(self, value):
        if value is None:
            return ""
        #return f"{value:.6g}"
        return f"{value:.3f}".rstrip('0').rstrip('.')

    #---------------------------------------------------------------------------------------------
    def _axis_settings_from_widgets(self):
        def parse_float(widget):
            text = widget.text().strip()
            if text == "":
                return None
            return float(text)
    
        return {
            "xaxis": {
                "type": self.xaxis_type_combo.currentText(),
                "invert": self.xaxis_invert_cb.isChecked(),
                "lim1": parse_float(self.xlim1_edit),
                "lim2": parse_float(self.xlim2_edit),
            },
            "yaxis": {
                "type": self.yaxis_type_combo.currentText(),
                "invert": self.yaxis_invert_cb.isChecked(),
                "lim1": parse_float(self.ylim1_edit),
                "lim2": parse_float(self.ylim2_edit),
            },
        }
    
    #---------------------------------------------------------------------------------------------
    def _set_axis_widgets_from_settings(self, settings):
        settings = settings or {}
    
        xaxis = settings.get("xaxis", {})
        yaxis = settings.get("yaxis", {})
   

        self.xaxis_type_combo.setCurrentText(xaxis.get("type", "linear"))
        self.xaxis_invert_cb.setChecked(bool(xaxis.get("invert", False)))
        self.xlim1_edit.setText(self.format_limit(xaxis.get("lim1")))
        self.xlim2_edit.setText(self.format_limit(xaxis.get("lim2")))
    
        self.yaxis_type_combo.setCurrentText(yaxis.get("type", "linear"))
        self.yaxis_invert_cb.setChecked(bool(yaxis.get("invert", False)))
        self.ylim1_edit.setText(self.format_limit(yaxis.get("lim1")))
        self.ylim2_edit.setText(self.format_limit(yaxis.get("lim2")))

    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_displayWindows, item):
        super().__init__()

        self.Id = Id
        self.open_displayWindows = open_displayWindows
        self.item = item

        self.seriesWidth = 0.8

        self.seriesDict = self.item.data(0, Qt.ItemDataRole.UserRole)
        self.xName = self.seriesDict['X']
        self.yName = self.seriesDict['Y']
        self.series = self.seriesDict['Series']

        title = 'Display series : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        self.tabs = QTabWidget()
        
        #----------------------------------------------
        data_tab = QWidget()
        data_layout = QVBoxLayout()
        self.data_table = CustomQTableWidget()
        self.data_table.setRowCount(len(self.series))

        if 'XOriginalValues' in self.seriesDict:
            self.data_table.setColumnCount(3)
            self.data_table.setHorizontalHeaderLabels(
                [self.xName, self.yName, self.seriesDict['XOriginal']]
            )
        else:
            self.data_table.setColumnCount(2)
            self.data_table.setHorizontalHeaderLabels(
                [self.xName, self.yName]
            )

        replicates = self.series.index.duplicated(keep=False)
        missing_values = self.series.isna().to_numpy()
        self.series = self.series.sort_index()

        for i in range(len(self.series)):
            self.data_table.setItem(i, 0, QTableWidgetItem(str(f'{self.series.index[i]:.6f}')))
            self.data_table.setItem(i, 1, QTableWidgetItem(str(f'{self.series.values[i]:.6f}')))

            if 'XOriginalValues' in self.seriesDict:
                if i < len(self.seriesDict['XOriginalValues']):
                    text = f'{float(self.seriesDict["XOriginalValues"][i]):.6f}'
                else:
                    text = ""
                self.data_table.setItem(i, 2, QTableWidgetItem(text))

            if missing_values[i]:
                base = QColor('peachpuff')
                alt = QColor('white') if i % 2 == 0 else QColor('whitesmoke')
                background_color = blend_colors(base, alt, ratio=0.6)
            elif replicates[i]:
                base = QColor('lemonchiffon')
                alt = QColor('white') if i % 2 == 0 else QColor('whitesmoke')
                background_color = blend_colors(base, alt, ratio=0.6)
            else:
                background_color = QColor('white') if i % 2 == 0 else QColor('whitesmoke')
            self.data_table.item(i, 0).setBackground(background_color)
            self.data_table.item(i, 1).setBackground(background_color)

            if ('XOriginalValues' in self.seriesDict and len(self.seriesDict['XOriginalValues']) == len(self.series)):
                self.data_table.item(i, 2).setBackground(background_color)

        self.data_table.resizeColumnsToContents()
        self.data_table.set_italic_headers()
        self.data_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        data_layout.addWidget(self.data_table)
        data_tab.setLayout(data_layout)
        
        #----------------------------------------------
        stats_tab = QWidget()
        stats_layout = QVBoxLayout()
        stats_table = CustomQTableWidget()
        stats_table.setRowCount(12)
        stats_table.setColumnCount(2)
        stats_table.setHorizontalHeaderLabels(["Stat", "Value"])
        stats = {
            "Number of points": (len(self.series), 'd'),
            "Number of replicates": ((self.series.index.value_counts() > 1).sum(), 'd'),
            "Number of missing": (self.series.isna().sum(), 'd'),
            "Mean": (self.series.mean(), '.6f'),
            "Median": (self.series.median(), '.6f'),
            "Minimum": (self.series.min(), '.6f'),
            "Maximum": (self.series.max(), '.6f'),
            "Standard deviation": (self.series.std(), '.6f'),
            "Quantile 25%": (self.series.quantile(0.25), '.6f'),
            "Quantile 50%": (self.series.quantile(0.50), '.6f'),
            "Quantile 75%": (self.series.quantile(0.75), '.6f'),
            "Inter quartile range (IQR)": (self.series.quantile(0.75) - self.series.quantile(0.25), '.6f'),
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
    
        self.interactive_plot = interactivePlot(
            allow_back_x_axis_settings=True,
            allow_back_y_axis_settings=True,
            allow_back_axis_settings=True,
            allow_save_axis_settings=True
        )
        canvas = FigureCanvas(self.interactive_plot.fig)
        plot_layout.addWidget(canvas)
        self.myplot()

        plot_tab.setLayout(plot_layout)

        #----------------------------------------------
        axis_tab = QWidget()
        axis_layout = QVBoxLayout()
        
        #-------------------------------
        # X axis group
        x_group = QGroupBox("X axis")
        x_form = QFormLayout()
        
        self.xaxis_type_combo = QComboBox()
        self.xaxis_type_combo.addItems(["linear", "log10", "log1-2-5"])
        self.xaxis_type_combo.setMaximumWidth(120)
        
        self.xaxis_invert_cb = QCheckBox("Invert X axis")
       
        self.xlim1_edit = QLineEdit()
        self.xlim2_edit = QLineEdit()
        self.xlim1_edit.setPlaceholderText("auto")
        self.xlim2_edit.setPlaceholderText("auto")
        self.xlim1_edit.setMaximumWidth(120)
        self.xlim2_edit.setMaximumWidth(120)
        self.axis_read_x_button = QPushButton("Read X view")
        self.axis_clear_x_button = QPushButton("Clear X limits")
        
        x_limits_layout = QHBoxLayout()
        x_limits_layout.addWidget(QLabel("Limits:"))
        x_limits_layout.addWidget(self.xlim1_edit)
        x_limits_layout.addWidget(self.xlim2_edit)
        x_limits_layout.addWidget(self.axis_read_x_button)
        x_limits_layout.addWidget(self.axis_clear_x_button)
        x_limits_layout.addStretch()
        
        x_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        x_form.addRow("Scale:", self.xaxis_type_combo)
        x_form.addRow("", self.xaxis_invert_cb)
        x_form.addRow(x_limits_layout)
        
        x_group.setLayout(x_form)
       
        #-------------------------------
        # Y axis group
        y_group = QGroupBox("Y axis")
        y_form = QFormLayout()
        
        self.yaxis_type_combo = QComboBox()
        self.yaxis_type_combo.addItems(["linear", "log10", "log1-2-5"])
        self.yaxis_type_combo.setMaximumWidth(120)
        
        self.yaxis_invert_cb = QCheckBox("Invert Y axis")
        
        self.ylim1_edit = QLineEdit()
        self.ylim2_edit = QLineEdit()
        self.ylim1_edit.setPlaceholderText("auto")
        self.ylim2_edit.setPlaceholderText("auto")
        self.ylim1_edit.setMaximumWidth(120)
        self.ylim2_edit.setMaximumWidth(120)
        self.axis_read_y_button = QPushButton("Read Y view")
        self.axis_clear_y_button = QPushButton("Clear Y limits")
       
        y_limits_layout = QHBoxLayout()
        y_limits_layout.addWidget(QLabel("Limits:"))
        y_limits_layout.addWidget(self.ylim1_edit)
        y_limits_layout.addWidget(self.ylim2_edit)
        y_limits_layout.addWidget(self.axis_read_y_button)
        y_limits_layout.addWidget(self.axis_clear_y_button)
        y_limits_layout.addStretch()
        
        y_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        y_form.addRow("Scale:", self.yaxis_type_combo)
        y_form.addRow("", self.yaxis_invert_cb)
        y_form.addRow(y_limits_layout)

        y_group.setLayout(y_form)
        
        #-------------------------------
        # Buttons
        button_layout_axis = QHBoxLayout()
        self.axis_apply_button = QPushButton("Apply")
        self.axis_read_xy_button = QPushButton("Read XY view")
        self.axis_clear_xy_button = QPushButton("Clear XY limits")
        
        button_layout_axis.addWidget(self.axis_apply_button)
        button_layout_axis.addSpacing(40)
        button_layout_axis.addWidget(self.axis_read_xy_button)
        button_layout_axis.addWidget(self.axis_clear_xy_button)
        button_layout_axis.addStretch()
        
        axis_layout.addWidget(x_group)
        axis_layout.addWidget(y_group)
        axis_layout.addSpacing(10)
        axis_layout.addLayout(button_layout_axis)
        axis_layout.addStretch()
        
        axis_tab.setLayout(axis_layout)

        self.axis_apply_button.clicked.connect(self.apply_axis_settings_from_tab)
        self.axis_read_x_button.clicked.connect(lambda: self.use_current_axis_view(read_x=True))
        self.axis_read_y_button.clicked.connect(lambda: self.use_current_axis_view(read_y=True))
        self.axis_read_xy_button.clicked.connect(lambda: self.use_current_axis_view(read_x=True, read_y=True))
        self.axis_clear_x_button.clicked.connect(lambda: self.clear_axis_limits(clear_x=True))
        self.axis_clear_y_button.clicked.connect(lambda: self.clear_axis_limits(clear_y=True))
        self.axis_clear_xy_button.clicked.connect(lambda: self.clear_axis_limits(clear_x=True, clear_y=True))

        self._set_axis_widgets_from_settings(self.seriesDict.get("AxisSettings"))

        #----------------------------------------------
        info_tab = QWidget()
        info_layout = QVBoxLayout()

        self.textName = QLabel(f"Name : <b>{self.seriesDict['Name']}</b>")

        self.textDate = QLabel(f"Date : {self.seriesDict['Date']}")

        labelHistory = QLabel("History :")
        self.textHistory = QTextEdit()
        self.textHistory.setFixedHeight(self.textHistory.fontMetrics().lineSpacing() * 10)
        self.textHistory.setText(f"<ol><li>{self.seriesDict['History']}</ol>")
        self.textHistory.setReadOnly(True)
        self.textHistory.setFont(QFont("Courier New"))

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
        self.tabs.addTab(axis_tab, "Axis settings")
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

        close_shortcut = QShortcut(QKeySequenceClose, self)
        close_shortcut.activated.connect(self.close)

    #---------------------------------------------------------------------------------------------

        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def validate_axis_settings(self, settings):
    
        for axis_key, axis_label in [("xaxis", "X"), ("yaxis", "Y")]:
    
            axis = settings[axis_key]
    
            lim1 = axis.get("lim1")
            lim2 = axis.get("lim2")
            scale_type = axis.get("type", "linear")
    
            if (lim1 is None) != (lim2 is None):
                QMessageBox.warning(
                    self,
                    "Axis settings",
                    f"{axis_label} limits: both values must be specified."
                )
                return False
    
            if lim1 is None:
                continue
    
            if lim2 <= lim1:
                QMessageBox.warning(
                    self,
                    "Axis settings",
                    f"{axis_label} limits: maximum must be greater than minimum."
                )
                return False
    
            if scale_type in ("log10", "log1-2-5"):
                if lim1 <= 0 or lim2 <= 0:
                    QMessageBox.warning(
                        self,
                        "Axis settings",
                        f"{axis_label} limits: logarithmic axes require positive values."
                    )
                    return False
    
        return True

    #---------------------------------------------------------------------------------------------
    def apply_axis_settings_from_tab(self):
    
        axis_settings = self._axis_settings_from_widgets()
    
        if not self.validate_axis_settings(axis_settings):
            return
    
        ax = self.interactive_plot.axs[0]
    
        self.interactive_plot.apply_axis_settings(ax, axis_settings)
    
        self.seriesDict["AxisSettings"] = axis_settings

    #---------------------------------------------------------------------------------------------
    def use_current_axis_view(self, read_x=False, read_y=False):
    
        ax = self.interactive_plot.axs[0]
    
        current_settings = self.interactive_plot.get_axis_settings(ax)
    
        if read_x and read_y:
            axis_settings = current_settings
        else:
            axis_settings = self._axis_settings_from_widgets()
    
            if read_x:
                axis_settings["xaxis"] = current_settings["xaxis"]
    
            if read_y:
                axis_settings["yaxis"] = current_settings["yaxis"]
    
        self._set_axis_widgets_from_settings(axis_settings)
    
        ax.axis_settings = axis_settings
        self.seriesDict["AxisSettings"] = axis_settings

    #---------------------------------------------------------------------------------------------
    def clear_axis_limits(self, clear_x=False, clear_y=False):
    
        axis_settings = self._axis_settings_from_widgets()
    
        if clear_x:
            axis_settings["xaxis"]["lim1"] = None
            axis_settings["xaxis"]["lim2"] = None
    
        if clear_y:
            axis_settings["yaxis"]["lim1"] = None
            axis_settings["yaxis"]["lim2"] = None
    
        self._set_axis_widgets_from_settings(axis_settings)
    
        ax = self.interactive_plot.axs[0]
        self.interactive_plot.apply_axis_settings(ax, axis_settings)
        self.seriesDict["AxisSettings"] = axis_settings

    #---------------------------------------------------------------------------------------------
    def myplot(self):
       
        self.interactive_plot.reset()

        ax = self.interactive_plot.axs[0]

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)

        seriesDict = self.item.data(0, Qt.ItemDataRole.UserRole)
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

        axis_settings = seriesDict.get("AxisSettings")
        self.interactive_plot.apply_axis_settings(ax, axis_settings)

        ax.figure.canvas.draw()
        ax.figure.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):

        plt.close()

        self.seriesDict['Comment'] = self.textComment.toPlainText()

        try:
            ax = self.interactive_plot.axs[0]
            if hasattr(ax, "axis_settings") and ax.axis_settings:
                self.seriesDict["AxisSettings"] = ax.axis_settings
        except Exception:
            pass

        # if WS has been removed while a Display is active 
        try:
            self.item.setData(0, Qt.ItemDataRole.UserRole, self.seriesDict)
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
    item.setData(0, Qt.ItemDataRole.UserRole, itemDict)

    open_displayWindows = {}
    Id_displayWindow = '1234'
    displayWindow = displaySingleSeriesWindow(Id_displayWindow, open_displayWindows, item)
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app_exec(app))
