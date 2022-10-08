#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

quote(string) {
    return """" string """"
}

get_my_utils_path(filename) {
	PYTHON_UTILS_DIR := "D:\Data\python\projects\note_utils\"
	
	fullpath :=  PYTHON_UTILS_DIR . filename
	fullpath := quote(fullpath)
    return fullpath
}

; window management
;#Up::WinMove A, ,0,0,A_ScreenWidth,(A_ScreenHeight-64)/2
;#Down::WinMove A, ,0,(A_ScreenHeight-64)/2,A_ScreenWidth,(A_ScreenHeight-64)/2

CapsLock & 1:: send ①
CapsLock & 2:: send ②
CapsLock & 3:: send ③
CapsLock & 4:: send ④
CapsLock & 5:: send ⑤
CapsLock & 6:: send ⑥
CapsLock & 7:: send ⑦
CapsLock & 8:: send ⑧
CapsLock & 9:: send ⑨
CapsLock & 0:: send ⑩

; supermemo, 将element转为纯文本
CapsLock & t::send ^+{F12}

; Abbyy ScreenshotReader
#Include %A_Scriptdir%\TrayIcon.ahk
AbbyyScreenReaderOCRText()
{
    TrayIcon_Button("ScreenshotReader.exe", "L")
    sleep, 100
    SendInput, r
}

CapsLock & r::AbbyyScreenReaderOCRText()

CopyPlainText()
{
	clipboard := ""  ; Start off empty to allow ClipWait to detect when the text has arrived.
	send, ^c
	ClipWait, 2, 1 ; wait until clipboard contains data
    clipboard :=  clipboard  ; Convert any copied files, HTML, or other formatted text to plain text.
}

Capslock & c::CopyPlainText()

; 进入spotlight模式，方便进行阅读pacer
Capslock & s::send ^!+P

LookUpDictionary()
{
   Clipboard := "" ; clear clipboard
   Send, ^c ; simulate Ctrl+C (=selection in clipboard)
   ClipWait, 2, 1 ; wait until clipboard contains data
   sleep, 200
   Send, ^!+c
}

Capslock & d:: LookUpDictionary()

; 将剪贴板中的markdown文本转为html，再将html文本放回剪贴板
ClipboardMarkdownToHtml()
{
	fullexec_path := get_my_utils_path("src\markdown2clipboard.pyw")
	RunWait, %fullexec_path%
	ClipWait, 2, 1 ; wait until clipboard contains data
}

Capslock & m:: ClipboardMarkdownToHtml()

N10NotesProcess()
{
	FileSelectFile, SelectedFiles, M3  ; M3 = Multiselect existing files.
	;MsgBox, The user selected the following:`n%SelectedFiles%
	if (SelectedFiles = "")
	{
    		return
	}
	else
	{
		files := quote(SelectedFiles)	
		;MsgBox, The quoted string:`n%files%
		
		fullexec_path := get_my_utils_path("src\n10_note_for_ahk.pyw")
		RunWait, %fullexec_path% %files%
	}
}

CapsLock & p:: N10NotesProcess()

SendMarkdownToOnenote()
{
	FileSelectFile, SelectedFile, 3, , , Markdown Documents (*.md)
	if (SelectedFile = "")
	{
		return
	}
	else
	{
		 ;MsgBox, The user selected the following:`n%SelectedFile%
		 
		 quoted_selectedfile := quote(SelectedFile)
		 
		fullexec_path := get_my_utils_path("src\send_markdown_to_onenote_for_ahk.pyw")
		RunWait, %fullexec_path% %quoted_selectedfile%
		
		SplitPath, SelectedFile,, dir
		dirname := quote(dir)
		RunWait, python -m http.server -d %dirname%
	}
}

CapsLock &  o:: SendMarkdownToOnenote()

ListMarkdownLatexEquations()
{
	FileSelectFile, SelectedFile, 3, , , Markdown Documents (*.md)
	if (SelectedFile = "")
	{
		return
	}
	else
	{
		 ;MsgBox, The user selected the following:`n%SelectedFile%
		 
		 quoted_selectedfile := quote(SelectedFile)
		 
		fullexec_path := get_my_utils_path("src\list_latex_equations.pyw")
		RunWait, %fullexec_path% %quoted_selectedfile%
		
		SplitPath, SelectedFile,, dir
		MsgBox, latex equations saved to %dir%\latex_equations.txt
	}
}

CapsLock &  l:: ListMarkdownLatexEquations()

SendMarkdownToSupermemo()
{
	FileSelectFile, SelectedFile, 3, , , Markdown Documents (*.md)
	if (SelectedFile = "")
	{
		return
	}
	else
	{
		 ;MsgBox, The user selected the following:`n%SelectedFile%
		 
		 quoted_selectedfile := quote(SelectedFile)
		 
		fullexec_path := get_my_utils_path("src\send_markdown_to_supermemo_from_ahk.pyw")
		RunWait, %fullexec_path% %quoted_selectedfile%
		
		SplitPath, SelectedFile,, dir
		dirname := quote(dir)
		RunWait, python -m http.server -d %dirname%
	}
}

CapsLock &  u:: SendMarkdownToSupermemo()

SendMarkdownToTheBrain()
{
	FileSelectFile, SelectedFile, 3, , , Markdown Documents (*.md)
	if (SelectedFile = "")
	{
		return
	}
	else
	{
		 ;MsgBox, The user selected the following:`n%SelectedFile%
		 
		 quoted_selectedfile := quote(SelectedFile)
		 
		fullexec_path := get_my_utils_path("src\send_markdown_to_thebrain_from_ahk.pyw")
		RunWait, %fullexec_path% %quoted_selectedfile%
		
		SplitPath, SelectedFile,, dir
		dirname := quote(dir)
		RunWait, python -m http.server -d %dirname%
	}
}

CapsLock &  i:: SendMarkdownToTheBrain()	

NormalizedPaste()
{
	fullexec_path := get_my_utils_path("src\normalize_clipboard.pyw")
	RunWait, %fullexec_path%
	send, ^v
}

CapsLock &  v:: NormalizedPaste()	

