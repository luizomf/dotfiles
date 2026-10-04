# TextEditor (macOS)

TextEditor is a Finder-facing AppleScript app that launches Neovim in OMXterm.
The launcher is `scripts/texteditor`; the app source is
`scripts/lib/texteditor.applescript`. It expects this checkout at `~/dotfiles`,
OMXterm installed, and `nvim` on the login shell's PATH. The launcher uses
`$SHELL` (a POSIX-compatible shell such as sh, bash, or zsh), falling back to
`/bin/sh` when empty (Bash may initialize an unset `$SHELL` from the user
account). If that shell cannot find Node, it loads `$NVM_DIR/nvm.sh` (defaulting
to `~/.nvm/nvm.sh`) when available, so Node-based language servers also work
when launched from Finder. An already available Node is left unchanged.

- Launch the app normally for an empty editor.
- Use Finder's **Open With → TextEditor**, or drop files onto the app.
- From a terminal:
  `~/dotfiles/scripts/texteditor "notes.txt" "another file.md"`.
- Via Launch Services: `open -a TextEditor "notes.txt"`.

Multiple files open as Neovim buffers (`:ls`, `:bn`, `:bp`). Relative paths are
resolved before the launcher switches to the home directory. File arguments are
passed separately from the shell command and after Neovim's `--` delimiter.

## Updating the existing app

Quit TextEditor first. Back up the existing `.app` outside `/Applications`
(preferably as a ZIP, so Finder does not register a second editor). Do not
commit app bundles or local backups.

Compile the handler into the existing bundle, preserving its icon and identity:

```sh
app=/Applications/Utilities/OM/TextEditor.app
# Script Editor may have saved the compiled script read-only.
chmod u+w "$app/Contents/Resources/Scripts/main.scpt"
osacompile -o "$app/Contents/Resources/Scripts/main.scpt" \
  scripts/lib/texteditor.applescript
chmod a-w "$app/Contents/Resources/Scripts/main.scpt"
```

Set `CFBundleDocumentTypes` in `Contents/Info.plist` to the following array:

```xml
<array>
  <dict>
    <key>CFBundleTypeName</key>
    <string>Text document</string>
    <key>CFBundleTypeRole</key>
    <string>Editor</string>
    <key>LSHandlerRank</key>
    <string>Alternate</string>
    <key>LSItemContentTypes</key>
    <array>
      <string>public.text</string>
      <string>public.json</string>
      <string>public.xml</string>
    </array>
  </dict>
</array>
```

Re-sign the modified local app and refresh its Launch Services registration:

```sh
codesign --force --sign - "$app"
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$app"
```

This advertises an alternate editor, without changing existing default file
associations. For a specific extension, use Finder's **Get Info → Open with →
Change All** only if you want it to become the default. For files not recognized
as text, use **Open With → Other → Enable: All Applications**.

Run isolated launcher checks with `bash tests/test_texteditor.sh`. After
updating the app, manually confirm Finder opens a disposable text file in
Neovim.
