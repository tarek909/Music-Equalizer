import logging
import time as ti
import io
from threading import Thread
import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib import animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from numpy import arange
from pylab import subplots
import my_accordion as instrument
from scipy.fft import rfft, rfftfreq, irfft
from scipy.io import wavfile
from scipy.io.wavfile import write
from PIL import Image
from vlc import MediaPlayer, Media

sg.theme('Reddit')
PLAY_SONG_IMAGE_PATH = 'play_button.png'
PAUSE_SONG_IMAGE_PATH = 'pause.png'
PIANO_IMAGE_PATH = 'piano.png'
CARILLON_IMAGE_PATH = 'carillon.png'
ACCORDION_IMAGE_PATH = 'accf.png'
Piano_path = 'piano.png'
double_bass_path = 'doublebass.png'
trumpet_path = 'trumbet.png'
sub_Bass_path = 'bass.png'
electronic_path = 'electronic.png'
plt.style.use('dark_background')
MusicPlayerLeftFigure, MusicPlayerLeftWindowAxis = plt.subplots(figsize=(5, 2))
MusicPlayerRightFigure, MusicPlayerRightFigureAxis = subplots(figsize=(5, 2))
EmphasizerLeftFigure, EmphasizerLeftFigureAxis = plt.subplots(nrows=2, constrained_layout=True)
EmphasizerRightFigure, EmphasizerRightFigureAxis = subplots(nrows=2, constrained_layout=True)
mediaplay = MediaPlayer()
music_start = 0


def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw_idle()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


def pause(event1, anim):
    if event1 == 'Pause':
        if anim.running:
            anim.event_source.stop()
            anim.running ^= True
        else:
            anim.event_source.start()
            anim.running = True


def audiodata(filename):
    file = filename
    sampleRate, audioBuffer = wavfile.read(file)
    duration = len(audioBuffer) / sampleRate
    time = arange(0, duration, 1 / sampleRate)
    if audioBuffer.shape[0] != audioBuffer.size:
        audioBuffer = audioBuffer[:, 0]
    return audioBuffer, time, sampleRate, duration


