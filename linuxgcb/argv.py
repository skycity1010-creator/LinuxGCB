"""Offline wm_exec argv subset: double quotes group; backslash escapes.

Single quotes are ordinary bytes. No shell expansion occurs at this layer.
Malformed input is rejected rather than guessing an executable argv.
"""


def w_strtok(command):
    argv, word = [], []
    quoted = active = False
    i = 0
    while i < len(command):
        char = command[i]
        if char == '\\':
            i += 1
            if i == len(command):
                raise ValueError('Trailing escape')
            word.append(command[i])
            active = True
        elif char == '"':
            quoted = not quoted
            active = True
        elif char in ' \t\r\n' and not quoted:
            if active:
                argv.append(''.join(word))
                word, active = [], False
        else:
            word.append(char)
            active = True
        i += 1
    if quoted:
        raise ValueError('Unpaired double quote')
    if active:
        argv.append(''.join(word))
    return argv


def quote_argument(value):
    """Encode one argument and verify its round trip through the model."""
    encoded = '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
    assert w_strtok(encoded) == [value]
    return encoded
