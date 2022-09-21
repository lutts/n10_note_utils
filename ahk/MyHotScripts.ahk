#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

quote(string) {
    return """" string """"
}

get_my_utils_path(filename) {
	PYTHON_UTILS_DIR := "D:\Data\python\projects\my_utils\"
	
	fullpath :=  PYTHON_UTILS_DIR . filename
	fullpath := quote(fullpath)
    return fullpath
}

; 将剪贴板中的markdown文本转为html，再将html文本放回剪贴板
ClipboardMarkdownToHtml()
{
	fullexec_path := get_my_utils_path("utils\markdown2clipboard.pyw")
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
		
		fullexec_path := get_my_utils_path("utils\n10_note_for_ahk.pyw")
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
		 
		fullexec_path := get_my_utils_path("utils\send_markdown_to_onenote_for_ahk.pyw")
		RunWait, %fullexec_ppath% %quoted_selectedfile%
		
		SplitPath, SelectedFile,, dir
		dirname := quote(dir)
		RunWait, C:\Users\lutts\AppData\Local\Microsoft\WindowsApps\python.exe -m http.server -d %dirname%
	}
}

CapsLock &  o:: SendMarkdownToOnenote()