def main():
    global music_start
    logging.basicConfig(filename='DEBUGMUSIC.log', format='%(asctime)s %(message)s', level=logging.DEBUG)
    logging.getLogger('matplotlib.font_manager').disabled = True
    sg.theme('Dark Green4')
    canvas1 = sg.Column([[sg.Canvas(size=(470, 100), key='-CANVAS-')]])
    canvas2 = sg.Column([[sg.Canvas(size=(470, 100), key='-CANVAS2-')]])
    ElementJustification = 'center'
    EmphasizerLayOut = [
        [sg.Text('Musical Instruments Emphasizer', size=(95, 1), justification=ElementJustification,
                 font=("Amatic SC", 35))],
        [sg.Button('Open File', font=("Amatic SC", 15)),
         sg.Image(filename=PLAY_SONG_IMAGE_PATH, size=(64, 64), pad=(10, 0), enable_events=True, key='Play1',
                  background_color='black'),
         sg.Image(filename=PAUSE_SONG_IMAGE_PATH, size=(58, 58), pad=(10, 0), enable_events=True, key='Pause1',
                  background_color='black')],
        [sg.Pane([canvas1, canvas2], key='pane', orientation='h', size=(250, 175))],
        [sg.Text('Select The Instruments That You Want To Emphasize', font=("Amatic SC", 17), size=(50, 1),
                 justification=ElementJustification)],
        [sg.Image(filename=Piano_path, size=(58, 58), pad=(15, 0), enable_events=True, key='PianoIcon',
                  background_color='black'),
         sg.Slider(orientation='vertical', key='PianoGain', range=(0.0, 10.0), resolution=0.1, default_value=1.0,
                   pad=(10, 10), size=(7, 12), disable_number_display=True, border_width=2),
         sg.Image(filename=double_bass_path, size=(58, 58), pad=(15, 0), enable_events=True, key='GuitarIcon',
                  background_color='black'),
         sg.Slider(orientation='vertical', key='GuitarGain', range=(0.0, 10.0), resolution=0.1, default_value=1.0,
                   pad=(10, 10), size=(7, 12), disable_number_display=True, border_width=2),
         sg.Image(filename=trumpet_path, size=(58, 58), pad=(15, 0), enable_events=True, key='DrumIcon',
                  background_color='black'),
         sg.Slider(orientation='vertical', key='DrumGain', range=(0.0, 10.0), resolution=0.1, default_value=1.0,
                   pad=(10, 30), size=(7, 12), disable_number_display=True, border_width=2),
         sg.Image(filename=sub_Bass_path, size=(58, 58), pad=(15, 0), enable_events=True, key='BassIcon',
                  background_color='black'),
         sg.Slider(orientation='vertical', key='BassGain', range=(0.0, 10.0), resolution=0.1, default_value=1.0,
                   pad=(10, 30), size=(7, 12), disable_number_display=True, border_width=2),
         sg.Image(filename=electronic_path, size=(58, 58), pad=(15, 0), enable_events=True, key='FemaleVoiceIcon',
                  background_color='black'),
         sg.Slider(orientation='vertical', key='FemaleVoiceGain', range=(0.0, 10.0), resolution=0.1, default_value=1.0,
                   pad=(10, 30), size=(7, 12), disable_number_display=True, border_width=2)]]
    AudioPlayerLayout = [
        [sg.Text('AudioPlayer', size=(20, 1), justification='center', font=("Amatic SC", 35), background_color='black',
                 text_color='white')],
        [sg.Canvas(size=(20, 20), key='-CANVAS3-'), sg.Canvas(size=(19, 20), key='-CANVAS4-')],
        [sg.Image(filename=PLAY_SONG_IMAGE_PATH, size=(64, 64), pad=(10, 0), enable_events=True, key='Play',
                  background_color='black'),
         sg.Image(filename=PAUSE_SONG_IMAGE_PATH, size=(58, 58), pad=(10, 0), enable_events=True, key='Pause',
                  background_color='black')],
        [sg.Slider(orientation='horizontal', key='Volume Level', range=(0, 100),
                   enable_events=True)],
        [sg.Button('Play Music', button_color='black', font=("Amatic SC", 15))]]
    InstrumentsLayout = [
        [sg.Text('Instrument Player', size=(53, 1), justification='center', font=("Amatic SC", 35),
                 background_color='white',
                 text_color='black')],
        [sg.Image(filename=PIANO_IMAGE_PATH, size=(64, 64), pad=(10, 0), enable_events=True, key='piano',
                  background_color='white'),
         sg.Image(filename=CARILLON_IMAGE_PATH, size=(64, 64), pad=(10, 0), enable_events=True, key='carillon',
                  background_color='white'),
         sg.Image(filename=ACCORDION_IMAGE_PATH, size=(64, 64), pad=(10, 0), enable_events=True, key='accordion',
                  background_color='white')],
        [sg.Image(key="-IMAGE-")]]
    FinalLayout = [
        [sg.TabGroup(
            [[sg.Tab('AudioPlayer', AudioPlayerLayout, key='-mykey-', background_color='black', title_color='black',
                     element_justification='center')],
             [sg.Tab('MusicalEmphasizer', EmphasizerLayOut, key='-mykey2-', background_color='black',
                     title_color='black', element_justification='center')],
             [sg.Tab('MusicalInstruments', InstrumentsLayout, key='-mykey3-', background_color='white',
                     title_color='black', element_justification='center')]], size=(1200, 680),
            key='Tab')]]

    window = sg.Window('AudioPlayer', layout=FinalLayout, size=(1200, 680), background_color='black', finalize=True,
                       grab_anywhere=True, resizable=True, auto_size_text=True,
                       auto_size_buttons=True, element_justification='center')

    MusicPlayerLeftFigureAgg = draw_figure(window['-CANVAS3-'].TKCanvas, MusicPlayerLeftFigure)
    MusicPlayerRightFigureAgg = draw_figure(window['-CANVAS4-'].TKCanvas, MusicPlayerRightFigure)
    EmphasizerLeftFigureAgg = draw_figure(window['-CANVAS-'].TKCanvas, EmphasizerLeftFigure)
    EmphasizerRightFigureAgg = draw_figure(window['-CANVAS2-'].TKCanvas, EmphasizerRightFigure)
    window.bind('<Configure>', 'Event')

    lowfreq = [1000, 500, 0, 6000, 2000]
    highfreq = [2000, 1000, 500, 20000, 6000]

    def animatedplot(y_axis, x_axis, Time):
        def animate(frame):
            global music_start
            MusicPlayerLeftWindowAxis.cla()
            frame = round((ti.perf_counter() - music_start) / Time * len(x_axis))
            MusicPlayerLeftWindowAxis.plot(x_axis[int(0.6 * frame):frame], y_axis[int(0.6 * frame):frame],
                                           color='white')

        anim = animation.FuncAnimation(MusicPlayerLeftFigure, animate,
                                       frames=[i for i in range(len(x_axis))], interval=1)
        MusicPlayerLeftFigure.canvas.mpl_connect('button_press_event', pause)
        anim.running = True
        MusicPlayerLeftFigureAgg.draw_idle()
        return anim

    def Fourier(signal, sampleRate):
        signalFrequencies = rfft(signal)
        signalFrequenciesAbs = abs(signalFrequencies)
        signalFreqbins = rfftfreq(signal.size, 1 / sampleRate)
        return signalFrequencies, signalFreqbins, signalFrequenciesAbs

    def graph_spectrogram(sound_info, frame_rate, axis, figagg):
        axis.cla()
        axis.specgram(sound_info, Fs=frame_rate)
        figagg.draw_idle()

    def ReadFile():
        file_path = sg.popup_get_file('Choose Your Music', no_window=True, file_types=(("WAV Files", "*.wav"),))
        sampleRate, signal = wavfile.read(file_path)
        return sampleRate, signal

    def Equalizer_fourreir(sampleRate, signal, lowfreq, highfreq, gain_arr):
        EmphasizerLeftFigureAxis[0].cla()
        EmphasizerLeftFigureAxis[1].cla()
        signal = signal / (pow(2.0, 15))
        if signal.shape[0] != signal.size:
            signal = signal[:, 0]  # work with 1 channel
        signalFrequencies, signalFreqBins, signalFreqAbs = Fourier(signal, sampleRate)
        EmphasizerLeftFigureAxis[0].plot(signalFreqBins, signalFrequencies)
        EmphasizerLeftFigureAxis[0].set_title('Original Signal')
        graph_spectrogram(signal, sampleRate, EmphasizerRightFigureAxis[0], EmphasizerRightFigureAgg)
        for index, frequency in enumerate(signalFreqBins):
            for i in range(len(highfreq)):
                if (lowfreq[i] <= frequency <= highfreq[i]) and (signalFrequencies[index] != 0):
                    signalFrequencies[index] = signalFrequencies[index] * gain_arr[i]
        EmphasizerLeftFigureAxis[1].plot(signalFreqBins, signalFrequencies)
        EmphasizerLeftFigureAxis[1].set_title('Filtered Signal')
        newsong = irfft(signalFrequencies)
        graph_spectrogram(newsong, sampleRate, EmphasizerRightFigureAxis[1], EmphasizerRightFigureAgg)
        EmphasizerLeftFigureAgg.draw_idle()
        write("newSong.wav", sampleRate, newsong)

    def display_image(image_path):
        image = Image.open(image_path)
        image.thumbnail((700, 700))
        bio = io.BytesIO()
        image.save(bio, format="PNG")
        window["-IMAGE-"].update(data=bio.getvalue())

    def playinstru(event):
        my_accordion = instrument.Accordion(sound_library=event,
                                            configuration="double_chords_keyboard")
        with instrument.sd.OutputStream(channels=2,
                                        callback=my_accordion.sound_generation_callback,
                                        samplerate=my_accordion.sample_rate):
            while not my_accordion.end:
                ti.sleep(0.1)

    while True:
        event, values = window.read()
        logging.info('Gui Event Loop Started')
        if event in (sg.WIN_CLOSED, None):
            logging.info('Closed Main Window')
            exit(0)
        if event == 'Play Music':
            try:
                file_path = sg.popup_get_file('Choose Your Music', no_window=True, file_types=(("WAV Files", "*.wav"),))
                audioda, time, fs, length = audiodata(file_path)
                media = Media(file_path)
                MusicPlayerRightFigureAgg.flush_events()
                Thread(target=graph_spectrogram,
                       args=[audioda, fs, MusicPlayerRightFigureAxis, MusicPlayerRightFigureAgg], daemon=True).start()
            except:
                logging.error('You DID NOT add a file yet!')
                pass
        if event == 'Open File':
            sampleRate, signal = ReadFile()
        if event == 'Play':
            if mediaplay.is_playing():
                pass
            else:
                try:
                    mediaplay.set_media(media)
                    mediaplay.play()
                    music_start = ti.perf_counter()
                    MusicPlayerLeftFigureAgg.flush_events()
                    logging.info('Starting Animation Frame')
                    anim = animatedplot(audioda, time, length)
                    logging.info('Finished Animation Frame')
                except:
                    logging.error('You DID NOT add a file yet! so you are basically playing nothing')
                    pass
        if event == 'Pause':
            if mediaplay.is_playing():
                mediaplay.pause()
                start = ti.time()
                try:
                    pause(event, anim)
                except:
                    logging.error('You can NOT pause when you did not add a file yet!')
                    pass
            else:
                end = ti.time()
                music_start = music_start + (end - start)
                pause(event, anim)
                mediaplay.pause()
        if event == 'Play1':
            media = Media('newSong.wav')
            gain_arr = [values['PianoGain'], values['GuitarGain'], values['BassGain'], values['FemaleVoiceGain'],
                        values['DrumGain']]
            Equalizer_fourreir(sampleRate, signal, lowfreq, highfreq, gain_arr)
            if mediaplay.is_playing():
                pass
            else:
                mediaplay.set_media(media)
                mediaplay.play()
        if event == 'Pause1':
            if mediaplay.is_playing():
                mediaplay.pause()
            else:
                mediaplay.pause()
        if event == 'Volume Level':
            mediaplay.audio_set_volume(int(values['Volume Level']))
        if event == 'Event':
            window['pane'].expand(True, True)
            window['-CANVAS3-'].expand(True, True)
            window['-CANVAS4-'].expand(True, True)
            window['Tab'].expand(True, True)
        if event == "piano":
            display_image('A-piano-with-the-keys-labeled.jpg')
            FirstTime = Thread(target=playinstru, args=[event], daemon=True)
            FirstTime.start()
        if event == "carillon":
            display_image('carrillon.jpg')
            SecondTime = Thread(target=playinstru, args=[event], daemon=True)
            SecondTime.start()
        if event == "accordion":
            display_image('accordion.jpg')
            ThirdTime = Thread(target=playinstru, args=[event], daemon=True)
            ThirdTime.start()
    window.close()


if __name__ == '__main__':
    main()
