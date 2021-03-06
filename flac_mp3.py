"""Convert FLAC to MP3 using FFmpeg."""

from pathlib import Path
import argparse
import subprocess
import sys


FFMPEG = ('ffmpeg -hide_banner -loglevel {loglevel}'
          ' -i "{source}" -f mp3 -ab {bitrate} -vcodec copy "{target}"')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-r', '--recursive', default=False, action='store_true',
        help='search subdirectories')
    parser.add_argument(
        '-b', '--bitrate', default='320k', metavar='BITRATE',
        choices=('256k', '320k'),
        help='desired bitrate of the target files (default 320k)')
    parser.add_argument(
        '--ffmpeg-loglevel', default='error', metavar='LEVEL',
        choices=('debug', 'verbose', 'info', 'warning',
                 'error', 'fatal', 'panic', 'quiet'),
        help='desired level of ffmpeg output (default error)')
    parser.add_argument(
        'sources', nargs='+', metavar='SOURCE', 
        help='file or directory to convert')
    parser.add_argument(
        'target', nargs=1, metavar='TARGET',
        help='target directory for the converted files and/or directories')
    args = parser.parse_args()
    args.sources = [Path(src) for src in args.sources]
    args.target = Path(args.target[0])
    return args


def call_ffmpeg(source, target, bitrate='320k', loglevel='error'):
    ffmpeg = FFMPEG.format(loglevel=loglevel, source=source,
                           bitrate=bitrate, target=target)
    return subprocess.check_output(
        ffmpeg, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)


if __name__ == '__main__':
    args = parse_args()

    if not args.target.exists():
        args.target.mkdir(parents=True)
    if not args.target.is_dir():
        print('error:', args.target, 'is not a directory')
        sys.exit(1)

    skipmsg = '{}: target already exists'
    for source in args.sources:
        if source.is_dir():
            print(source.name)
            pattern = '**/*.flac' if args.recursive else '*.flac'
            for flac in sorted(source.glob(pattern)):
                target = args.target / source.name / flac.relative_to(source)
                target = target.parent / target.name.replace('.flac', '.mp3')
                if not target.parent.exists():
                    target.parent.mkdir(parents=True)
                if target.exists():
                    print('|', skipmsg.format(flac.relative_to(source)))
                    continue

                print('|', flac.relative_to(source))
                output = call_ffmpeg(flac, target, bitrate=args.bitrate,
                                     loglevel=args.ffmpeg_loglevel)
                if output:
                    print(output.rstrip())

        elif source.is_file():
            target = args.target / source.name.replace('.flac', '.mp3')
            if target.exists():
                print(skipmsg.format(source.name))
                continue

            print(source.name)
            output = call_ffmpeg(source, target, bitrate=args.bitrate,
                                 loglevel=args.ffmpeg_loglevel)
            if output:
                print(output.rstrip())

        else:
            print('warning: no such file or directory:', source)
