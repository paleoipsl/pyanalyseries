from resources.qt_compat import *

import sys
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

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
        self.interactive_plot = interactivePlot(
            rows=len(items), 
            cols=1,
            allow_back_x_axis_settings=True,
            allow_back_y_axis_settings=True,
            allow_back_axis_settings=True,
            allow_save_axis_settings=False
        )
        
        main_layout = QVBoxLayout()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        # Grouping per plot
        self.plot_to_group = {}  # {plot_index: group_id}
        self._init_default_plot_groups()

        controls_layout = QHBoxLayout()

        sharex_label = QLabel('Shared horizontal axis :')
        self.sharex_cb = QCheckBox()
        self.sharex_cb.setChecked(self.sharex)

        self.axis_label = QLabel('Axis :')
        self.axis_cb = QComboBox()
        self.axis_cb.setFixedWidth(170)
        self.axis_cb.view().setTextElideMode(Qt.TextElideMode.ElideRight)
        self._fill_axis_cb_with_plots()

        self.in_group_label = QLabel('in group :')
        self.group_cb = QComboBox()
        self._fill_group_numbers()

        self.reset_groups_btn = QPushButton('Reset default')
        self.close_button = QPushButton('Close', self)

        controls_layout.addWidget(sharex_label)
        controls_layout.addWidget(self.sharex_cb)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.axis_label)
        controls_layout.addWidget(self.axis_cb)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(self.in_group_label)
        controls_layout.addWidget(self.group_cb)
        controls_layout.addSpacing(10)
        controls_layout.addWidget(self.reset_groups_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.close_button)

        main_layout.addLayout(controls_layout)

        # signals
        self.sharex_cb.stateChanged.connect(self.update)
        self.sharex_cb.toggled.connect(self._on_sharex_toggled)
        self.axis_cb.currentIndexChanged.connect(self._sync_group_cb_with_plot)
        self.group_cb.currentIndexChanged.connect(self._assign_plot_to_group_from_ui)
        self.reset_groups_btn.clicked.connect(self._reset_default_groups)
        self.close_button.clicked.connect(self.close)

        self._sync_group_cb_with_plot()
        self._on_sharex_toggled(self.sharex_cb.isChecked())
        self.setLayout(main_layout)

        #----------------------------------------------
        close_shortcut = QShortcut(QKeySequenceClose, self)
        close_shortcut.activated.connect(self.close)

        self.myplot()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def _fill_axis_cb_with_plots(self):
        """Combo shows each plot, even if X axis name is identical."""
        self.axis_cb.blockSignals(True)
        self.axis_cb.clear()
        for n, item in enumerate(self.items):
            seriesDict = item.data(0, Qt.ItemDataRole.UserRole)
            xname = seriesDict.get('X', '')
            self.axis_cb.addItem(f"{n+1} : {xname}", n)  # data = plot index
        self.axis_cb.blockSignals(False)

    #---------------------------------------------------------------------------------------------
    def _fill_group_numbers(self):
        import string
        self.group_cb.blockSignals(True)
        self.group_cb.clear()
    
        letters = list(string.ascii_lowercase)
        n = len(self.items)
    
        for k in range(n):
            label = letters[k] if k < len(letters) else f"g{k+1}"
            self.group_cb.addItem(label, k+1)  # backend still int
    
        self.group_cb.blockSignals(False)

    #---------------------------------------------------------------------------------------------
    def _init_default_plot_groups(self):
        """Default behavior: same X axis name => same group."""
        self.plot_to_group = {}
        xname_to_gid = {}
        next_gid = 1
        for n, item in enumerate(self.items):
            seriesDict = item.data(0, Qt.ItemDataRole.UserRole)
            xname = seriesDict.get('X', '')
            if xname not in xname_to_gid:
                xname_to_gid[xname] = next_gid
                next_gid += 1
            self.plot_to_group[n] = xname_to_gid[xname]

    #---------------------------------------------------------------------------------------------
    def _reset_default_groups(self):
        self._init_default_plot_groups()
        self._sync_group_cb_with_plot()
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def _sync_group_cb_with_plot(self):
        plot_index = self.axis_cb.currentData()
        if plot_index is None:
            return
        gid = int(self.plot_to_group.get(int(plot_index), 1))
        for i in range(self.group_cb.count()):
            if int(self.group_cb.itemData(i)) == gid:
                self.group_cb.blockSignals(True)
                self.group_cb.setCurrentIndex(i)
                self.group_cb.blockSignals(False)
                break

    #---------------------------------------------------------------------------------------------
    def _assign_plot_to_group_from_ui(self):
        plot_index = self.axis_cb.currentData()
        gid = self.group_cb.currentData()
        if plot_index is None or gid is None:
            return
        self.plot_to_group[int(plot_index)] = int(gid)
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def _on_sharex_toggled(self, checked: bool):
        # Disable/enable grouping UI when sharex is off
        self.axis_label.setEnabled(checked)
        self.axis_cb.setEnabled(checked)
        self.in_group_label.setEnabled(checked)
        self.group_cb.setEnabled(checked)
        self.reset_groups_btn.setEnabled(checked)
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

            seriesDict = item.data(0, Qt.ItemDataRole.UserRole)

            ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
            ax.set_xlabel(seriesDict['X'])
            ax.set_ylabel(seriesDict['Y'])

            series = seriesDict['Series']
            series = series.groupby(series.index).mean()
            seriesColor = seriesDict['Color']

            ax.line_points_pairs = []
            line, = ax.plot(series.index, series.values, color=seriesColor, linewidth=self.seriesWidth)
            points = ax.scatter(series.index, series.values, s=5, marker='o', color=seriesColor, visible=False)
            ax.line_points_pairs.append((line, points))

            axis_settings = seriesDict.get("AxisSettings")
            self.interactive_plot.apply_axis_settings(ax, axis_settings)

        #-----------------------------------
        if self.sharex:
            group_to_indices = {}
            for n in range(len(self.items)):
                gid = int(self.plot_to_group.get(n, 1))
                group_to_indices.setdefault(gid, []).append(n)

            for idxs in group_to_indices.values():
                if len(idxs) <= 1:
                    continue
                base_ax = self.interactive_plot.axs[idxs[0]]
                for j in idxs[1:]:
                    self.interactive_plot.axs[j].sharex(base_ax)

        #-----------------------------------
        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

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
        'Date': '',
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }
    item1 = QTreeWidgetItem()
    item1.setData(0, Qt.ItemDataRole.UserRole, series1Dict)

    x2 = np.linspace(5, 15, 100)
    y2 = np.cos(x2)
    series2 = pd.Series(y2, index=x2)

    series2Dict = {
        'Id': '222',
        'X': 'x2Name',
        'Y': 'y2Name',
        'Series': series2,
        'Color': 'darkorange',
        'Date': '',
        'Comment': 'A text',
        'History': 'command1 ; command2'
    }
    item2 = QTreeWidgetItem()
    item2.setData(0, Qt.ItemDataRole.UserRole, series2Dict)

    open_displayWindows = {}
    Id_displayWindow = tuple([series1Dict['Id'], series2Dict['Id']])
    displayWindow = displayStackedSeriesWindow(Id_displayWindow, open_displayWindows, [item1, item2])
    open_displayWindows[Id_displayWindow] = displayWindow
    displayWindow.show()

    sys.exit(app_exec(app))
