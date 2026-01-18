' Silent launcher for WhisperVoice
' This script launches the application without showing a console window

Set WshShell = CreateObject("WScript.Shell")
ScriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
ProjectDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(ScriptDir)

' Try compiled executable first, fall back to Python script
ExePath = ProjectDir & "\dist\WhisperVoice.exe"
PythonScript = ProjectDir & "\whisper_app.py"

Set fso = CreateObject("Scripting.FileSystemObject")
If fso.FileExists(ExePath) Then
    WshShell.Run """" & ExePath & """", 0, False
ElseIf fso.FileExists(PythonScript) Then
    WshShell.Run "pythonw """ & PythonScript & """", 0, False
Else
    MsgBox "WhisperVoice not found. Please build the application first.", vbExclamation, "WhisperVoice"
End If
