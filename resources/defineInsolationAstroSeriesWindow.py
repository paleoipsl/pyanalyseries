from resources.qt_compat import *

import sys
import datetime
import pandas as pd
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from .misc import *
from .interactivePlot import interactivePlot

from .insolationAstroSeries import *

#=========================================================================================
for key in plt.rcParams.keys():
    if key.startswith('keymap.'):
        plt.rcParams[key] = []

#=========================================================================================
DEFAULT_MIN = -5_000_000
DEFAULT_MAX =  5_000_000

#=========================================================================================
class defineInsolationAstroSeriesWindow(QWidget):
    #---------------------------------------------------------------------------------------------
    def __init__(self, open_insolationAstroSeriesWindow, add_item_tree_widget):
        super().__init__()

        self.app_dir = Path(__file__).resolve().parent.parent

        self.open_insolationAstroSeriesWindow = open_insolationAstroSeriesWindow
        self.add_item_tree_widget = add_item_tree_widget

        title = 'Define Insolation / Astronomical series'
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 1200, 800)
        self.setMinimumSize(1000, 800)
        
        main_layout = QVBoxLayout()

        #----------------------------------------------
        col_layout = QHBoxLayout()

        #----------------------------------------------
        col1_layout = QVBoxLayout()

        #----------------------------------------------
        groupbox1 = QGroupBox('Parameters :')

        form_layout = QFormLayout()

        #-------------------------------
        # Insolation type dropdown
        self.plotType_dropdown = QComboBox()
        self.plotType_dropdown.addItems(PLOT_TYPES)
        self.plotType_dropdown.insertSeparator(4)
        self.plotType_dropdown.setCurrentText("Daily insolation")

        #-------------------------------
        # Astronomical solution dropdown
        self.solutionAstro_dropdown = QComboBox()
        self.solutionAstro_dropdown.addItems(ASTRO_SOLUTIONS)
        self.solutionAstro_dropdown.setCurrentText("Laskar2004")
        
        #-------------------------------
        # Solar constant input
        self.solar_constant_input = QDoubleSpinBox()
        self.solar_constant_input.setRange(1000, 1500)
        self.solar_constant_input.setValue(1365)
        self.solar_constant_input.setSingleStep(5)
        self.solar_constant_input.setDecimals(2)

        #-------------------------------
        # Latitude slider
        self.latitude_input = QDoubleSpinBox()
        self.latitude_input.setRange(-90, 90)
        self.latitude_input.setValue(65)
        self.latitude_input.setSingleStep(5)
        self.latitude_input.setDecimals(2)

        #-------------------------------
        # True longitude #1
        self.trueLongitude1_input = QDoubleSpinBox()
        self.trueLongitude1_input.setRange(0, 360)
        self.trueLongitude1_input.setValue(90)
        self.trueLongitude1_input.setSingleStep(5)
        self.trueLongitude1_input.setDecimals(2)
        self.trueLongitude1_input.valueChanged.connect(self.updateTrueLongitude2Limit)

        #-------------------------------
        # True longitude #2
        self.trueLongitude2_input = QDoubleSpinBox()
        self.trueLongitude2_input.setRange(1, 360)
        self.trueLongitude2_input.setValue(180)
        self.trueLongitude2_input.setSingleStep(5)
        self.trueLongitude2_input.setDecimals(2)

        #-------------------------------
        # Time direction
        self.timeConvention_dropdown = QComboBox()
        self.timeConvention_dropdown.addItems([
            "Past < 0",
            "Past > 0",
        ])
        self.timeConvention_dropdown.setCurrentIndex(0)
        self.t_convention = 1

        #-------------------------------
        # Time inputs (Start, End, Step)
        self.tstart_input = QSpinBox()
        lim1 = -101000                         # Range for Laskar2004
        lim2 = 21000
        self.tstart_input.setRange(min(lim1, lim2), max(lim1, lim2))
        self.tstart_input.setValue(-1000)
        self.tstart_input.setSingleStep(1000)
        self.tstart_input.setToolTip(f"Choose a value between {min(lim1, lim2)} and {max(lim1, lim2)}")
        
        self.tend_input = QSpinBox()
        self.tend_input.setRange(min(lim1, lim2), max(lim1, lim2))
        self.tend_input.setValue(500)
        self.tend_input.setSingleStep(1000)
        self.tend_input.setToolTip(f"Choose a value between {min(lim1, lim2)} and {max(lim1, lim2)}")

        self.tstep_input = QDoubleSpinBox()
        lim1Step = 0.001
        lim2Step = 1000
        self.tstep_input.setRange(lim1Step, lim2Step)
        self.tstep_input.setValue(1)
        self.tstep_input.setSingleStep(1)
        self.tstep_input.setDecimals(3)
        self.tstep_input.setToolTip(f"Choose a value between {lim1Step} and {lim2Step}")

        #-------------------------------
        self.timeUnit_dropdown = QComboBox()
        self.timeUnit_dropdown.addItems([
            "yr",
            "kyr"
        ])
        self.timeUnit_dropdown.setCurrentIndex(1)
        self.timeUnit = self.timeUnit_dropdown.currentText()

        #-------------------------------
        form_layout.addRow("Type :", self.plotType_dropdown)
        form_layout.addRow("Astronomical solution :", self.solutionAstro_dropdown)
        form_layout.addRow("Solar constant [W/m2] :", self.solar_constant_input)
        form_layout.addRow("Latitude [°] :", self.latitude_input)
        form_layout.addRow("True longitude #1 [°] :", self.trueLongitude1_input)
        form_layout.addRow("True longitude #2 [°] :", self.trueLongitude2_input)
        form_layout.addRow("Time direction :", self.timeConvention_dropdown)
        form_layout.addRow("Time unit:", self.timeUnit_dropdown)
        self.label_tstart = QLabel(f"Start [{self.timeUnit}] :")
        form_layout.addRow(self.label_tstart, self.tstart_input)
        self.label_tend = QLabel(f"End [{self.timeUnit}] :")
        form_layout.addRow(self.label_tend, self.tend_input)
        self.label_tstep = QLabel(f"Step [{self.timeUnit}] :")
        form_layout.addRow(self.label_tstep, self.tstep_input)

        #-------------------------------
        groupbox1.setLayout(form_layout)
        col1_layout.addWidget(groupbox1)

        #----------------------------------------------
        col2_layout = QVBoxLayout()

        self.ref = QLabel()
        self.ref.setText(f"Reference : {get_solution_reference('Laskar2004')}")
        self.ref.setFixedWidth(600)
        self.ref.setFixedHeight(80)
        self.ref.setWordWrap(True)
        self.ref.setOpenExternalLinks(True)
        self.ref.setTextInteractionFlags(TextSelectableByMouse | TextBrowserInteraction)

        self.range = QLabel()
        self.range.setText(f"Range : {get_solution_range_label('Laskar2004')}")
        self.range.setFixedWidth(600)
        self.range.setFixedHeight(20)
        self.range.setWordWrap(True)
        self.range.setTextInteractionFlags(TextSelectableByMouse)

        #-----------------------------
        self.image_stack = QStackedWidget()
        self.image_stack.setFixedSize(500, 250)
        
        self.image_label1 = QLabel()
        self.image_label1.setAlignment(AlignCenter)

        textTooltip1 = '''
        The vernal point (γ) is defined as the position of the Sun as seen from Earth at the time of the NH spring equinox.<br>
        The climatic precession angle (ῶ) is the position of the perihelion relative to the vernal point γ.
        '''
        self.image_label1.setToolTip(textTooltip1)
        
        self.image_label2 = QLabel()
        self.image_label2.setAlignment(AlignCenter)
        textTooltip2 = '''
        Seasonal durations are defined by fixed true-longitude intervals, but vary through time due to changes in the Earth's orbital velocity.<br>
        This modulation of time spent within each sector contributes to variations in integrated insolation and thus to orbital-scale climate variability.
        '''
        self.image_label2.setToolTip(textTooltip2)
        
        self.pixmap1 = QPixmap(str(self.app_dir / 'resources' / 'precession_angle.png'))
        self.pixmap2 = QPixmap(str(self.app_dir / 'resources' / 'season_length.png'))
        
        self.image_label1.setPixmap(
            self.pixmap1.scaled(
                500, 250,
                KeepAspectRatio,
                SmoothTransformation
            )
        )
    
        self.image_label2.setPixmap(
            self.pixmap2.scaled(
                500, 250,
                KeepAspectRatio,
                SmoothTransformation
            )
        )

        self.image_stack.addWidget(self.image_label1)
        self.image_stack.addWidget(self.image_label2)

        #-----------------------------
        nav_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("◀")
        self.next_button = QPushButton("▶")

        for button in (self.prev_button, self.next_button):
            button.setFixedSize(22, 22)
            button.setStyleSheet("padding: 0px; font-size: 10px;")
        
        self.prev_button.clicked.connect(self.show_prev_image)
        self.next_button.clicked.connect(self.show_next_image)
        
        nav_layout.addSpacing(250)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()

        #-----------------------------
        col2_layout.addWidget(self.ref)
        col2_layout.addWidget(self.range)
        col2_layout.addSpacing(10)
        col2_layout.addWidget(self.image_stack)
        col2_layout.addLayout(nav_layout)
        col2_layout.addStretch()

        #----------------------------------------------
        col_layout.addLayout(col1_layout)
        col_layout.addLayout(col2_layout)
        col_layout.addStretch()
        main_layout.addLayout(col_layout)

        #----------------------------------------------
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.myplot)

        self.plotType_dropdown.currentIndexChanged.connect(self.plotType_change)
        self.solutionAstro_dropdown.currentIndexChanged.connect(self.solutionAstro_change)
        self.timeUnit_dropdown.currentIndexChanged.connect(self.timeUnit_change)
        self.timeConvention_dropdown.currentIndexChanged.connect(self.timeConvention_change)

        self.solar_constant_input.valueChanged.connect(self.delayed_update)
        self.latitude_input.valueChanged.connect(self.delayed_update)
        self.trueLongitude1_input.valueChanged.connect(self.delayed_update)
        self.trueLongitude2_input.valueChanged.connect(self.delayed_update)
        self.tstart_input.valueChanged.connect(self.delayed_update)
        self.tend_input.valueChanged.connect(self.delayed_update)
        self.tstep_input.valueChanged.connect(self.delayed_update)
        self.timeConvention_dropdown.currentIndexChanged.connect(self.delayed_update)

        #----------------------------------------------
        self.interactive_plot = interactivePlot()

        canvas = FigureCanvas(self.interactive_plot.fig)
        main_layout.addWidget(canvas)

        #----------------------------------------------
        button_layout = QHBoxLayout()

        style = "padding: 4px 12px;"
        self.import_button = QPushButton("Import series", self)
        self.import_button.setStyleSheet(style)
        self.close_button = QPushButton("Close", self)
        self.close_button.setStyleSheet(style)
        button_layout.addStretch()

        button_layout.addWidget(self.import_button)
        button_layout.addSpacing(50)
        button_layout.addWidget(self.close_button)
        main_layout.addLayout(button_layout)

        self.import_button.clicked.connect(self.import_series)
        self.close_button.clicked.connect(self.close)

        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        self.status_bar.setSizeGripEnabled(False)

        main_layout.addWidget(self.status_bar)

        #----------------------------------------------
        self.setLayout(main_layout)

        close_shortcut = QShortcut(QKeySequenceClose, self)
        close_shortcut.activated.connect(self.close)

        self.plotType_change()
        self.myplot()

    #---------------------------------------------------------------------------------------------
    def show_prev_image(self):
        index = self.image_stack.currentIndex()
        count = self.image_stack.count()
        self.image_stack.setCurrentIndex((index - 1) % count)
    
    def show_next_image(self):
        index = self.image_stack.currentIndex()
        count = self.image_stack.count()
        self.image_stack.setCurrentIndex((index + 1) % count)
    
    #---------------------------------------------------------------------------------------------
    def timeConvention_change(self):
   
        v1 = self.tstart_input.value()
        v2 = self.tend_input.value()

        self.tstart_input.blockSignals(True)
        self.tend_input.blockSignals(True)

        self.tstart_input.setValue(-v2)
        self.tend_input.setValue(-v1)

        self.tstart_input.blockSignals(False)
        self.tend_input.blockSignals(False)

        if self.timeConvention_dropdown.currentIndex() == 0:
            self.t_convention = 1   # Past < 0
        else:
            self.t_convention = -1  # Past > 0
    
        if self.timeUnit == 'yr':
            scaleFactor = 1000
        else:
            scaleFactor = 1
    
        lim1, lim2 = get_solution_limits_kyr(self.solutionAstro)
        if lim1 is None:
            lim1 = DEFAULT_MIN
            lim2 = DEFAULT_MAX
        else:
            lim1 *= scaleFactor
            lim2 *= scaleFactor
            if self.t_convention == -1:
                lim1, lim2 = -lim2, -lim1
        self.tstart_input.setRange(lim1, lim2)
        self.tstart_input.setToolTip(f"Choose a value between {lim1} and {lim2}")
        self.tend_input.setRange(lim1, lim2)
        self.tend_input.setToolTip(f"Choose a value between {lim1} and {lim2}")

        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def timeUnit_change(self):

        self.timeUnit = self.timeUnit_dropdown.currentText()
        self.label_tstart.setText(f"Start [{self.timeUnit}] :")
        self.label_tend.setText(f"End [{self.timeUnit}] :")
        self.label_tstep.setText(f"Step [{self.timeUnit}] :")

        if self.timeUnit == 'yr':
            scaleFactor = 1000
        else:
            scaleFactor = 1
       
        lim1, lim2 = get_solution_limits_kyr(self.solutionAstro)
        if lim1 is None:
            lim1 = DEFAULT_MIN
            lim2 = DEFAULT_MAX
        else:
            lim1 *= scaleFactor
            lim2 *= scaleFactor
            if self.t_convention == -1:
                lim1, lim2 = -lim2, -lim1
        self.tstart_input.setRange(lim1, lim2)
        self.tstart_input.setToolTip(f"Choose a value between {lim1} and {lim2}")
        self.tend_input.setRange(lim1, lim2)
        self.tend_input.setToolTip(f"Choose a value between {lim1} and {lim2}")

        value1 = self.tstart_input.value()
        value2 = self.tend_input.value()
        step_lim1 = self.tstep_input.minimum()
        step_lim2 = self.tstep_input.maximum()
        step_value = self.tstep_input.value()

        if self.timeUnit == 'yr':
            value1 = value1 * 1000
            value2 = value2 * 1000
            step = 1000
            step_lim1 = step_lim1 * 1000
            step_lim2 = step_lim2 * 1000
            step_value = step_value * 1000
        else:
            value1 = int(value1 / 1000)
            value2 = int(value2 / 1000)
            step = 1
            step_lim1 = step_lim1 / 1000
            step_lim2 = step_lim2 / 1000
            step_value = step_value / 1000

        self.tstart_input.blockSignals(True)
        self.tstart_input.setValue(value1)
        self.tstart_input.setSingleStep(step)
        self.tstart_input.blockSignals(False)

        self.tend_input.blockSignals(True)
        self.tend_input.setValue(value2)
        self.tend_input.setSingleStep(step)
        self.tend_input.blockSignals(False)

        self.tstep_input.blockSignals(True)
        self.tstep_input.setRange(step_lim1, step_lim2)
        self.tstep_input.setToolTip(f"Choose a value between {step_lim1} and {step_lim2}")
        self.tstep_input.setValue(step_value)
        self.tstep_input.setSingleStep(step)
        self.tstep_input.blockSignals(False)

        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def updateTrueLongitude2Limit(self, value):
        self.trueLongitude2_input.setMinimum(value + 1)

    #---------------------------------------------------------------------------------------------
    def plotType_change(self):

        self.plotType = self.plotType_dropdown.currentText()

        if self.plotType in ["Eccentricity", "Obliquity", "Precession angle", "Precession parameter"]:
            self.solar_constant_input.setEnabled(False)
            self.latitude_input.setEnabled(False)
            self.trueLongitude1_input.setEnabled(False)
            self.trueLongitude2_input.setEnabled(False)
        if self.plotType == "Daily insolation":
            self.solar_constant_input.setEnabled(True)
            self.latitude_input.setEnabled(True)
            self.trueLongitude1_input.setEnabled(True)
            self.trueLongitude2_input.setEnabled(False)
        elif self.plotType == "Integrated insolation between 2 true longitudes":
            self.solar_constant_input.setEnabled(True)
            self.latitude_input.setEnabled(True)
            self.trueLongitude1_input.setEnabled(True)
            self.trueLongitude2_input.setEnabled(True)
        elif self.plotType in ["Caloric summer insolation", "Caloric winter insolation"]:
            self.solar_constant_input.setEnabled(True)
            self.latitude_input.setEnabled(True)
            self.trueLongitude1_input.setEnabled(False)
            self.trueLongitude2_input.setEnabled(False)

        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def solutionAstro_change(self):
    
        self.solutionAstro = self.solutionAstro_dropdown.currentText()
    
        allowed = set(get_allowed_plot_types(self.solutionAstro))
    
        model = self.plotType_dropdown.model()
    
        for i in range(self.plotType_dropdown.count()):
            item = model.item(i)
    
            # Skip separator (None item)
            if item is None:
                continue
    
            text = item.text()

            if text in allowed:
                item.setFlags(item.flags() | ItemIsEnabled)
                item.setToolTip("")  # reset si re-enabled
            else:
                item.setFlags(item.flags() & ~ItemIsEnabled)
                item.setToolTip("Not available for this astronomical solution")

        # Si l'item courant devient invalide → fallback
        current = self.plotType_dropdown.currentText()
        if current not in allowed:
            for pt in PLOT_TYPES:
                if pt in allowed:
                    self.plotType_dropdown.setCurrentText(pt)
                    break
    
        # ---- Gestion des bornes temporelles (inchangée)
        if self.timeUnit == 'yr':
            scaleFactor = 1000
        else:
            scaleFactor = 1
    
        lim1, lim2 = get_solution_limits_kyr(self.solutionAstro)
        if lim1 is None:
            lim1 = DEFAULT_MIN
            lim2 = DEFAULT_MAX
        else:
            lim1 *= scaleFactor
            lim2 *= scaleFactor
            if self.t_convention == -1:
                lim1, lim2 = -lim2, -lim1
        self.tstart_input.setRange(lim1, lim2)
        self.tstart_input.setToolTip(f"Choose a value between {lim1} and {lim2}")
        self.tend_input.setRange(lim1, lim2)
        self.tend_input.setToolTip(f"Choose a value between {lim1} and {lim2}")

        self.ref.setText(f"Reference : {get_solution_reference(self.solutionAstro)}")
        self.range.setText(f"Range : {get_solution_range_label(self.solutionAstro)}")
    
        self.delayed_update()

    #---------------------------------------------------------------------------------------------
    def delayed_update(self):
        self.status_bar.showMessage('Waiting', 1000)
        self.update_timer.start(1000)

    #---------------------------------------------------------------------------------------------
    def myplot(self):
    
        self.plotType = self.plotType_dropdown.currentText()
        self.solutionAstro = self.solutionAstro_dropdown.currentText()
   
        t0 = self.tstart_input.value()
        t1 = self.tend_input.value()
        
        if self.t_convention == -1:  # Past > 0
            t0 = -t0
            t1 = -t1
        
        t_start = min(t0, t1)
        t_end   = max(t0, t1)

        try:
            result = compute_insolation_astro_series(
                plot_type=self.plotType,
                solution=self.solutionAstro,
                solar_constant=self.solar_constant_input.value(),
                latitude=self.latitude_input.value(),
                true_longitude1=self.trueLongitude1_input.value(),
                true_longitude2=self.trueLongitude2_input.value(),
                t_start=t_start,
                t_end=t_end,
                t_step=self.tstep_input.value(),
                time_unit=self.timeUnit
            )
        except Exception as e:
            self.status_bar.showMessage(str(e), 5000)
            return
    
        self.index = result["index"]
        if self.t_convention == -1:
            self.index = -self.index

        self.values = result["values"]
        self.shortName = result["short_name"]
        self.ylabel = result["ylabel"]
    
        ax = self.interactive_plot.axs[0]
        ax.clear()
        self.interactive_plot.reset()
    
        ax.grid(visible=True, which='major', color='lightgray', linestyle='dashed', linewidth=0.5)
    
        color = "darkorange"
        line1, = ax.plot(self.index, self.values, linewidth=0.5, color=color)
        points1 = ax.scatter(self.index, self.values, s=5, marker='o', color=color, visible=False)
        ax.line_points_pairs.append((line1, points1))
    
        ax.set_xlabel(self.timeUnit)
        ax.set_ylabel(self.ylabel)
        ax.autoscale()
    
        self.interactive_plot.fig.canvas.draw()
        self.interactive_plot.fig.canvas.setFocus()
        self.status_bar.showMessage('Updated', 1000)

    #---------------------------------------------------------------------------------------------
    def import_series(self):
    
        self.plotType = self.plotType_dropdown.currentText()
        self.solutionAstro = self.solutionAstro_dropdown.currentText()
    
        history = build_history(
            plot_type=self.plotType,
            solution=self.solutionAstro,
            solar_constant=self.solar_constant_input.value(),
            latitude=self.latitude_input.value(),
            true_longitude1=self.trueLongitude1_input.value(),
            true_longitude2=self.trueLongitude2_input.value(),
        )
    
        series_Id = generate_Id()
        history += f'---> series <i><b>{series_Id}</b></i>'
    
        seriesDict = {
            'Id': series_Id,
            'Type': 'Series',
            'Name': '',
            'X': self.timeUnit,
            'Y': self.shortName,
            'Color': generate_color(),
            'History': history,
            'Date': datetime.datetime.now().strftime("Created %Y/%m/%d at %H:%M:%S"),
            'Comment': '',
            'Series': pd.Series(self.values, index=self.index),
        }
    
        try:
            self.add_item_tree_widget(None, seriesDict)
        except Exception as e:
            self.status_bar.showMessage(str(e), 5000)

    #---------------------------------------------------------------------------------------------
    def closeEvent(self, event):
        self.open_insolationAstroSeriesWindow.pop('123456', None)
        event.accept()

#=========================================================================================
# Example usage
if __name__ == "__main__":

    def handle_item(parent, item):
        print('handle', parent, item)

    app = QApplication([])

    Id_insolationAstroSeriesWindow = '1234'
    open_insolationAstroSeriesWindow = {}

    insolationAstroSeriesWindow = defineInsolationAstroSeriesWindow(open_insolationAstroSeriesWindow, handle_item)
    open_insolationAstroSeriesWindow[Id_insolationAstroSeriesWindow] = defineInsolationAstroSeriesWindow
    insolationAstroSeriesWindow.show()

    sys.exit(app_exec(app))
