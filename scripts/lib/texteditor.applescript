-- Finder delivers documents as an open event, not command-line arguments.
on run
	launchEditor({})
end run

on open openedFiles
	launchEditor(openedFiles)
end open

on launchEditor(openedFiles)
	set launcher to (POSIX path of (path to home folder)) & "dotfiles/scripts/texteditor"
	set commandLine to quoted form of launcher
	repeat with fileRef in openedFiles
		set commandLine to commandLine & " " & quoted form of (POSIX path of fileRef)
	end repeat
	do shell script commandLine
end launchEditor
