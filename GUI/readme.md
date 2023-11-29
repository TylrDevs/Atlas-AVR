## Compilation Guide
Download the AVR repository on your desktop. 

Download Python 3.10.10 { https://www.python.org/downloads/release/python-31010/ 

On installation click `Add Python to Windows Path`{ https://youtu.be/aW_TlaLZny4 0:18 - 0:30 

Once that's complete open CMD then exec the following { first time 

cd (directory_of_your_/GUI/) 

python -m venv .venv 

.venv\Scripts\activate 

python -m pip install pip wheel --upgrade 

python -m pip install -r requirements.txt 

python build.py # edit line 12 to just be `"AVRGUI",`, 

.\dist\AVRGUI.exe ( if you wanna boot instantly ) 

Open `dist/` there should be your new AVRGUI.exe 


## If this is your Second/ ++ time proceed with the following. 

cd (directory_of_your_/GUI/) 

python -m venv .venv 

.venv\Scripts\activate 

python build.py 

Appendix { Extras 

https://www.bellavrforum.org/t/how-to-compile-gui-after-making-changes-to-code/611 
https://datatofish.com/executable-pyinstaller/ 

Note: You can’t have GUI open while it's executing 
