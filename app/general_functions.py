"""
This is just a module for some general functions
"""


def convert_bytes_to_size(some_bytes):
    """
    Convert number of bytes to appropriate form for display.
    :param some_bytes: A string or integer
    :return: A string
    """
    some_bytes = int(some_bytes)
    suffix_dict = {
        '0': 'B',
        '1': 'KiB',
        '2': 'MiB',
        '3': 'GiB',
        '4': 'TiB',
        '5': 'PiB'

    }
    counter = 0
    while some_bytes > 1 and counter <= 5:
        tmp = some_bytes / 1024
        if tmp < 1:
            break
        else:
            some_bytes = tmp
            counter += 1

    return str(format(some_bytes, '.2f')) + ' ' + str(suffix_dict[str(counter)])
