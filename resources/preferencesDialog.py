
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

class preferencesDialog(QDialog):

    def __init__(self, on_font_changed, on_custom_tooltip_changed, parent=None):
        super().__init__(parent)
        self.on_font_changed = on_font_changed
        self.on_custom_tooltip_changed = on_custom_tooltip_changed

        self.setWindowTitle("Preferences")
        self.setMinimumSize(400, 200)

        layout = QVBoxLayout(self)

        settings = QSettings("MyPythonApps", "PyAnalySeries")

        size = settings.value("ui/fontSize", QApplication.instance().font().pointSize(), type=int)

        self.cb_tooltip = QCheckBox("Enable custom tooltip")
        self.cb_tooltip.setChecked(settings.value("ui/customTooltipEnabled", True, type=bool))
        self.cb_tooltip.toggled.connect(self.on_custom_tooltip_toggled)

        row = QHBoxLayout()
        row.addWidget(QLabel("Font size"))

        self.spin = QSpinBox()
        self.spin.setFixedWidth(50)
        self.spin.setRange(8, 20)
        self.spin.setValue(settings.value("ui/fontSize", QApplication.instance().font().pointSize(), type=int))
        self.spin.valueChanged.connect(self.on_font_changed)

        row.addWidget(self.spin)
        row.addStretch()

        layout.addWidget(self.cb_tooltip)
        layout.addLayout(row)
        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def on_custom_tooltip_toggled(self, enabled: bool):
        settings = QSettings("MyPythonApps", "PyAnalySeries")
        settings.setValue("ui/customTooltipEnabled", enabled)
    
        self.on_custom_tooltip_changed(enabled)


