Set WshShell = WScript.CreateObject("WScript.Shell")

If Wscript.Arguments.Count = 0 Then
	arg = ""
Else
	arg = " "+chr(34)+Wscript.Arguments(0)+chr(34)
End If

Command = "pyVMw.exe  -c "+chr(34)+"from uniconvw import uniconvw_run; uniconvw_run();"+chr(34)+arg
     
WshShell.Run Command
