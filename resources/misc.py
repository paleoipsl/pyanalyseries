
import uuid
import random
import numpy as np
import pandas as pd

from matplotlib import cm

from PyQt6.QtGui import QColor 

#========================================================================================
def generate_Id():
    return f"Id-{str(uuid.uuid4())[:8].upper()}"

#========================================================================================
def generate_color(exclude_color=None):
    tab20_colors = [QColor(*(int(c * 255) for c in cm.tab20(i)[:3])).name() for i in range(20)]
    if exclude_color in tab20_colors:
        tab20_colors.remove(exclude_color)
    return random.choice(tab20_colors)

#========================================================================================
def blend_colors(color1, color2, ratio=0.5):
    r = round(color1.red() * (1 - ratio) + color2.red() * ratio)
    g = round(color1.green() * (1 - ratio) + color2.green() * ratio)
    b = round(color1.blue() * (1 - ratio) + color2.blue() * ratio)
    return QColor(r, g, b)

#========================================================================================
def append_to_htmlText(text, new_value):
    if text:
        text += "<li>"
    text += new_value
    return text 

#========================================================================================
def addNanList(aList, length=None):
    """
    - Replace '' by np.nan
    - If length is provided: truncate to that length (no trimming logic here)
    - Else: trim trailing NaNs (legacy behavior)
    """
    out = [np.nan if x == '' else x for x in aList]

    if length is not None:
        return out[:length]

    # legacy: trim trailing NaNs
    for i in range(len(out) - 1, -1, -1):
        if not pd.isna(out[i]):
            return out[:i + 1]
    return []

#========================================================================================
def effective_length_from_index(index_list):
    """
    Compute the useful length from index column:
    last row where index is not ''/NaN.
    """
    idx = addNanList(index_list)  # uses legacy trim
    return len(idx)

#========================================================================================
def cleanSpaceList(aList):
    return [x for x in aList if x != '']

#========================================================================================
def is_open(file):
    try:
        # Try to open the file in read/write mode.
        with open(file, "r+") as f:
            return False  # File was opened successfully → not locked
    except IOError:
        return True  # File is likely in use or inaccessible

#========================================================================================
def QLineEdit_check(widget, default: float):
    txt = widget.text().strip()
    # sign or empty
    if txt in ("", "+", "-", "."):
        widget.setText(str(default))
        return
    # comma → point
    if ',' in txt:
        txt = txt.replace(',', '.')
        widget.setText(txt)
    # final test
    try:
        float(txt)
    except ValueError:
        widget.setText(str(default))

#========================================================================================
def is_axvline(line):
    xdata = line.get_xdata()
    ydata = line.get_ydata()

    x_is_constant = (
        len(xdata) == 1 or
        (len(xdata) == 2 and xdata[0] == xdata[1])
    )

    y_covers_full_axis = (
        len(ydata) == 2 and ydata[0] == 0 and ydata[1] == 1
    )

    return x_is_constant and y_covers_full_axis

#========================================================================================
def str_to_bool(s: str) -> bool:
    if s == "True":
        return True
    if s == "False":
        return False
    raise ValueError(f"Invalid boolean string: {s!r}")

#========================================================================================
