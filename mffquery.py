""".mff querying tool"""

from argparse import ArgumentParser
from datetime import datetime

import mffpy


def str_to_time(t: str) -> datetime:
    # Shave off UTC offset
    t = t[:-6]
    time_format = '%Y-%m-%dT%H:%M:%S.%f'
    return datetime.strptime(t, time_format)


def dt_to_seconds(t: str, start) -> str:
    tt = str_to_time(t)
    dt = tt - start
    return f"{dt.seconds:03}.{dt.microseconds:06}"


def main():
    parser = ArgumentParser(description='.mff querying tool')
    parser.add_argument('file', help='The file to query.')
    parser.add_argument(
        '--time',
        help=(
            "Use datetime instead of seconds from recording start "
            "for event onsets."
        ),
        action='store_true',
    )
    args = parser.parse_args()
    info = mffpy.Reader(args.file)
    mff_content = info.get_mff_content()
    start_time = str_to_time(mff_content['fileInfo']['recordTime'])
    print(start_time)
    event_list = mff_content['eventTrack']['event']
    count = 0
    LABEL = "Label"
    if args.time:
        START = "Start Time"
    else:
        START = "Start Time (s)"
    DURATION = "Duration (ms)"
    if args.time:
        header_line = f"N   \t{LABEL:10}\t{START:25}\t\t{DURATION:<10}"
    else:
        header_line = f"N   \t{LABEL:10}\t{START:15}\t{DURATION:<10}"
    dash_line = '-'*75
    print(header_line)
    print(dash_line)
    for event in event_list:
        label = event['label']
        description = event['description']
        if args.time:
            begin_time = event['beginTime']
        else:
            begin_time = dt_to_seconds(event['beginTime'], start_time)
        duration = event['duration']
        if args.time:
            print(
                f"{count:04}\t{label:10}\t{begin_time:25}\t{duration:<10}"
            )
        else:
            print(
                f"{count:04}\t{label:10}\t{begin_time:15}\t{duration:<10}"
            )

        count += 1
        if count > 10:
            break


if __name__ == '__main__':
    main()
