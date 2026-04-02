
### Shortcuts 

#### Icon : <img src="resources/PyAnalySeries_icon.svg" alt="shortcut icon" width="80" />

#### Shortcut on Linux :
* Copy the `misc/PyAnalySeries.desktop` file to your Desktop, and make change to specify YOURLOGIN
* Make change in the `PyAnalySeries.sh` file to specify the anaconda installation directory
* Set an icon on the shorcut by choosing the `resources/PyAnalySeries_icon.png` file as icon

#### Shortcut on MacOS :
* Use Automator tool to set a shortcut (choose new application and execute shell)
* Copy in the shell the PyAnalySeries.sh file content with correct anaconda path
* Save as an application in your Desktop directory
* Set an icon by pressing **⌘ + I** on the shorcut created and drag the `resources/PyAnalySeries_icon.svg` file on the top icon 

#### Shortcut on Windows
* Right-click on Desktop → **New → Text Document**
* Rename to `run_pyanalyseries.bat` (⚠️ ensure `.bat`, not `.txt`)
* Edit the file and paste:
  ```@echo off
         call conda activate env_PyAnalySeries
         cd /d C:\Users\YOUR_USERNAME\PyAnalySeries
         python PyAnalySeries.py
         pause
  ```
* Save the file
* Right-click the `.bat` file → **Create shortcut**
* Move the shortcut to Desktop
* Double-click the shortcut to launch PyAnalySeries
* Windows does **not support SVG icons** → convert to `.ico`
* Right-click shortcut → **Properties → Change Icon**
* Select your `.ico` file
