""".mff querying tool"""

from argparse import ArgumentParser
from datetime import datetime

import mffpy


VALID_COLUMNS = ('code', 'description', 'label', 'none')


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
    parser.add_argument(
        '--clock',
        help=(
            "Use clock time instead of time relative to record start."
        ),
        action='store_true',
    )
    parser.add_argument(
        '--number',
        help=(
            "Number events as the leftmost column."
        ),
        action='store_true'
    )
#    parser.add_argument(
#        '--csv',
#        help=(
#            "Store output in csv file instead of print to standard out."
#        )
#    )
    parser.add_argument(
        'file',
        help=".mff file to read events from.",
    )
    parser.add_argument(
        'column',
        help=(
            "Additional columns to print. "
            f"Valid values are {VALID_COLUMNS}."
        ),
        nargs='+',
    )
    args = parser.parse_args()
    for c in args.column:
        if c not in VALID_COLUMNS:
            raise ValueError(
                f"{c} is not a valid column type. "
                f"Valid column types are: {VALID_COLUMNS}"
            )
    columns_to_add = args.column
    if 'none' in columns_to_add and len(columns_to_add) != 1:
        raise ValueError(
            f"Cannot combine 'none' and other columns {columns_to_add}"
        )
    elif 'none' in columns_to_add:
        add_columns = False
    else:
        add_columns = True
    info = mffpy.Reader(args.file)
    is_relative = not args.clock
    add_numbers = args.number
#    use_stdout = not args.csv

    mff_content = info.get_mff_content()
    start_time = str_to_time(mff_content['fileInfo']['recordTime'])
    event_list = mff_content['eventTrack']['event']
    count = 0
    for event in event_list:
        to_print = []
        if add_numbers:
            to_print.append(str(count))
        count += 1
        # get a time string
        time_str = event['beginTime']
        if is_relative:
            event_time = str_to_time(event['beginTime'])
            difference = event_time - start_time
            time = f"{difference.seconds:04}.{difference.microseconds:06}"
        else:
            time = time_str
        to_print.append(time)
        if add_columns:
            for col in columns_to_add:
                to_print.append(event[col])
        print('\t'.join(to_print))


if __name__ == '__main__':
    main()
