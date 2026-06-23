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

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineFilterWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_filterWindows, item, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_filterWindows = open_filterWindows
        self.item = item
        self.add_item_tree_widget = add_item_tree_widget

        self.seriesWidth = 0.8
        self.window_size = 9 

        title = 'Define FILTER : ' + self.Id
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
        
        self.window_size_sb = QSpinBox(self)
        self.window_size_sb.setRange(1, 33)
        self.window_size_sb.setSingleStep(2)
        self.window_size_sb.setValue(self.window_size)
        self.window_size_sb.setFixedWidth(50)
        self.window_size_sb.valueChanged.connect(self.update_value)
        self.window_size_sb.lineEdit().setReadOnly(True)

        form_layout.addRow("Moving average window size :", self.window_size_sb)

        #-------------------------------
        groupbox1_layout.addLayout(form_layout)

        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1)

        #----------------------------------------------
        self.interactive_plot = interactivePlot(
            allow_back_x_axis_settings=True,
            allow_back_y_axis_settings=True,
            allow_back_axis_settings=True,
            allow_save_axis_settings=False
        )        

        self.myplot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        style = "padding: 4px 12px;"
        self.saveFilter_button = QPushButton("Save filter", self)
        self.saveFilter_button.setStyleSheet(style)
        self.saveFilter_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.saveFilterAndSeriesFiltered_button = QPushButton("Save filter and series filtered", self)
        self.saveFilterAndSeriesFiltered_button.setStyleSheet(style)
        self.close_button = QPushButton("Close", self)
        self.close_button.setStyleSheet(style)
        button_layout.addStretch()

        saveClose_layout = QVBoxLayout()
        saveClose_layout.addWidget(self.saveFilter_button)
        saveCloseLine_layout = QHBoxLayout()
        saveCloseLine_layout.addWidget(self.saveFilterAndSeriesFiltered_button)
        saveCloseLine_layout.addWidget(self.close_button)
        saveClose_layout.addLayout(saveCloseLine_layout)
        button_layout.addLayout(saveClose_layout)
        
        main_layout.addLayout(button_layout)

        self.saveFilter_button.clicked.connect(self.saveFilter)
        self.saveFilterAndSeriesFiltered_button.clicked.connect(self.saveFilterAndSeriesFiltered)
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

        self.status_bar.showMessage('Ready', 5000)

    #---------------------------------------------------------------------------------------------
    def update_value(self):
        self.window_size = self.window_size_sb.value()

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

        ax = self.interactive_plot.axs[0]

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)

        seriesFiltered = self.moving_average(self.series, window_size=self.window_size)
        seriesColor = self.seriesDict['Color']

        line1, = ax.plot(self.series.index, self.series.values, color=seriesColor, linewidth=self.seriesWidth, label='Original')
        points1 = ax.scatter(self.series.index, self.series.values, s=5, marker='o', color=seriesColor, visible=False)
        ax.line_points_pairs.append((line1, points1))
        
        line2, = ax.plot(seriesFiltered.index, seriesFiltered.values, color='black', linewidth=self.seriesWidth, alpha=0.4, label='Filtered')
        points2 = ax.scatter(seriesFiltered.index, seriesFiltered.values, s=5, marker='o', color='black', alpha=0.4, visible=False)
        ax.line_points_pairs.append((line2, points2))

        legend = ax.legend()
        for legend_line, ax_line in zip(legend.get_lines(), ax.get_lines()):
            legend_line.set_picker(5)
            ax.map_legend_to_line[legend_line] = ax_line

        axis_settings = self.seriesDict.get("AxisSettings")
        self.interactive_plot.apply_axis_settings(ax, axis_settings)

        if limits:
            ax.set_xlim(limits[0])
            ax.set_ylim(limits[1])

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    @staticmethod
    def moving_average(series, window_size=5):
        if window_size == 1:
            result_series = series
        else:
            half_window = window_size // 2
            result_values = np.convolve(series.values, np.ones(window_size), 'valid') / window_size
            adjusted_index = series.index[half_window: -half_window]
            result_series = pd.Series(result_values, index=adjusted_index)
        return result_series

    #---------------------------------------------------------------------------------------------
    def saveFilter(self):
        filter_Id = generate_Id()
        filterDict = {
            'Id': filter_Id,
            'Type': 'FILTER', 
            'Name': f'Moving average {self.window_size} pts', 
            'Parameters': f'{self.window_size}',
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'Comment': '',
            'History': f'FILTER <i><b>{filter_Id}</i></b> with parameters :' + \
                    '<ul>' + \
                    f'<li>Moving average size : {self.window_size}' + \
                    '</ul>'
        }
        try:
            self.add_item_tree_widget(self.item.parent(), filterDict)
        except:
            pass

        return filter_Id

    #---------------------------------------------------------------------------------------------
    def saveFilterAndSeriesFiltered(self):
        filter_Id = self.saveFilter() 

        #series_filtered = self.moving_average(self.series, self.window_size)

        # to keep replicates
        series_XMean = self.moving_average(self.series, self.window_size)
        series = self.seriesDict['Series']
        series_filtered = series_XMean.reindex(series.index)

        filtered_Id = generate_Id()
        filtered_seriesDict = self.seriesDict | {'Id': filtered_Id,
            'Type': 'Series filtered', 
            'Series': series_filtered,
            'Color': generate_color(exclude_color=self.seriesDict['Color']),
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'History': append_to_htmlText(self.seriesDict['History'], 
                f'Series <i><b>{self.seriesDict["Id"]}</i></b> filtered with FILTER <i><b>{filter_Id}</i></b> with a moving average of size {self.window_size}<BR>---> series <i><b>{filtered_Id}</b></i>'),
            'Comment': '',
        }

        try:
            position = self.item.parent().indexOfChild(self.item)
            self.add_item_tree_widget(self.item.parent(), filtered_seriesDict, position+1)
        except:
            pass

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.open_filterWindows.pop(self.Id, None)
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

    open_filterWindows = {}
    Id_filterWindow = '1234'
    filterWindow = defineFilterWindow(Id_filterWindow, open_filterWindows, item, handle_item)
    open_filterWindows[Id_filterWindow] = filterWindow
    filterWindow.show()

    sys.exit(app_exec(app))
