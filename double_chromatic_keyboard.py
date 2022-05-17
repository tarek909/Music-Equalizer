from pynput.keyboard import Key

keyboard = \
    {
        # Main gauche
        't': 'Sol2',
        'f': 'La2',
        'r': 'La#2',
        "'": 'Si2',
        'd': 'Do3',
        'e': 'Do#3',
        '"': 'Re3',
        's': 'Re#3',
        'z': 'Mi3',
        'é': 'Fa3',
        'q': 'Fa#3',
        'a': 'Sol3',
        '&': 'Sol#3',
        Key.caps_lock: 'La3',

        # Main droite
        '(': 'Re3',
        '-': 'Fa3',
        'g': 'Fa#3',
        'y': 'Sol3',
        'è': 'Sol#3',
        'h': 'La3',
        'u': 'La#3',
        '_': 'Si3',
        'j': 'Do4',
        'i': 'Do#4',
        'ç': 'Re4',
        'k': 'Re#4',
        'o': 'Mi4',
        'à': 'Fa4',
        'l': 'Fa#4',
        'p': 'Sol4',
        ')': 'Sol#4',
        'm': 'La4',
        '^': 'La#4',
        '=': 'Si4',
        'ù': 'Do5',
        '$': 'Do#5',
        Key.backspace: 'Re5',
        Key.enter: 'Mi5'
    }
