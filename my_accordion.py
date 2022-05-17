import copy
import sounddevice as sd
import numpy as np
import time
from pynput import keyboard
from pynput.keyboard import Key
import single_chromatic_keyboard
import double_chromatic_keyboard
import double_chords_keyboard


class Accordion():
    gamme = ['Do', 'Do#', 'Re', 'Re#', 'Mi', 'Fa', 'Fa#', 'Sol',
             'Sol#', 'La', 'La#', 'Si']

    def __init__(self, sound_library, configuration):
        # Variables initialisation
        self.volume = 0.05  # range [0.0, 1.0], keep low to avoid saturation
        self.end = False
        self.start_idx = 0
        self.soundlibrary = {'diapson': 1, 'accordion': 0.2, 'carillon': 0.8, 'custom_synthetiser': 0.2, 'piano': 0.3}
        self.buttons_stabilised = []
        self.crescendo_beginning = []
        self.decrescendo_beginning = []
        self.crescendo_ended = []
        self.decrescendo_ended = []
        self.buttons_crescendo = dict()
        # {freq : [press_time, volume, current_volume]}
        self.buttons_decrescendo = dict()
        # {freq : [release_time, volume, current_volume]}
        self.notes_played = []
        self.keys_pressed = []
        self.volumes_of_notes = {}
        self.sound = np.zeros((384, 1))
        self.sample_rate = 44100

        self.keyboardListener = keyboard.Listener(
            on_press=self.on_press, on_release=self.on_release)
        self.keyboardListener.start()

        self.sound_library = sound_library
        self.switcher_pressed = False
        self.crescendo_duration = 0.01
        for i in self.soundlibrary.keys():
            if sound_library == i:
                self.decrescendo_duration = self.soundlibrary.get(i)

        # if sound_library == "diapason":
        #     self.decrescendo_duration = 1
        #
        # if sound_library == "accordion":
        #     self.decrescendo_duration = 0.2
        #
        # if sound_library == "carillon":
        #     self.decrescendo_duration = 0.8
        #
        # if sound_library == "custom_synthetiser":
        #     self.decrescendo_duration = 0.2
        #
        # if sound_library == "piano":
        #     self.decrescendo_duration = 0.3

        self.keyboard_configuration = configuration

        if self.keyboard_configuration == "single_chromatic_keyboard":
            self.keys_to_notes = single_chromatic_keyboard.keyboard
        elif self.keyboard_configuration == "double_chromatic_keyboard":
            self.keys_to_notes = double_chromatic_keyboard.keyboard
        elif self.keyboard_configuration == "double_chords_keyboard":
            self.keys_to_notes = double_chords_keyboard.keyboard
        else:
            raise Exception("Configuration not understood.")

    #  Notes to frequencies
    def get_freq_from_note(self, note):
        if note == "None":
            return [0]
        elif note[-2] in ['M', 'm']:
            note_index = self.gamme.index(note[:-2])
            note_scale = eval(note[-1]) - 1  # constant to adjust scale
            accord_freqs = [440 * 2 ** ((note_scale - 3) + (note_index - 9) / 12)]
            if note[-2] == 'm':
                accord_freqs.append(440 * 2 ** ((note_scale - 3) +
                                                (note_index + 3 - 9) / 12))
            if note[-2] == 'M':
                accord_freqs.append(440 * 2 ** ((note_scale - 3) +
                                                (note_index + 4 - 9) / 12))
            accord_freqs.append(440 * 2 ** ((note_scale - 3) + (note_index + 7 - 9) / 12))
            return accord_freqs
        else:
            note_index = self.gamme.index(note[:-1])
            note_scale = eval(note[-1]) - 1  # constant to adjust scale
            note_freq = 440 * 2 ** ((note_scale - 3) + (note_index - 9) / 12)
            return [note_freq]

    #   Keyboard monitoring
    def get_note_from_key(self, key):
        try:
            if key in self.keys_to_notes.keys():
                note = self.keys_to_notes[key]
            elif key.char in self.keys_to_notes.keys():
                note = self.keys_to_notes[key.char]
            return note
        except Exception:
            return 'None'

    def get_sound_from_freq(self, sample_time):
        new_sound = 0 * sample_time
        harmonics = self.get_harmonics(self.sound_library)

        for key, press_time, initial_volume, current_volume \
                in self.crescendo_beginning:
            self.buttons_crescendo[key] = [press_time,
                                           initial_volume,
                                           current_volume]
        self.crescendo_beginning = []

        for key, press_time, initial_volume, current_volume \
                in self.decrescendo_beginning:
            self.buttons_decrescendo[key] = [press_time,
                                             initial_volume,
                                             current_volume]
        self.decrescendo_beginning = []

        for key in self.buttons_stabilised:
            note = self.get_note_from_key(key)
            frequencies = self.get_freq_from_note(note)
            for frequency in frequencies:
                new_sound += np.sin(2 * np.pi * sample_time * frequency)
                for alpha_n, power in harmonics:
                    new_sound += power * np.sin(2 * np.pi *
                                                sample_time * frequency * alpha_n)

        for key in self.buttons_crescendo:
            press_time, initial_volume, current_volume = \
                self.buttons_crescendo[key]
            volume = 1 - (1 - initial_volume) * \
                     np.exp(-(time.time() - press_time) / self.crescendo_duration)
            self.buttons_crescendo[key][2] = volume
            note = self.get_note_from_key(key)
            frequencies = self.get_freq_from_note(note)
            for frequency in frequencies:
                new_sound += volume * np.sin(2 * np.pi * sample_time * frequency)
                for alpha_n, power in harmonics:
                    new_sound += volume * power * \
                                 np.sin(2 * np.pi * sample_time * frequency * alpha_n)
            if volume > 0.99:
                self.crescendo_ended.append(key)

        for key in self.crescendo_ended:
            self.buttons_crescendo.pop(key, None)
            if key not in self.buttons_decrescendo:
                self.buttons_stabilised.append(key)
        self.crescendo_ended = []
        dfinal = copy.deepcopy(self.buttons_decrescendo)
        for key in dfinal:
            release_time, initial_volume, current_volume = \
                self.buttons_decrescendo[key]
            volume = initial_volume * \
                     np.exp(-(time.time() - release_time) / self.decrescendo_duration)
            self.buttons_decrescendo[key][2] = volume
            note = self.get_note_from_key(key)
            frequencies = self.get_freq_from_note(note)
            for frequency in frequencies:
                new_sound += volume * np.sin(2 * np.pi * sample_time * frequency)
                for alpha_n, power in harmonics:
                    new_sound += volume * power * \
                                 np.sin(2 * np.pi * sample_time * frequency * alpha_n)
            if volume < 0.01:
                self.decrescendo_ended.append(key)

        for key in self.decrescendo_ended:
            self.buttons_decrescendo.pop(key, None)
        self.decrescendo_ended = []

        return new_sound

    def on_press(self, key):
        # print(key)
        note = self.get_note_from_key(key)
        # frequency = self.get_freq_from_note(note)

        if key not in self.buttons_crescendo.keys() \
                and key not in self.buttons_stabilised:
            volume = 0
            if key in self.buttons_decrescendo:
                self.decrescendo_ended.append(key)
                volume = self.buttons_decrescendo[key][2]
            self.crescendo_beginning.append([key,
                                             time.time(),
                                             volume,
                                             volume])
            # self.keys_pressed.append(key)
            self.notes_played.append(note)
        if key == Key.space and not self.switcher_pressed \
                and "double" in self.keyboard_configuration:
            self.keyboard_configuration = "double_chords_keyboard" \
                if self.keyboard_configuration == "double_chromatic_keyboard" \
                else "double_chromatic_keyboard"
            exec(f"self.keys_to_notes={self.keyboard_configuration}.keyboard")
            self.switcher_pressed = True

    def on_release(self, key):
        note = self.get_note_from_key(key)
        # frequency = self.get_freq_from_note(note)

        if key not in self.buttons_decrescendo.keys():
            volume = 1
            if key in self.buttons_crescendo:
                self.crescendo_ended.append(key)
                volume = self.buttons_crescendo[key][2]
            self.decrescendo_beginning.append([key,
                                               time.time(),
                                               volume,
                                               volume])
            self.buttons_decrescendo[key] = [time.time(), volume, volume]
            # self.keys_pressed.remove(key)
            self.notes_played.remove(note)
            if key in self.buttons_stabilised:
                self.buttons_stabilised.remove(key)

        if key == Key.space and self.switcher_pressed:
            self.switcher_pressed = False

        if key == Key.esc:
            self.end = True
            return False

    def get_harmonics(self, instrument):
        if instrument == "diapason":
            harmonics = []

        if instrument == "carillon":
            harmonics = [(0.5, 0.552), (1.2, 0.75), (1.5, 0.08), (2, 0.88),
                         (2.5, 0.12), (2.6, 0.05), (2.7, 0.15), (3, 0.47),
                         (3.3, 0.08), (3.7, 0.06), (5.1, 0.11), (6.3, 0.19),
                         (7.6, 0.1), (8.7, 0.03)]

        if instrument == "accordion":
            harmonics = [(2.0, 0.18), (3.0, 1.11), (4.0, 0.47), (5.0, 0.20),
                         (6.0, 0.36), (7.0, 0.48), (8.0, 0.22), (9.0, 0.13),
                         (10.0, 0.06), (11.0, 0.054), (12.0, 0.045),
                         (13.0, 0.036), (14.0, 0.038), (16.0, 0.027),
                         (17.0, 0.033), (18.0, 0.033)]

        if instrument == "custom_synthetiser":
            harmonics = [(0.5, 0.7), (1.5, 0.6), (2.0, 0.5), (2.5, 0.14),
                         (3.0, 1.11), (4.0, 0.47), (5.0, 0.20), (6.0, 0.36),
                         (7.0, 0.48), (8.0, 0.22), (9.0, 0.13), (10.0, 0.06),
                         (11.0, 0.054)]

        if instrument == "piano":
            harmonics = [(2.0, 0.4), (3.0, 0.2), (4.0, 0.08), (5.0, 0.05),
                         (6.0, 0.02), (7.0, 0.01)]

        return harmonics

    # Continuously called callback
    def sound_generation_callback(self, outdata, frames, time, status):
        print("Notes played : ", self.notes_played)
        t = ((self.start_idx + np.arange(frames))
             / self.sample_rate).reshape(-1, 1)
        self.start_idx += frames  # frames = 384
        outdata[:] = self.volume * self.get_sound_from_freq(t)


#   MAIN
if __name__ == "__main__":
    # "diapason", "accordion", "carillon", "custom_synthetiser"
    # "single", "double"
    my_accordion = Accordion(sound_library="piano",
                             configuration="double_chords_keyboard")

    with sd.OutputStream(channels=2,
                         callback=my_accordion.sound_generation_callback,
                         samplerate=my_accordion.sample_rate):
        while not my_accordion.end:
            time.sleep(0.1)
