#!/usr/bin/env python3

import getopt
import os
import sys

import emoji
import export
import jsonutils
import log
import manifest

VERSION = '0.2.0'

HELP = f'''orxporter {VERSION}
USAGE: orxport.py [options...]

OPTIONS:
-h                      prints this help message
-m PATH                 manifest file path (default: manifest)
-i PATH                 input directory path (default: in)
-o PATH                 output directory path (default: out)
-f PATH_EXPR            output naming system (default: %f/%s)
-F FORMAT[,FORMAT...]   output formats (default: svg)
-e FILTER               emoji filter
-j FILE                 export JSON replica of directory structure
-J FILE                 export JSON metadata for mutstd website
-c                      disable ANSI color codes
-q WIDTHxHEIGHT         ensure source images have given size
-t NUM                  number of worker threads (default: 1)
--force-desc            ensure all emoji have a description
-r RENDERER             SVG renderer (default: inkscape)
-b NUM                  maximum files per exiftool call (default: 1000)

OUTPUT FORMATS:
svg
png-SIZE

RENDERERS:
inkscape
rendersvg'''

def main():
    manifest_path = 'manifest'
    input_path = 'in'
    output_path = 'out'
    output_naming = '%f/%s'
    output_formats = ['svg']
    emoji_filter = []
    json_out = None
    web_out = None
    src_size = None
    num_threads = 1
    force_desc = False
    renderer = 'inkscape'
    max_batch = 1000
    try:
        opts, _ = getopt.getopt(sys.argv[1:],
                                'hm:i:o:f:F:ce:j:J:q:t:r:b:',
                                ['help', 'force-desc'])
        for opt, arg in opts:
            if opt in ['-h', '--help']:
                print(HELP)
                sys.exit()
            elif opt == '-m':
                manifest_path = arg
            elif opt == '-i':
                input_path = arg
            elif opt == '-o':
                output_path = arg
            elif opt == '-f':
                output_naming = arg
            elif opt == '-F':
                output_formats = arg.split(',')
            elif opt == '-c':
                log.use_color = False
            elif opt == '-e':
                k, v = arg.split('=')
                v = v.split(',')
                emoji_filter.append((k, v))
            elif opt == '-j':
                json_out = arg
            elif opt == '-J':
                web_out = arg
            elif opt == '-q':
                t1, t2 = arg.split('x')
                src_size = int(t1), int(t2)
            elif opt == '-t':
                num_threads = int(arg)
                if num_threads <= 0:
                    raise ValueError
            elif opt == '--force-desc':
                force_desc = True
            elif opt == '-r':
                renderer = arg
            elif opt == '-b':
                max_batch = int(arg)
                if max_batch <= 0:
                    raise ValueError
    except Exception:
        print(HELP)
        sys.exit(2)
    try:
        if renderer not in ['inkscape', 'rendersvg', 'imagemagick']:
            raise Exception('Invalid renderer: ' + renderer)
        log.out(f'Loading manifest file...', 36)
        m = manifest.Manifest(os.path.dirname(manifest_path),
                              os.path.basename(manifest_path))
        log.out(f'{len(m.emoji)} emoji defined', 33, 4)
        filtered_emoji = [e for e in m.emoji if emoji.match(e, emoji_filter)]
        if emoji_filter:
            log.out(f'{len(filtered_emoji)} / {len(m.emoji)} '
                    f'emoji match filter', 34, 4)
        if force_desc:
            nondesc = [e.get('code', str(e)) for e in filtered_emoji if 'desc' not in e]
            if nondesc:
                raise ValueError('Emoji without a description: ' +
                                 ', '.join(nondesc))
        if json_out:
            jsonutils.write_emoji(filtered_emoji, json_out)
        elif web_out:
            jsonutils.write_web(filtered_emoji, web_out)
        else:
            export.export(m, filtered_emoji, input_path, output_formats,
                          os.path.join(output_path, output_naming), src_size,
                          num_threads, renderer, max_batch)
    except Exception as e:
        log.out(f'!!! {e}', 31)
        sys.exit(1)
    log.out('All done', 36)

if __name__ == '__main__':
    main()
