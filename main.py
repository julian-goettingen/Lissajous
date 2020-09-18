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

class LissMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()
        self.show()
        self.run()

    def initUI(self):

        self.firstFreq = freqSelector(np.linspace(400,600,10), "first freq\n(x-axis)", 0)
        self.sndFreq = freqSelector(np.linspace(400,600,10), "snd freq\n(y-axis)", 90)

        lo = QVBoxLayout()

        lo.addWidget(self.firstFreq)
        lo.addWidget(self.sndFreq)

        self.mainVis = mainVisual()
        lo.addWidget(self.mainVis)

        central = QWidget()
        central.setLayout(lo)
        self.setCentralWidget(central)

    def run(self):

        self.t = QTimer()
        self.t.start(0.001)
        self.t.timeout.connect(self.plot_next)


    def plot_next(self):

        x = self.firstFreq.generate_data()
        y = self.sndFreq.generate_data()

        self.mainVis.accept_new_data_point(x,y)

class mainVisual(FigureCanvasQTAgg):

    def __init__(self):
        self.fig = Figure((2, 2), 100)
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)
        # self.axes.set_xlim(-1,1)
        # self.axes.set_ylim(-1,1)
        self.axes.set_aspect('equal')

        self.maxdata = 300
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
        self.axes.plot(self.x_data, self.y_data)
        self.fig.canvas.draw()



class freqSelector(QWidget):

    def __init__(self, freqlist, labeltext, initial_phase_offset):

        self.time = 0
        self.timestep = 0.0003
        self.phase_offset = 0
        self.amplitudes = np.zeros(freqlist.shape)
        self.freqlist = freqlist

        super().__init__()
        lo = QHBoxLayout()

        info = QVBoxLayout()

        info.addWidget(QLabel(labeltext))

        phase = QHBoxLayout()
        s = QSpinBox()
        s.setMinimum(0); s.setMaximum(360)
        s.setSingleStep(5)
        s.valueChanged.connect(self.set_phase)
        s.setValue(initial_phase_offset)
        phase.addWidget(QLabel("phase offset"))
        phase.addWidget(s)
        info.addLayout(phase)

        lo.addLayout(info)


        for i, f in enumerate(freqlist):
            slide_lo = QVBoxLayout()
            s = QSlider()
            s.setMinimum(0)
            s.setMaximum(100)
            s.setOrientation(Qt.Vertical)
            slide_lo.addWidget(s)
            l = QLabel(str(int(round(f,0))))
            act = partial(self.set_amplitude, freq_index=i)
            s.valueChanged.connect(act)
            s.setValue(90 if i==0 or i==2 or i==4 else 5)
            slide_lo.addWidget(l)
            lo.addLayout(slide_lo)

        self.setLayout(lo)
        self.setFixedHeight(120)


    def set_amplitude(self, new_amp, freq_index):

        self.amplitudes[freq_index] = new_amp

    def set_phase(self, new_phase):

        assert(0 <= new_phase <= 360)
        self.phase_offset = new_phase


    def generate_data(self):

        val = 0
        for f,a in zip(self.freqlist, self.amplitudes):
            val += a*np.sin(f*self.time+(self.phase_offset)*(2*np.pi/360))

        self.time += self.timestep

        return val

if __name__ == "__main__":

    app = QApplication(sys.argv)
    mw = LissMainWindow()
    exit(app.exec())

