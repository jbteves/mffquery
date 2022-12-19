import argparse                     # ArgumentParser
import datetime                     # datetetime
import glob                         # glob
import os                           # path.join
import xml.etree.ElementTree as ET  # parse

PREFIX_EVENT_EGI = '{http://www.egi.com/event_mff}'
PREFIX_INFO_EGI = '{http://www.egi.com/info_mff}'

def harvest_event_files(mffname: str) -> list[str]:
    return glob.glob(os.path.join(mffname, 'Events_*'))

def trim_evt_prefix(s: str) -> str:
    return s[len(PREFIX_EVENT_EGI):]

def trim_info_prefix(s: str) -> str:
    return s[len(PREFIX_INFO_EGI):]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--datetime',
        help='Do not convert datetimes into relative milliseconds.',
        action='store_true',
    )
    parser.add_argument(
        '--sort_by',
        default='relative_millis',
        help=(
            'The column to sort by. The special key "relative_millis" may '
            'be used to sort by the relative time. Default "relative_millis,"'
            ' or "beginTime" if the --datetime option is used.'
        ),
    )
    parser.add_argument(
        '--to_csv',
        default=None,
        help='File to save output to as a csv. Default None.',
    )
    parser.add_argument(
        'mff',
        help='The .mff file to parse',
    )
    parser.add_argument(
        'columns',
        help=(
            'The columns to write out, in the desired order.'
            'Either relative_millis or beginTime is always written out.'
        ),
        nargs='+',
    )
    args = parser.parse_args()
    time_column = 'relative_millis' if not args.datetime else 'beginTime'
    args.columns.insert(0, time_column)
    # Decide if beginTime or relative_millis should be used
    if args.datetime and args.sort_by == 'relative_millis':
        sorter = lambda x: x['beginTime']
    else:
        sorter = lambda x: x[args.sort_by]
    event_files = harvest_event_files(args.mff)
    # Events should be a dictionary, where each key represents an event file,
    # and each event file has an "events" key and optionally a "trackType"
    events = {}
    # Iterate over all event files and find the events
    for f in event_files:
        tree = ET.parse(f)
        root = tree.getroot()
        # First sub-element tag: 'name', text: the name of the event track
        name_element = root[0]
        element_tag = trim_evt_prefix(name_element.tag)
        if element_tag != 'name':
            raise ValueError(
                'Unexpected Tree type: first XML element does not have name'
            )
        curr_name = name_element.text
        events[curr_name] = {}
        curr_dict = events[curr_name]
        # Second sub-element should be trackType, but also might not
        track_element = root[1]
        element_tag = trim_evt_prefix(track_element.tag)
        start = 1
        if element_tag == 'trackType':
            curr_dict['trackType'] = track_element.text
            start += 1
        curr_dict['events'] = []
        for x in root[start:]:
            # Iterate over events
            if trim_evt_prefix(x.tag) != 'event':
                continue
            curr_dict['events'].append(
                {trim_evt_prefix(y.tag): y.text for y in x}
            )
    # Harvest all events
    all_events = []
    for k, v in events.items():
        for evt in v['events']:
            all_events.append(evt)
    if not args.datetime:
        # Get the recording start time
        info_xml = os.path.join(args.mff, "info.xml")
        info_tree = ET.parse(info_xml)
        info_root = info_tree.getroot()
        record_start = None
        for x in info_root:
            if trim_info_prefix(x.tag) == 'recordTime':
                record_start = x.text
        if not record_start:
            raise ValueError('Could not find the recording start time.')
        record_dt = datetime.datetime.fromisoformat(record_start)
        # Calculate the time in milliseconds between recording and event start
        for evt in all_events:
            evt_dt = datetime.datetime.fromisoformat(evt['beginTime'])
            delta_t = evt_dt - record_dt
            evt['relative_millis'] = (
                delta_t.seconds * 1000
                + delta_t.microseconds // 1000
            )
    # Sort the events
    all_events.sort(key=sorter)
    # Determine if a delimiter should be a comma or tab
    delimiter = '\t' if not args.to_csv else ','
    out_lines = [delimiter.join(args.columns)]
    for evt in all_events:
        out_lines.append(delimiter.join(
            [str(evt[column]) if evt[column] else "" for column in args.columns]
        ))
    out_str = '\n'.join(out_lines)
    # Put into file or stdout
    if args.to_csv:
        with open(args.to_csv, 'w') as f:
            f.write(out_str)
    else:
        print(out_str)

if __name__ == '__main__':
    main()
