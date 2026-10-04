// Register TextEditor for common plain-text, configuration, and source-code types.
// Run without arguments to preview; --apply saves backups before changing defaults.
import Foundation
import AppKit
import UniformTypeIdentifiers

let arguments = Array(CommandLine.arguments.dropFirst())
guard arguments.isEmpty || arguments == ["--list"] || arguments == ["--apply"] else {
    print("Usage: swift scripts/lib/texteditor-defaults.swift [--list|--apply]")
    exit(2)
}
let apply = arguments == ["--apply"]
let editor = "com.apple.ScriptEditor.id.TextEditor"
let extensions = """
txt text log md markdown mdown mkd mdx rst rest adoc asciidoc org tex latex bib sty cls
js mjs cjs jsx ts mts cts tsx py pyw pyi pyx pxd pxi ipynb rb rake gemspec php phtml php3 php4 php5 php7 php8 phps
sh bash zsh ksh fish csh tcsh command ps1 psm1 psd1 bat cmd awk sed pl pm pod r R rmd qmd jl lua luau tcl tk
c h cc hh cpp hpp cxx hxx c++ h++ m mm swift rs go java kt kts scala sc groovy gvy gsh clj cljs cljc edn
cs fs fsx fsi vb vbs vba dart ex exs erl hrl hs lhs ml mli mll mly elm pures purs lisp lsp cl el scm ss rkt
zig nim nims d di pas pp f f90 f95 f03 f08 for f77 asm s S v sv vh svh vhd vhdl sol proto thrift graphql gql
html htm xhtml shtml css scss sass less vue svelte astro njk nunjucks jinja jinja2 j2 liquid twig hbs handlebars mustache erb ejs haml pug jade
json jsonc json5 jsonl ndjson yaml yml toml xml xsd xsl xslt dtd entitlements xcconfig xcworkspacedata
ini cfg conf config properties env dotenv editorconfig gitignore gitattributes gitmodules gitconfig npmrc nvmrc tool-versions lock
sql csv tsv diff patch gradle cmake make mk mak makefile dockerfile containerfile tf tfvars hcl nix nixexpr cu cuh ino
feature robot spec test http rasi desktop service timer socket target mount automount path rules policy
""".split(whereSeparator: \.isWhitespace).map(String.init)

// Do not claim public.data, public.content, executables, or rich-text bundles.
var identifiers = Set([
    "public.plain-text", "public.utf8-plain-text", "public.utf16-plain-text",
    "public.utf16-external-plain-text", "public.source-code", "public.script",
    "public.shell-script", "public.json", "public.xml", "public.html",
    "public.css", "public.comma-separated-values-text", "public.tab-separated-values-text"
])
let forbiddenIdentifiers: Set<String> = [
    "public.data", "public.content", "public.item", "public.executable",
    "public.unix-executable", "com.apple.mach-o-binary", "com.apple.application",
    "com.apple.application-bundle", "com.adobe.pdf"
]
let forbiddenAncestors = ["public.executable", "public.unix-executable", "com.apple.mach-o-binary", "com.apple.application"]
    .compactMap { UTType($0) }
var extensionTypes: [String: String] = [:]
var skipped: [String: String] = [:]
for ext in extensions {
    if let type = UTType(filenameExtension: ext) {
        // Some source-code extensions collide with media formats on macOS.
        // macOS declares .ts as video, but this extension is explicitly wanted
        // for TypeScript. Only accept that collision if the type covers .ts alone.
        let typescript = ext == "ts" && type.tags[.filenameExtension] == ["ts"]
        // Executable source (for example JavaScript) is still text; compiled
        // executables are not. Declared non-text types may collide with source
        // extensions, such as GarageBand's binary .exs instruments.
        let text = type.conforms(to: .text) || type.conforms(to: .sourceCode) || type.conforms(to: .script)
        if forbiddenIdentifiers.contains(type.identifier) || type.conforms(to: .pdf)
            || (!text && forbiddenAncestors.contains(where: { type.conforms(to: $0) }))
            || type.conforms(to: .image) || type.conforms(to: .archive)
            || type.conforms(to: .folder)
            || (!typescript && (type.conforms(to: .audiovisualContent) || (!type.isDynamic && !text))) {
            skipped[ext] = type.identifier
            continue
        }
        identifiers.insert(type.identifier)
        extensionTypes[ext] = type.identifier
    }
}

if !apply {
    for identifier in identifiers.sorted() {
        print("TYPE \(identifier)")
    }
    for ext in extensionTypes.keys.sorted() {
        print("\(ext): \(extensionTypes[ext]!)")
    }
    for ext in skipped.keys.sorted() {
        print("SKIP \(ext): \(skipped[ext]!)")
    }
    print("Preview only. Use --apply to save backups and change defaults.")
    exit(0)
}

