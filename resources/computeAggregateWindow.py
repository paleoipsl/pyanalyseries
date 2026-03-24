from PyQt6.QtWidgets import * 
from PyQt6.QtCore import * 
from PyQt6.QtGui import *

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from .misc import *
from .CustomQTableWidget import CustomQTableWidget
from .interactivePlot import interactivePlot

import sys
import datetime
import numpy as np
import pandas as pd

matplotlib.rcdefaults()

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
class computeAggregateWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, Id, open_aggregateWindows, item, add_item_tree_widget):
        super().__init__()

        self.Id = Id
        self.open_aggregateWindows = open_aggregateWindows
        self.item = item
        self.add_item_tree_widget = add_item_tree_widget

        self.seriesWidth = 0.8

        self.seriesDict = self.item.data(0, Qt.ItemDataRole.UserRole)
        self.xName = self.seriesDict["X"]
        self.yName = self.seriesDict["Y"]
        self.series = self.seriesDict["Series"]
   
        self.series_original = self.series.copy()
        self.data_modified = False

        title = 'Compute Edit / Aggregate / Clean : ' + self.Id
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(800, 600)
       
        self.tabs = QTabWidget()

        #----------------------------------------------
        data_tab = QWidget()
        data_layout = QVBoxLayout()
        self.data_table = CustomQTableWidget()
        self.data_table.setRowCount(len(self.series))
        self.data_table.setColumnCount(2)
        self.data_table.setHorizontalHeaderLabels([self.xName, self.yName])
        replicates = self.series.index.duplicated(keep=False)
        missing_values = self.series.isna().to_numpy()
        self.series = self.series.sort_index()

        for i in range(len(self.series)):

            item_x = QTableWidgetItem(f'{self.series.index[i]:.6f}')
            item_x.setFlags(item_x.flags() & ~Qt.ItemFlag.ItemIsEditable)  # column X not editable
            self.data_table.setItem(i, 0, item_x)

            item_y = QTableWidgetItem(f'{self.series.values[i]:.6f}')      # column Y editable
            self.data_table.setItem(i, 1, item_y)           

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
        self.data_table.resizeColumnsToContents()
        self.data_table.set_italic_headers()
        self.data_table.itemChanged.connect(self.on_item_changed)

        data_layout.addWidget(self.data_table)
        data_tab.setLayout(data_layout)

        #----------------------------------------------
        agg_tab = QWidget()
        agg_layout = QVBoxLayout()

        groupbox1 = QGroupBox("Parameters")
        groupbox1.setFixedHeight(130)
        
        groupbox1_layout = QVBoxLayout()
        
        # ===============================
        # Aggregation method
        # ===============================
        form_layout = QFormLayout()
        
        self.method_dropdown = QComboBox()
        self.method_dropdown.addItems([
            "mean",
            "median",
            "min",
            "max"
        ])
        self.method_dropdown.setCurrentText("mean")
        self.method_dropdown.setFixedWidth(180)
        self.method_dropdown.currentIndexChanged.connect(self.update_method)
        self.method_dropdown.setToolTip(
            "Aggregation operator applied to values sharing the same index."
        )
        
        form_layout.addRow("Aggregation:", self.method_dropdown)
        groupbox1_layout.addLayout(form_layout)
        
        # ===============================
        # Missing values options
        # ===============================
        options_layout = QVBoxLayout()
        
        self.trim_edges_nan_checkbox = QCheckBox("Trim edge NaN values")
        self.trim_edges_nan_checkbox.setChecked(True)
        self.trim_edges_nan_checkbox.setToolTip(
            "Remove NaN values only at the beginning and at the end of the series."
        )
        self.trim_edges_nan_checkbox.stateChanged.connect(self.update_method)
        
        self.drop_internal_nan_checkbox = QCheckBox("Drop internal NaN values before aggregation")
        self.drop_internal_nan_checkbox.setChecked(False)
        self.drop_internal_nan_checkbox.setToolTip(
            "Remove all internal NaN values before aggregation.\n"
            "Use with care because this changes the effective input data."
        )
        self.drop_internal_nan_checkbox.stateChanged.connect(self.update_method)
        
        options_layout.addWidget(self.trim_edges_nan_checkbox)
        options_layout.addWidget(self.drop_internal_nan_checkbox)
        
        groupbox1_layout.addLayout(options_layout)
        
        groupbox1.setLayout(groupbox1_layout)
        agg_layout.addWidget(groupbox1) 

        #----------------------------------------------
        self.interactive_plot = interactivePlot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        agg_layout.addWidget(canvas)

        agg_tab.setLayout(agg_layout)

        #----------------------------------------------
        self.tabs.addTab(data_tab, "Edit data")
        self.tabs.addTab(agg_tab, "Aggregate / Clean")
        self.tabs.setCurrentIndex(1)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        style = "padding: 4px 12px;"
        self.saveSeriesAggregated_button = QPushButton("Save series aggregated", self)
        self.saveSeriesAggregated_button.setStyleSheet(style)
        self.close_button = QPushButton("Close", self)
        self.close_button.setStyleSheet(style)
        button_layout.addStretch()

        saveClose_layout = QVBoxLayout()
        saveCloseLine_layout = QHBoxLayout()
        saveCloseLine_layout.addWidget(self.saveSeriesAggregated_button)
        saveCloseLine_layout.addWidget(self.close_button)
        saveClose_layout.addLayout(saveCloseLine_layout)
        button_layout.addLayout(saveClose_layout)
        
        self.saveSeriesAggregated_button.clicked.connect(self.saveSeriesAggregated)
        self.close_button.clicked.connect(self.close)

        main_layout.addLayout(button_layout)

        #----------------------------------------------
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        exit_shortcut = QShortcut('q', self)
        exit_shortcut.activated.connect(self.close)

        self.interactive_plot.fig.canvas.setFocus()
        self.myplot()

        self.status_bar.showMessage('Ready', 5000)

    #---------------------------------------------------------------------------------------------
    def trim_edge_nan(self, series):
        """
        Remove NaN values only at the start and at the end of the series.
        Keep internal NaN values unchanged.
        """
        if series.empty:
            return series
    
        valid_mask = series.notna()
        if not valid_mask.any():
            return series.iloc[0:0]
    
        first_valid = valid_mask.idxmax()
        last_valid = valid_mask[::-1].idxmax()
    
        return series.loc[first_valid:last_valid]

    #---------------------------------------------------------------------------------------------
    def update_method(self):
    
        method = self.method_dropdown.currentText()
    
        xlim = self.interactive_plot.axs[0].get_xlim()
        ylim = self.interactive_plot.axs[0].get_ylim()
        self.interactive_plot.axs[0].clear()
        self.myplot(limits=[xlim,ylim])

        self.status_bar.showMessage('Updated', 2000)

    #---------------------------------------------------------------------------------------------
    def on_item_changed(self, item):
    
        if item.column() != 1:
            return
    
        row = item.row()
        text = item.text()
    
        try:
            value = parse_real(text)
        except ValueError:
            return
    
        #print(f"Row={row}, Value={value}")

        self.data_table.blockSignals(True)
        item.setText(f"{value:.6f}")
        self.data_table.blockSignals(False)
    
        self.series.iloc[row] = value

        self.data_modified = not self.series.equals(self.series_original)

        self.update_method()

    #---------------------------------------------------------------------------------------------
    def myplot(self, limits=None):
    
        self.interactive_plot.reset()
    
        ax = self.interactive_plot.axs[0]
    
        ax.grid(visible=True, which="major", color="lightgray", linestyle="dashed", linewidth=0.5)
        ax.set_xlabel(self.xName)
        ax.set_ylabel(self.yName)
        ax.autoscale()
    
        # -----------------------------
        # Get values from UI
        # -----------------------------
        self.method = self.method_dropdown.currentText()
        trim_edges = self.trim_edges_nan_checkbox.isChecked()
        drop_internal_nan = self.drop_internal_nan_checkbox.isChecked()
    
        params = [f"method={self.method}"]
        params.append(f"trim_edges={trim_edges}")
        params.append(f"drop_internal_nan={drop_internal_nan}")
        params.append(f"data_modified={self.data_modified}")
        self.parameters = "; ".join(params)
    
        # -----------------------------
        # Prepare input series
        # -----------------------------
        series_to_aggregate = self.series.copy()

        if trim_edges:
            series_to_aggregate = self.trim_edge_nan(series_to_aggregate)
    
        if drop_internal_nan:
            series_to_aggregate = series_to_aggregate.dropna()
    
        # -----------------------------
        # Aggregate
        # -----------------------------
        if series_to_aggregate.empty:
            self.seriesAggregated = series_to_aggregate
        else:
            self.seriesAggregated = series_to_aggregate.groupby(series_to_aggregate.index).agg(self.method)
    
        seriesColor = self.seriesDict["Color"]
    
        # Original series
        line1, = ax.plot(
            self.series.index,
            self.series.values,
            color=seriesColor,
            linewidth=self.seriesWidth,
            label="Original",
        )
        points1 = ax.scatter(
            self.series.index,
            self.series.values,
            s=5,
            marker="o",
            color=seriesColor,
            visible=False,
        )
        ax.line_points_pairs.append((line1, points1))
    
        # Aggregated series
        line2, = ax.plot(
            self.seriesAggregated.index,
            self.seriesAggregated.values,
            color="black",
            linewidth=self.seriesWidth,
            alpha=0.5,
            label=f"Aggregated ({self.method})",
        )
        points2 = ax.scatter(
            self.seriesAggregated.index,
            self.seriesAggregated.values,
            s=8,
            marker="o",
            color="black",
            alpha=0.5,
            visible=False,
        )
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
    def saveSeriesAggregated(self):
    
        aggregated_Id = generate_Id()
        aggregated_seriesDict = self.seriesDict | {
            "Id": aggregated_Id,
            "Type": "Series aggregated",
            "Series": self.seriesAggregated,
            "Color": generate_color(exclude_color=self.seriesDict["Color"]),
            "Date": datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            "History": append_to_htmlText(
                self.seriesDict["History"],
                f'Series <i><b>{self.seriesDict["Id"]}</b></i> aggregated '
                f'with {self.parameters}<BR>---> series <i><b>{aggregated_Id}</b></i>'
            ),
            "Comment": "",
        }
    
        try:
            position = self.item.parent().indexOfChild(self.item)
            self.add_item_tree_widget(self.item.parent(), aggregated_seriesDict, position + 1)
        except:
            pass

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        plt.close()
        self.open_aggregateWindows.pop(self.Id, None)
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

    open_aggregateWindows = {}
    Id_aggregateWindow = '1234'
    aggregateWindow = computeAggregateWindow(Id_aggregateWindow, open_aggregateWindows, item, handle_item)
    open_aggregateWindows[Id_aggregateWindow] = aggregateWindow
    aggregateWindow.show()

    sys.exit(app.exec())
