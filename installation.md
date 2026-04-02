## Installation

### Requirements

- Python ≥ 3.10  
- Conda (Miniconda or Anaconda recommended)  
- macOS, Linux or Windows  

---

### Recommended installation (Conda)

PyAnalySeries supports both **PyQt6** and **PyQt5**.

You should first try installing with **PyQt6** (recommended), and fallback to **PyQt5** if needed (e.g. older macOS such as Mojave).

---

### 1. Clone the repository

```bash
git clone https://github.com/PaleoIPSL/PyAnalySeries.git
cd PyAnalySeries
```

---

### 2. Create environment (PyQt6 – default)

```bash
conda env create -f environment-pyqt6.yml
conda activate env_PyAnalySeries
```

If installation succeeds, run:

```bash
python PyAnalySeries.py
```

---

### 3. Fallback (PyQt5 – compatibility mode)

If the PyQt6 environment fails to install (this may happen on older macOS versions):

```bash
conda env create -f environment-pyqt5.yml
conda activate env_PyAnalySeries
```

Then run:

```bash
python PyAnalySeries.py
```

---

### Notes

- PyQt6 is the **preferred backend** and should be used when available.  
- PyQt5 is maintained for **backward compatibility**.  
- The application uses an internal compatibility layer, so no code changes are required between versions.  

---

### macOS specific note

On some macOS configurations, certain dependencies (e.g. `pyproj`) must be installed via conda-forge to avoid build issues. This is already handled in the provided environment files.

---

### Summary

| Platform / Setup         | Recommended Qt |
|--------------------------|----------------|
| Recent systems           | PyQt6          |
| Older macOS (e.g. 10.x)  | PyQt5          |

---

### Important

If you previously used an older environment, it is recommended to recreate it:

```bash
conda remove --name env_PyAnalySeries --all
conda env create -f environment-pyqt6.yml
```
