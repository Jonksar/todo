import os
import sys
from threading import Event
from PyQt4.QtGui import *
from PyQt4 import QtCore
from enum import Enum
from LaptopDemo import LaptopSyncDemo

class Status(Enum):
    locked = 0
    unlocked = 1

def clamp(val, min_, max_):
    return min(max_, max(val, min_))

def linear_interp(y0, y1, t):
    t = clamp(t, 0, 1)
    return y0 + (y1 - y0) * t

def smooth_interp(y0, y1, t):
    t = clamp(t, 0, 1)
    return linear_interp(y0, y1, t**2 * (3 - 2 * t))


class DesktopDemoWindow(QWidget):
    MAX_OPACITY = 1


    def __init__(self, fps=60, demo=None):
        super(DesktopDemoWindow, self).__init__()

        # Screen variables
        screen_resolution = app.desktop().screenGeometry()

        def clamp(value, minvalue, maxvalue):
            return max(minvalue, min(value, maxvalue))

        def linear_interp(y0, y1, t):
            t = clamp(t, 0, 1)
            return y0 + t * (y1 - y0)

        self.sc_width = screen_resolution.width()
        self.sc_height = screen_resolution.height()

        # resources
        self.pixmap_unlocked = QPixmap('res/16labDemoUnlocked2.png').scaled(self.sc_width, self.sc_height)
        self.pixmap_locked = QPixmap('res/16labDemoLocked2.png').scaled(self.sc_width, self.sc_height)

        # Updating variables
        self.fps = fps
        self._xmap_unlocked = QPixmap('res/16labDemoUnlocked2.png').scaled(self.sc_width, self.sc_height)
        self._update_time = 1000 / fps

        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self._update)
        self.update_timer.start(self._update_time)

        # The higher level control variables
        self.lock_event = Event()
        self.state = Status.locked

        # Widget variables
        self.transition_speed = 500
        self.progress_timer = QtCore.QElapsedTimer()
        self.progress_timer.start()

        self.true_progress = 0
        self.visible_progress = 0

        self.target_progress = self.MAX_OPACITY
        self.started_progess = 0

        # Setting up data input settings
        self.demo = demo
        self.demo.set_event_ref(event_ref=self.lock_event)

        # Demo update
        self.demo_update_timer = QtCore.QTimer()
        self.demo_update_timer.timeout.connect(self.demo.update)
        self.demo_update_timer.start(5)

        # Setting up the window itself
        self.label_unlocked = QLabel(self)
        self.label_unlocked.setPixmap(self.pixmap_unlocked)
        self.label_unlocked.setGraphicsEffect(self.gen_opacity_effect(self.target_progress))

        self.setWindowTitle("16lab laptop demo")
        self.label_locked = QLabel(self)
        self.label_locked.setPixmap(self.pixmap_locked)
        self.label_locked.setGraphicsEffect(self.gen_opacity_effect(self.started_progess))

        self.painter = QPainter()

        self.resize(self.sc_width, self.sc_height)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
        elif e.key() == QtCore.Qt.Key_T:
            self.lock_event.set()
        elif e.key() == QtCore.Qt.Key_F11:
            if not self.isFullScreen():
                self.showFullScreen()

                # Screen variables
                screen_resolution = app.desktop().screenGeometry()
                self.sc_width = screen_resolution.width()
                self.sc_height = screen_resolution.height()

                # resources
                self.pixmap_unlocked = QPixmap('res/16labDemoUnlocked2.png').scaled(self.sc_width, self.sc_height)
                self.pixmap_locked = QPixmap('res/16labDemoLocked2.png').scaled(self.sc_width, self.sc_height)

                self.label_locked.setPixmap(self.pixmap_locked)
                self.label_unlocked.setPixmap(self.pixmap_unlocked)

                self.resize(self.sc_width, self.sc_height)
            else:
                self.showMaximized()


    def _update(self):
        # Handle lock_event
        if self.lock_event.is_set():
            self.lock_event.clear()

            self._set_internal_vars()

        self._fade_anim()

    def _set_internal_vars(self):
        # Case when we are locked atm
        if self.state == Status.locked:
            # Switch up the internal variables
            self.state = Status.unlocked
            self.target_progress = 0

        # Case when we are unlocked atm
        elif self.state == Status.unlocked:
            # Switch up the internal variables
            self.state = Status.locked
            self.target_progress = self.MAX_OPACITY

            # Continue from current visible progress
        self.started_progess = self.visible_progress
        self.progress_timer.start()

    def _fade_anim(self):
        self.true_progress = float(self.progress_timer.elapsed()) / self.transition_speed
        self.visible_progress = smooth_interp(self.started_progess, self.target_progress, self.true_progress)

        self.label_locked.setGraphicsEffect(self.gen_opacity_effect(self.visible_progress))

    def gen_opacity_effect(self, amount):
        opacity_fx = QGraphicsOpacityEffect()
        opacity_fx.setOpacity(amount)

        return opacity_fx

if __name__ == '__main__':
    # Create window
    app = QApplication(sys.argv)

    # Creates bluetooth connection with 2 devices on threads
    # And provides dataframes to save the data & analyze function
    demo = LaptopSyncDemo()

    # Window for displaying the results.
    layout = QStackedLayout()


