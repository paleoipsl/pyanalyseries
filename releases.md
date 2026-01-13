 * 6.00 
   * Fixed remaining windows not closing on application exit.
   * Add Pyleoclim
   * New conda environment
   * PyQt5 to PyQt6
 * 5.45
   * Typo fix in defineSinusoidalSeriesWindow
 * 5.44
   * Move display actions into a dedicated Display menu
   * Add a Preferences menu to control font size (persisted via QSettings)
   * Add a Preferences option to control tooltip visibility (persisted via QSettings)
 * 5.43
   * Remove Y-axis inverted (now available via the context menu)
   * Fix missing Date in various examples from resource classes
   * Fix worksheet saving when items are removed in overwrite mode
 * 5.42
   * Add local and global autoscale
   * Fix exit handling
 * 5.41
   * Ensure correct file extension based on selected save format
 * 5.40
   * Change Serie to Series in interface, dialogs and code
   * Fix read of boolean values (in define sampling)
 * 5.32
   * Tag before deep change (5.40)
 * 5.31.2
   * Add missing icons
   * Fix Date missing in apply filter, sample, interpolation
 * 5.31.1
   * Fix History in define Interpolation
 * 5.31
   * Add Date as field for items (save in WS, handle existing or not)
   * Improve History texts
   * Add Date as field for items (save in WS, handle existing or not)
   * Improve History texts
   * Modify interactivePlot :  
       - to add context menu on axis to choose invert, linear, log display
       - to add context menu on plot to save figure
   * Handle missing values when import serie
 * 5.30
   * Add timestamp when saving
   * Fix synchronisation item lost from 5.26 
   * Allow readonly on ID column
   * Keep existing sheetnames when saving WS
 * 5.29
   * Fix import data when number of columns is not consistent.
 * 5.28
   * Add 'Create / Sinusoidal Serie' with the defineSinusoidalSerieWindow class
   * Change some parameters input as float in defineInsolationAstroSerieWindow
 * 5.27
   * Fix saved status when items are modified
 * 5.26
   * Issue #18 Control saving WorkSheet individually
   * Issue #17 Exit sequence with control of unsaved worksheets
   * Issue #16 Align vertical axis in defineInterpolationWindown with Z
   * Fix saved status when items are pasted
 * 5.25
   * Fix alternating row colors and selections
   * Use last dir when creating new worksheet
   * Fix height of parameters in defineSampleWindow
 * 5.24
   * Alternating row colors in main window
   * Fix when no WS exist and display windows ask to update item
   * Issue #15 Add 'Save ...' in addition to 'Save and ...'  
   * Issue #14 Change removing connection keeps pointers
 * 5.23
   * Fix save WS when paste an item. 
   * Fix multiple drop items. Not allowed.
 * 5.22
   * Add 'Astronomical solution' in History in defineInsolationAstroSerieWindow 
 * 5.21
   * Issue #10 change to handle the order in the choosen series in Define Samping
   * Issue #9 Fix on zoom behaviour
   * Issue #8 Fix on keeping zoom position in Define Interpolation
   * Issue #7 Add on Wiki a paragraph to detail exporting plots and possible use of Inkscape
 * 5.20
   * inso as standalone module to be installed by a `pip install inso`
   * Add a Shuffle button in defineRandomSerieWindow
 * 5.19
   * Fix omission of Precession parameter when Import serie
 * 5.18
   * Fix in sampling when x values are used (XCoords were not saved)
 * 5.17
   * Force sorting on serie index when import, display data and save
 * 5.16
   * Fix \r when clipboard (copy/paste) is produced from Mac
 * 5.15
   * Fix Display Together and Display Stacked to disallow INTERPOLATION
   * Fix test on monotonic increasing and unique when import pointers
   * Fix colors order (missing, duplicates) with displaySingleSerieWindow
 * 5.14
   * Fix style for buttons
   * Allow empty cells in 1st column when importing series
   * Set headers of QTableWidget
   * Blend colors in QTableWidget
 * 5.13
   * Add last recent dir when open worksheets
   * Fix when xlsx file has no item detected
   * Fix html files
   * Add href links in references for insolation
 * 5.12
   * Fix hide of tooltip when not focus.
   * Add encoding utf-8 for reading html files
 * 5.11
   * Add padding on various buttons.
   * Fix sampling intervals (start and end were missing).
 * 5.1
   * Alpha release 
 * 5.0
   * Beta realease 
