import numpy as np
from functools import partial
from PyQt5.QtWidgets import QMainWindow, QApplication, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QWidget, \
    QSlider, QLabel, QSpinBox
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
import sys

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class WaveParams():

    def __init__(self, offset, freqs, amps):

        self.offset = offset
        assert(freqs.shape == amps.shape)
        self.freqs = freqs
        self.amps = amps

        self.any_change_callbacks = []

    def register_any_change_callback(self, fun):

        self.any_change_callbacks.append(fun)

    def change_amp(self, new_amp, index):

        self.amps[index] = new_amp
        for f in self.any_change_callbacks:
            f()

    def change_offset(self, offset):

        self.offset = offset
        for f in self.any_change_callbacks:
            f()


class LissMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setStyleSheet("color: rgb(0,255,30); background-color : rgb(30,30,30)")
        self.initUI()
        self.show()
        self.run()

    def initUI(self):

        self.fullyInitialized = False

        sz = 13
        x_freqs = np.linspace(200,800,sz)
        y_freqs = x_freqs.copy()
        x_amps = np.array([90 if i==0 or i==2 or i==4 else 0 for i in range(sz)])
        y_amps = np.array([80 if i==1 or i==5 else 0 for i in range(sz)])
        x_offset = 0
        y_offset = 90

        self.x_wave = WaveParams(x_offset, x_freqs, x_amps)
        self.y_wave = WaveParams(y_offset, y_freqs, y_amps)

        self.x_wave.register_any_change_callback(self.replot_static)
        self.y_wave.register_any_change_callback(self.replot_static)


        self.firstFreqSelector = freqSelector(self.x_wave, "first freq\n(x-axis)")
        self.sndFreqSelector = freqSelector(self.y_wave, "snd freq\n(y-axis)")

        lo = QVBoxLayout()

        lo.addWidget(self.firstFreqSelector)
        lo.addWidget(self.sndFreqSelector)

        vis = QHBoxLayout()
        self.dynVis = dynamicVisual()
        vis.addWidget(self.dynVis)

        self.staticVis = staticVisual([],[])
        vis.addWidget(self.staticVis)

        lo.addLayout(vis)

        central = QWidget()
        central.setLayout(lo)
        self.setCentralWidget(central)

        self.fullyInitialized = True
        self.replot_static()

    def replot_static(self):

        if not self.fullyInitialized:
            return

        t = np.linspace(0,0.1,500)
        xdata = sum([a * np.sin(f * t + self.x_wave.offset) for a,f in zip(self.x_wave.amps, self.x_wave.freqs)])
        ydata = sum([a * np.sin(f * t + self.y_wave.offset) for a,f in zip(self.y_wave.amps, self.y_wave.freqs)])


        self.staticVis.replot(xdata, ydata)

    def run(self):

        self.t = QTimer()
        self.t.start(1)
        self.t.timeout.connect(self.plot_next)


    def plot_next(self):

        x = self.firstFreqSelector.generate_data()
        y = self.sndFreqSelector.generate_data()

        self.dynVis.accept_new_data_point(x, y)

class staticVisual(FigureCanvasQTAgg):

    def __init__(self, xdata, ydata):
        self.fig = Figure((200,200), 100)
        self.fig.patch.set_facecolor((0.05,0.05,0.05))
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('black')
        self.axes.set_aspect('equal')

        self.replot(xdata, ydata)

    def replot(self, xdata, ydata):

        self.axes.clear()
        self.axes.plot(xdata, ydata, color=(0,1,0.1))
        self.fig.canvas.draw()

class dynamicVisual(FigureCanvasQTAgg):

    def __init__(self):
        self.fig = Figure((200, 200), 100)
        self.fig.patch.set_facecolor((0.05,0.05,0.05))
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('black')
        self.axes.set_aspect('equal')

        self.maxdata = 100
        self.x_data = []
        self.y_data = []

    @pyqtSlot(int, int)
    def accept_new_data_point(self, x, y):

        self.x_data.append(x)
        self.y_data.append(y)
        if len(self.x_data) > self.maxdata:
            self.x_data.pop(0)
            self.y_data.pop(0)

        self.axes.clear()
        self.axes.plot(self.x_data, self.y_data, color="cyan")
        self.fig.canvas.draw()



class freqSelector(QWidget):

    def __init__(self, wave, labeltext):

        self.time = 0
        self.timestep = 0.0003

        self.wave = wave

        super().__init__()
        lo = QHBoxLayout()

        info = QVBoxLayout()

        info.addWidget(QLabel(labeltext))

        phase = QHBoxLayout()
        s = QSpinBox()
        s.setMinimum(0); s.setMaximum(360)
        s.setSingleStep(5)
        s.valueChanged.connect(self.set_phase)
        s.valueChanged.connect(wave.change_offset)
        s.setValue(wave.offset)
        phase.addWidget(QLabel("phase offset"))
        phase.addWidget(s)
        info.addLayout(phase)

        lo.addLayout(info)


        for i, f in enumerate(wave.freqs):
            slide_lo = QVBoxLayout()
            s = QSlider()
            s.setMinimum(0)
            s.setMaximum(100)
            s.setOrientation(Qt.Vertical)
            slide_lo.addWidget(s)
            l = QLabel(str(int(round(f,0))))
            act = partial(self.set_amplitude, freq_index=i)
            s.valueChanged.connect(act)
            s.setValue(wave.amps[i])
            slide_lo.addWidget(l)
            lo.addLayout(slide_lo)

        self.setLayout(lo)
        self.setFixedHeight(120)


    def set_amplitude(self, new_amp, freq_index):

        self.wave.change_amp(new_amp, freq_index)

    def set_phase(self, new_phase):

        assert(0 <= new_phase <= 360)
        self.wave.change_offset(new_phase)


    def generate_data(self):

        val = 0
        for f,a in zip(self.wave.freqs, self.wave.amps):
            val += a*np.sin(f*self.time+(self.wave.offset)*(2*np.pi/360))

        self.time += self.timestep

        return val

if __name__ == "__main__":

    app = QApplication(sys.argv)
    mw = LissMainWindow()
    exit(app.exec())

