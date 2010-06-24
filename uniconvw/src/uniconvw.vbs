Set WshShell = WScript.CreateObject("WScript.Shell")
Command="pyVMw.exe  -c "+chr(34)+"from uniconvw import uniconvw_run; uniconvw_run();"+chr(34)      
WshShell.Run Command
