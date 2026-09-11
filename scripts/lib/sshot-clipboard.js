// Wait for one new clipboard image; never export the initial contents.
ObjC.import('AppKit');
ObjC.import('Foundation');
function run(argv) {
    const pb = $.NSPasteboard.generalPasteboard;
    if (argv[0] === '--count') return String(Number(pb.changeCount));
    const destination = argv[0];
    let previous = Number(argv[1]);
    const deadline = Date.now() + 120000;
    while (Date.now() < deadline) {
        if ($.NSFileManager.defaultManager.fileExistsAtPath($(argv[2]))) return 'Cancelled';
        const current = Number(pb.changeCount);
        if (current !== previous) {
            previous = current;
            const type = pb.availableTypeFromArray($(['public.png', 'public.tiff']));
            if (type && !type.isNil()) {
                const data = pb.dataForType(type);
                if (data && !data.isNil() && Number(pb.changeCount) === current) {
                    const rep = $.NSBitmapImageRep.imageRepWithData(data);
                    if (!rep || rep.isNil()) throw Error('Clipboard image cannot be decoded');
                    const png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $({}));
                    if (!png || png.isNil() || !png.writeToFileAtomically($(destination), true)) {
                        throw Error('Cannot save clipboard PNG');
                    }
                    return 'New image captured';
                }
            }
        }
        delay(0.25);
    }
    return 'Expired: no new image captured within 120 seconds';
}
