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

## Make TextEditor the default in bulk

With the app installed and registered, use the macOS Swift toolchain:

```sh
# Preview only; does not change associations or create backups.
swift scripts/lib/texteditor-defaults.swift

# Save local backups, apply associations, and verify the resulting handlers.
swift scripts/lib/texteditor-defaults.swift --apply
```

The script covers common plain-text, source-code, markup, and configuration
extensions, plus generic plain-text/source-code types. The preview includes
every proposed type, including generic ones without an extension. It does not
install software or sync machines. Repeat it on each Mac; defaults are per user.

macOS may ask **Use TextEditor** separately for many types. Run `--apply` with
access to that Mac's desktop and approve the requested changes there; SSH does
not bypass these confirmations. Already-correct associations are skipped. If a
confirmation takes more than 90 seconds, the script stops without retrying;
resolve any pending dialog and inspect the result before running it again.

Backups of raw Launch Services preferences and resolved previous handlers go to
`~/Library/Application Support/OM/TextEditor/`, never into Git. Preserve these
files if you need to restore previous choices. Importing a complete preferences
backup also reverts unrelated association changes made since that backup;
restore selectively when necessary. Partial failures are reported with a nonzero
exit code, without silently rolling back other successful changes.

The script does not claim generic data, images, PDFs, archives, or executables.
Some extensions are ambiguous: macOS classifies `.ts` as video, but this script
explicitly assigns it to TextEditor for TypeScript. Consequently, actual video
files named `.ts` also use TextEditor. `.mts` is skipped when its type also
covers `.m2ts` videos. Declared non-text types (for example GarageBand's `.exs`)
and extensions resolving to generic `public.data` are also skipped. Unknown
extensions and extensionless names are not guaranteed; Finder's per-file **Open
With** remains available. No blanket association can reliably infer whether
arbitrary file contents are source code.

Run the read-only association checks with
`bash tests/test_texteditor_defaults.sh`.