guard let editorURL = NSWorkspace.shared.urlForApplication(withBundleIdentifier: editor) else {
    print("TextEditor.app is not registered. Install and register the app first.")
    exit(1)
}

func handler(_ identifier: String) -> String? {
    guard let type = UTType(identifier),
          let url = NSWorkspace.shared.urlForApplication(toOpen: type) else { return nil }
    return Bundle(url: url)?.bundleIdentifier
}
let protected = ["public.data", "public.jpeg", "public.png", "com.adobe.pdf", "public.movie", "public.avchd-mpeg-2-transport-stream", "public.zip-archive", "public.unix-executable"]
let protectedBefore = protected.map { handler($0) }
let directory = FileManager.default.homeDirectoryForCurrentUser
    .appendingPathComponent("Library/Application Support/OM/TextEditor", isDirectory: true)
try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
let stamp = ISO8601DateFormatter().string(from: Date()).replacingOccurrences(of: ":", with: "-") + "-" + UUID().uuidString
// Keep the raw preferences too: resolved handlers alone cannot distinguish
// explicit user choices from inherited defaults when restoring associations.
let preferencesURL = directory.appendingPathComponent("launchservices-before-\(stamp).plist")
let exportProcess = Process()
exportProcess.executableURL = URL(fileURLWithPath: "/usr/bin/defaults")
exportProcess.arguments = ["export", "com.apple.LaunchServices/com.apple.launchservices.secure", preferencesURL.path]
try exportProcess.run()
exportProcess.waitUntilExit()
guard exportProcess.terminationStatus == 0 else {
    print("Could not back up Launch Services preferences; no defaults changed.")
    exit(1)
}
var previous: [String: [String: String]] = [:]
for identifier in identifiers.sorted() {
    var resolved: [String: String] = [:]
    resolved["default"] = handler(identifier)
    previous[identifier] = resolved
}
let backup: [String: Any] = ["handlers": previous, "extensions": extensionTypes]
let backupURL = directory.appendingPathComponent("handlers-before-\(stamp).json")
try JSONSerialization.data(withJSONObject: backup, options: [.prettyPrinted, .sortedKeys]).write(to: backupURL, options: .atomic)

var failures: [String] = []
var configured = 0
for identifier in identifiers.sorted() {
    guard let type = UTType(identifier) else {
        failures.append("\(identifier): unavailable content type")
        continue
    }
    if handler(identifier)?.caseInsensitiveCompare(editor) == .orderedSame {
        configured += 1
        continue
    }
    // The deprecated Launch Services setter can return success without changing
    // anything on modern macOS. Use NSWorkspace and wait for its completion.
    var completed = false
    var failure: Error?
    NSWorkspace.shared.setDefaultApplication(at: editorURL, toOpen: type) { error in
        failure = error
        completed = true
    }
    let deadline = Date().addingTimeInterval(90)
    while !completed && Date() < deadline {
        _ = RunLoop.current.run(mode: .default, before: Date().addingTimeInterval(0.02))
    }
    if !completed {
        print("\(identifier): timed out; consent may be pending. Stopped without retrying.")
        print("Configured \(configured)/\(identifiers.count) types before stopping.")
        print("Backups: \(backupURL.path), \(preferencesURL.path)")
        // Do not query Launch Services again while a consent request is pending.
        exit(1)
    } else if let failure {
        failures.append("\(identifier): \(failure.localizedDescription)")
    } else if handler(identifier)?.caseInsensitiveCompare(editor) != .orderedSame {
        failures.append("\(identifier): verification mismatch")
    } else {
        configured += 1
    }
}
print("Configured \(configured)/\(identifiers.count) text/code types; planned \(extensionTypes.count) extension spellings.")
print("Previous handlers saved: \(backupURL.path)")
print("Raw preferences saved: \(preferencesURL.path)")
for ext in ["txt", "md", "js", "ts", "py", "json", "yaml", "sh"] {
    if let identifier = extensionTypes[ext] {
        print(".\(ext): \(handler(identifier) ?? "unset")")
    }
}
for (index, identifier) in protected.enumerated() {
    if handler(identifier) != protectedBefore[index] {
        failures.append("Protected association changed: \(identifier)")
    }
}
for ext in skipped.keys.sorted() {
    let identifier = skipped[ext]!
    print("Left unchanged .\(ext) (\(identifier)): \(handler(identifier) ?? "unset")")
}
if !failures.isEmpty {
    print(failures.joined(separator: "\n"))
    exit(1)
}
