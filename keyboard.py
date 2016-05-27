class Keyboard:
    def __init__(self):
        self.keymap = {
            'a': 0, 'q': 1, 'w': 2, 'z': 3,
            's': 4, 'x': 5, 'e': 6, 'd': 7,
            'c': 8, 'r': 9, 'f': 0xA, 'v': 0xB,
            't': 0xC, 'g': 0xD, 'b': 0xE, 'y': 0xF
        }
        self.key_down = None

    def set_key_down(self, key_id):
        self.key_down = self.keymap[key_id]

    def reset_key_state(self):
        self.key_down = None

