'First message dialog'
ret = MsgBox("This script will update your Inkscape 0.47/0.48 installation"+chr(13)+"to use latest UniConvertor 1.1.5 features.",65, "Inkscape patch")
If ret=2 Then
    ret = MsgBox("Patch script is terminated!",48, "Exit")
    Wscript.Quit 
End If

'Select folder dialog'
Const WINDOW_HANDLE = 0
Const SHOW_EDITBOX = &H0010
Const VALIDATION = &H0020
Const DESKTOP = 0
Set objShell = CreateObject("Shell.Application")
Set objFolder = objShell.BrowseForFolder(WINDOW_HANDLE, _
    "Please select Inkscape installation folder"+chr(13)+"(usually in %Program Files% folder):", _
    SHOW_EDITBOX + VALIDATION, DESKTOP)


If objFolder Is Nothing Then
    ret = MsgBox("Patch script is terminated!",48, "Exit")
    Wscript.Quit
End If
   
Dim sPath, target1, target2, source1, source2 
sPath = objFolder.self.Path
source1 = "uniconv-ext.py"
source2 = "uniconv_output.py"
targetDir= sPath+"\share\extensions\"
target1 = targetDir + source1
target2 = targetDir + source2


Dim fso
Set fso = CreateObject("Scripting.FileSystemObject")

If (fso.FileExists(target1)) And (fso.FileExists(target2)) Then
      fso.CopyFile source1, targetDir
      fso.CopyFile source2, targetDir
Else
    ret = MsgBox("Target files are not found in folder: "+sPath+chr(13)+ _
    " Check your Inkscape installation folder! Patch script is terminated.",48, "Exit")
    Wscript.Quit
End If

ret=MsgBox("Inkscape installation is successfully patched."+chr(13)+"Enjoy new UniConvertor 1.1.5 features!",65, "Inkscape patch")

Wscript.Quit
