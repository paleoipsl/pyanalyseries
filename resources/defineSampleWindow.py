from PyQt5.QtWidgets import * 
from PyQt5.QtCore import * 
from PyQt5.QtGui import *

import matplotlib
matplotlib.use("Qt5Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from .misc import *
from .interactivePlot import interactivePlot

import sys
import datetime
import numpy as np
import pandas as pd

from scipy import interpolate
from scipy.integrate import fixed_quad

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class defineSampleWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_sampleWindows, items, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_sampleWindows = open_sampleWindows
        self.items = items
        self.add_item_tree_widget = add_item_tree_widget

        self.item = self.items[0]
        if len(self.items) == 2:
            self.itemRef = self.items[1]
        else: 
            self.itemRef = None
        self.seriesWidth = 0.8
        self.step = 25.0
        self.kind = 'linear' 
        self.integrated = False

        title = 'Define SAMPLE : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters')
        groupbox1_layout = QVBoxLayout()
        groupbox1.setFixedHeight(200)

        rightMargin = 40

        # ===== 
        series_layout = QHBoxLayout()

        self.series_combo_label = QLabel("Sample series :")
        self.series_combo_label.setFixedWidth(120)
        self.series_combo = QComboBox()
        font = QFont("Courier New", 12)
        self.series_combo.setFont(font)
        for n,item in enumerate(self.items):
            seriesDict = item.data(0, Qt.UserRole)
            XName = seriesDict['X']
            YName = seriesDict['Y']
            Id = seriesDict['Id']
            self.series_combo.addItem(f'{n+1} with {Id}: {XName} / {YName}')
        self.series_combo.setCurrentIndex(0)

        series_layout.addWidget(self.series_combo_label)
        series_layout.addWidget(self.series_combo)
        series_layout.addStretch()

        groupbox1_layout.addLayout(series_layout)

        # =====
        self.step_radio = QRadioButton("Sampling with step :")
        self.step_spinbox = QDoubleSpinBox()
        self.step_spinbox.setRange(0, 1000)
        self.step_spinbox.setSingleStep(5)
        self.step_spinbox.setValue(self.step)
        self.step_spinbox.setDecimals(2)
        self.step_spinbox.setFixedWidth(80)

        step_layout = QHBoxLayout()
        step_layout.addWidget(self.step_radio)
        step_layout.addWidget(self.step_spinbox)
        step_layout.addStretch()
        step_layout.setContentsMargins(rightMargin, 0, 0, 0)

        self.xvalues_radio = QRadioButton("Sampling using x values of series :")
        self.xvalues_label = QLabel('None')
        font = QFont("Courier New", 12)
        self.xvalues_label.setFont(font)

        xvalues_layout = QHBoxLayout()
        xvalues_layout.addWidget(self.xvalues_radio)
        xvalues_layout.addWidget(self.xvalues_label)
        xvalues_layout.addStretch()
        xvalues_layout.setContentsMargins(rightMargin, 0, 0, 0)

        self.group = QButtonGroup(self)
        self.group.addButton(self.step_radio)
        self.group.addButton(self.xvalues_radio)

        groupbox1_layout.addLayout(step_layout)
        groupbox1_layout.addLayout(xvalues_layout)

        if self.itemRef:
            self.xvalues_radio.setChecked(True)
            self.seriesRefDict = self.itemRef.data(0, Qt.UserRole)
            self.seriesRef_XName = self.seriesRefDict['X']
            self.seriesRef_YName = self.seriesRefDict['Y']
            self.seriesRef_Id = self.seriesRefDict['Id']
            self.xvalues_label.setText(f'2 with {self.seriesRef_Id} : {self.seriesRef_XName} / {self.seriesRef_YName}')
            self.sample_from_xvalues = True 
        else:
            self.step_radio.setChecked(True)
            self.xvalues_radio.setEnabled(False)
            self.xvalues_label.setEnabled(False)
            self.sample_from_xvalues = False

        # ===== 
        kind_layout = QHBoxLayout()
        label_s2 = QLabel('Kind of interpolation :')
        self.kind_dropdown = QComboBox()
        self.kind_dropdown.addItems([
             'nearest', 'zero', 'linear', 'quadratic', 'cubic'
        ])
        self.kind_dropdown.setFixedWidth(100)
        self.kind_dropdown.setCurrentText(self.kind)
        kind_layout.addWidget(label_s2)
        kind_layout.addWidget(self.kind_dropdown)
        kind_layout.addStretch()
        kind_layout.setContentsMargins(rightMargin, 0, 0, 0)

        integrated_layout = QHBoxLayout()
        label_s3 = QLabel('Integration :')
        self.integrated_checkbox = QCheckBox()
        self.integrated_checkbox.setChecked(self.integrated)
        integrated_layout.addWidget(label_s3)
        integrated_layout.addWidget(self.integrated_checkbox)
        integrated_layout.addStretch()
        integrated_layout.setContentsMargins(rightMargin, 0, 0, 0)

        groupbox1_layout.addLayout(kind_layout)
        groupbox1_layout.addLayout(integrated_layout)
        groupbox1_layout.addStretch()

        # ===== 
        groupbox1.setLayout(groupbox1_layout)
        main_layout.addWidget(groupbox1)

        #----------------------------------------------
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_value)

        self.step_spinbox.editingFinished.connect(self.check_value_step)
        self.step_radio.toggled.connect(self.delayed_update)
        self.xvalues_radio.toggled.connect(self.delayed_update)
        self.kind_dropdown.currentIndexChanged.connect(self.delayed_update)
        self.integrated_checkbox.stateChanged.connect(self.delayed_update)

        self.series_combo.currentIndexChanged.connect(self.series_change)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()
        self.myplot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        style = "padding: 4px 12px;"
        self.saveSample_button = QPushButton("Save sample", self)
        self.saveSample_button.setStyleSheet(style)
        self.saveSample_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.saveSampleAndSeriesSampled_button = QPushButton("Save sample and series sampled", self)
        self.saveSampleAndSeriesSampled_button.setStyleSheet(style)
        self.close_button = QPushButton("Close", self)
        self.close_button.setStyleSheet(style)
        button_layout.addStretch()

        saveClose_layout = QVBoxLayout()
        saveClose_layout.addWidget(self.saveSample_button)
        saveCloseLine_layout = QHBoxLayout()
        saveCloseLine_layout.addWidget(self.saveSampleAndSeriesSampled_button)
        saveCloseLine_layout.addWidget(self.close_button)
        saveClose_layout.addLayout(saveCloseLine_layout)
        button_layout.addLayout(saveClose_layout)

        main_layout.addLayout(button_layout)

        self.saveSample_button.clicked.connect(self.saveSample)
        self.saveSampleAndSeriesSampled_button.clicked.connect(self.saveSampleAndSeriesSampled)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        self.interactive_plot.fig.canvas.setFocus()

        self.status_bar.showMessage('Ready', 5000)

    #---------------------------------------------------------------------------------------------
    def check_value_step(self):
        if self.step_spinbox.value() == 0.0:
            QMessageBox.warning(self, "Invalid Value", "Zero is not allowed.")
            self.step_spinbox.setValue(5)  # Set to a default non-zero value
        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def delayed_update(self):
        self.status_bar.showMessage('Waiting', 1000)
        self.update_timer.start(1000)

    #---------------------------------------------------------------------------------------------
    def update_value(self):

        self.step = self.step_spinbox.value()
        self.kind = self.kind_dropdown.currentText()
        self.sample_from_xvalues = self.xvalues_radio.isChecked()
        self.integrated = self.integrated_checkbox.isChecked()

        xlim = self.interactive_plot.axs[0].get_xlim()
        ylim = self.interactive_plot.axs[0].get_ylim()

        self.interactive_plot.axs[0].clear()
        self.myplot(limits=[xlim,ylim])

    #---------------------------------------------------------------------------------------------
    def series_change(self):

        n = self.series_combo.currentIndex()
        self.item = self.items[n]
        self.itemRef = self.items[n^1]
         
        self.seriesRefDict = self.itemRef.data(0, Qt.UserRole)
        self.seriesRef_XName = self.seriesRefDict['X']
        self.seriesRef_YName = self.seriesRefDict['Y']
        self.seriesRef_Id = self.seriesRefDict['Id']
        self.xvalues_label.setText(f'{(n^1)+1} with {self.seriesRef_Id} : {self.seriesRef_XName} / {self.seriesRef_YName}')

        self.interactive_plot.axs[0].clear()
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def myplot(self, limits=None):

        self.interactive_plot.reset()

        self.seriesDict = self.item.data(0, Qt.UserRole)
        self.xName = self.seriesDict['X']
        self.yName = self.seriesDict['Y']
        self.series = self.seriesDict['Series']
        self.series = self.series.groupby(self.series.index).mean()

        if self.sample_from_xvalues:
            self.seriesRefDict = self.itemRef.data(0, Qt.UserRole)
            self.seriesRef = self.seriesRefDict['Series']
            self.sample_index = self.seriesRef.index
        else:
            index_min = self.series.index.min()
            index_max = self.series.index.max()
            index_min = np.ceil(index_min / self.step) * self.step
            index_max = np.floor(index_max / self.step) * self.step
            self.sample_index = np.arange(index_min, index_max + self.step, self.step)

        ax = self.interactive_plot.axs[0]

        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)
        ax.autoscale()

        seriesSampled = self.sample(self.series, self.sample_index, self.kind, integrated=self.integrated, ax=ax)
        seriesColor = self.seriesDict['Color']

        line1, = ax.plot(self.series.index, self.series.values, color=seriesColor, linewidth=self.seriesWidth, label='Original')
        points1 = ax.scatter(self.series.index, self.series.values, s=5, marker='o', color=seriesColor, visible=False)
        ax.line_points_pairs.append((line1, points1))
        
        line2, = ax.plot(seriesSampled.index, seriesSampled.values, color='black', linewidth=self.seriesWidth, alpha=0.4, label='Sampled')
        points2 = ax.scatter(seriesSampled.index, seriesSampled.values, s=5, marker='o', color='black', alpha=0.4, visible=False)
        ax.line_points_pairs.append((line2, points2))

        legend = ax.legend()
        data_lines = [line for line in ax.get_lines() if not is_axvline(line)]
        for legend_line, ax_line in zip(legend.get_lines(), data_lines):
            legend_line.set_picker(5)
            ax.map_legend_to_line[legend_line] = ax_line

        if limits:
            ax.set_xlim(limits[0])
            ax.set_ylim(limits[1])

        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()

    #---------------------------------------------------------------------------------------------
    def sync_with_item(self, item):
        if item != self.item: return

        self.raise_()

        xlim = self.interactive_plot.axs[0].get_xlim()
        ylim = self.interactive_plot.axs[0].get_ylim()
        self.interactive_plot.axs[0].clear()
        self.myplot(limits=[xlim,ylim])

    #----------------------------------------------------------------------------------
    @staticmethod
    def sample(series, sample_index, kind="linear", integrated=False, ax=None, quad_points=20):
        """
        Interpolates or integrates a time series on specified sample points.
    
        Parameters:
            series (pd.Series): Time series with index as x-values.
            sample_index (np.ndarray): Points where values are interpolated or integrated.
            kind (str): Interpolation type ('linear', 'cubic', etc.).
            integrated (bool): If True, use integration-based sampling.
            ax (matplotlib axis, optional): For visualizing integration intervals.
            quad_points (int): Number of points for fixed quadrature if integrated=True.
    
        Returns:
            pd.Series: Sampled values at specified indices.
        """
    
        # Remove duplicate indices and keep the mean
        series = series.groupby(series.index).mean()
    
        # Restrict to range of data
        x_min, x_max = series.index.min(), series.index.max()
        sample_index = np.array(sample_index)                           # convert list to numpy array
        valid_sample_index = sample_index[(sample_index >= x_min) & (sample_index <= x_max)]
    
        if not integrated:
            # Standard interpolation
            result_series = pd.Series(index=valid_sample_index, dtype=float)
            result_series = result_series.combine_first(series).sort_index()
            result_series = result_series.interpolate(method=kind, limit_direction="both")
            return result_series.loc[valid_sample_index]
        else:
            # Integrated interpolation using fixed_quad
            interpolator = interpolate.interp1d(series.index, series.values, kind=kind, fill_value="extrapolate")
  
            # Compute midpoints between valid sample points
            mids = (valid_sample_index[1:] + valid_sample_index[:-1]) / 2

            # Compute extended edges for first and last interval
            first_edge = valid_sample_index[0] - (mids[0] - valid_sample_index[0])
            last_edge = valid_sample_index[-1] + (valid_sample_index[-1] - mids[-1])
            
            # Combine all edges
            edges = [first_edge] + list(mids) + [last_edge]
            result_index = valid_sample_index  # Each interval is associated with a sample point
 
            # Create full list of intervals and associated result index
            intervals = []
            filtered_index = []
            
            for i in range(len(result_index)):
                a = edges[i]
                b = edges[i + 1]
            
                if a >= x_min and b <= x_max:
                    intervals.append((a, b))
                    filtered_index.append(result_index[i])

            # Perform integration
            integrated_values = []
            for (a, b) in intervals:
                integral_value, _ = fixed_quad(interpolator, a, b, n=quad_points)
                mean_value = integral_value / (b - a)
                integrated_values.append(mean_value)
            
                # Optional: visualize integration interval
                if ax is not None:
                    line1 = ax.axvline(a, color="blue", linestyle="--", alpha=0.4, lw=0.5)
                    line2 = ax.axvline(b, color="blue", linestyle="--", alpha=0.4, lw=0.5)
    
            return pd.Series(data=integrated_values, index=filtered_index)

    #---------------------------------------------------------------------------------------------
    def saveSample(self):
        sample_Id = generate_Id()
        if not self.sample_from_xvalues:
            sampleDict = {
                'Id': sample_Id,
                'Type': 'SAMPLE', 
                'Name': f'Sample every {self.step}' if not self.integrated else f'Sample every {self.step} with integration',
                'Parameters': f'{self.step} ; {self.kind}; {self.integrated}',
                'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
                'Comment': '',
                'History': f'SAMPLE <i><b>{sample_Id}</i></b> with parameters :' + \
                        '<ul>' + \
                        f'<li>Step : {self.step}' + \
                        f'<li>Kind of interpolation : {self.kind}' + \
                        f'<li>Integrated : {self.integrated}' + \
                        '</ul>'
            }
        else:
            sampleDict = {
                'Id': sample_Id,
                'Type': 'SAMPLE', 
                'Name': f'Sample using x values of {self.seriesRef_YName}',
                'Parameters': f'{self.kind} ; {self.integrated}',
                'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
                'History': f'SAMPLE <i><b>{sample_Id}</i></b> with parameters :' + \
                        '<ul>' + \
                        f'<li>X values from {self.seriesRef_Id} : {self.seriesRef_XName} / {self.seriesRef_YName}' + \
                        f'<li>Kind of interpolation : {self.kind}' + \
                        f'<li>Integrated : {self.integrated}' + \
                        '</ul>',
                'Comment': '',
                'XCoords': self.sample_index
            }
        try:
            self.add_item_tree_widget(self.item.parent(), sampleDict)
        except:
            pass 

        return sample_Id

    #---------------------------------------------------------------------------------------------
    def saveSampleAndSeriesSampled(self):
        sample_Id = self.saveSample()

        sampled_Id = generate_Id()
        if not self.sample_from_xvalues:
            if self.integrated:
                textHistory = f'every {self.step} and {self.kind} interpolation with integration'
            else:
                textHistory = f'every {self.step} and {self.kind} interpolation'
        else:
            if self.integrated:
                textHistory = f'using x values from {self.seriesRef_YName} and {self.kind} interpolation with integration'
            else:
                textHistory = f'using x values from {self.seriesRef_YName} and {self.kind} interpolation'

        sampled_seriesDict = self.seriesDict | {'Id': sampled_Id, 
            'Type': 'Series sampled', 
            'Series': self.sample(self.series, self.sample_index, kind=self.kind, integrated=self.integrated),
            'Color': generate_color(exclude_color=self.seriesDict['Color']),
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'History': append_to_htmlText(self.seriesDict['History'], 
                f'Series <i><b>{self.seriesDict["Id"]}</i></b> sampled {textHistory} with SAMPLE <i><b>{sample_Id}</i></b><BR>---> series <i><b>{sampled_Id}</b></i>'),
            'Comment': '',
        }

        try:
            position = self.item.parent().indexOfChild(self.item)
            self.add_item_tree_widget(self.item.parent(), sampled_seriesDict, position+1)
        except:
            pass 

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.open_sampleWindows.pop(self.Id, None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(parent, item):
        print('handle', parent, item)

    app = QApplication([])

    #---------------------------------
    x1 = np.arange(0, 10+0.1, 0.1)
    y1 = np.sin(x1)
    x2 = np.arange(-10, 20+1, 1)
    random_values = np.random.uniform(-10, 20, 10)  # Générer n valeurs entre a et b
    x2 = np.sort(random_values)
    y2 = np.cos(x2)

    #---------------------------------
    np.random.seed(42)
    x1 = np.linspace(0, 10, 500)
    y1 = np.sin(2 * np.pi * x1) + 0.5 * np.sin(10 * np.pi * x1)  # Signal HF
    y1 += np.random.normal(scale=0.1, size=len(y1))  # Add noise

    #x2 = np.linspace(0, 10, 21)
    x2 = [ 1, 1.5, 2, 2.2, 5, 6, 8.5, 9]
    y2 = np.cos(x2)

    #---------------------------------
    series1 = pd.Series(y1, index=x1)

    series1Dict = {'Id': 'abcd', 'X': 'xName', 'Y': 'yName', 'Series': series1, 
            'Color': 'darkorange',
            'Date': '', 'Comment': 'A text', 'History': 'command1 ; command2'}
    item1 = QTreeWidgetItem()
    item1.setData(0, Qt.UserRole, series1Dict)

    #---------------------------------
    series2 = pd.Series(y2, index=x2)

    series2Dict = {'Id': 'abcd', 'X': 'xName', 'Y': 'yName', 'Series': series2, 
            'Color': 'darkorange',
            'Date': '', 'Comment': 'A text', 'History': 'command1 ; command2'}
    item2 = QTreeWidgetItem()
    item2.setData(0, Qt.UserRole, series2Dict)

    #---------------------------------
    items = []
    items.append(item1)
    items.append(item2)

    open_sampleWindows = {}
    Id_sampleWindow = '1234'
    sampleWindow = defineSampleWindow(Id_sampleWindow, open_sampleWindows, items, handle_item)
    open_sampleWindows[Id_sampleWindow] = sampleWindow
    sampleWindow.show()

    sys.exit(app.exec_())

