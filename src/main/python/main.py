from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2 import QtWidgets, QtCore, QtGui, QtCore
from pypresence import Presence

import sys, traceback, time, os, ctypes

class Server(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.EnumWindows = ctypes.windll.user32.EnumWindows
        self.EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        self.GetWindowText = ctypes.windll.user32.GetWindowTextW
        self.GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        self.IsWindowVisible = ctypes.windll.user32.IsWindowVisible
        self.started = False
        self.client_id = "842383082123296799"
        self.RPC = Presence(client_id=self.client_id)
        self.title = ""
        self.threadpool = QtCore.QThreadPool()
        self.tray = QtWidgets.QSystemTrayIcon()
        self.icon = QtGui.QIcon(QtGui.QPixmap(appctxt.get_resource("server.png")))
        self.menu = QtWidgets.QMenu()
        self.exitAction = self.menu.addAction("exit")
        self.exitAction.triggered.connect(self.close)
        self.tray.setIcon(self.icon)
        self.tray.setContextMenu(self.menu)
        self.tray.show()
        self.run()

    def progress_fn(self, msg):
        for i in self.titles:
            if "- Google Chrome" in i:
                self.title = i
                self.title = self.title.replace("- Google Chrome", "")
                if not self.started:
                    self.RPC.connect()
                    self.started = True
                self.RPC.update(large_image="icon", details="Being on Chrome", state=self.title)
        if not "Google Chrome" in str(self.titles) and self.started:
            self.started = False
            self.RPC.clear()
            self.RPC.close()
                

    def run_threaded_process(self, process, progress_fn, on_complete):
        worker = Worker(fn=process)
        self.threadpool.start(worker)
        worker.signals.finished.connect(on_complete)
        worker.signals.progress.connect(progress_fn)

    def run(self):
        self.stopped = False
        self.run_threaded_process(self.test, self.progress_fn, self.completed)

    def stop(self):
        self.stopped=True
        if self.started:
                self.started = False
                self.RPC.clear()
                self.RPC.close()
        os.kill(os.getpid(), 19)

    def completed(self):
        pass

    def test(self, progress_callback):
        while not self.stopped:
            self.titles = []
            self.EnumWindows(self.EnumWindowsProc(self.foreach_window), 0)
            progress_callback.emit("k")
            time.sleep(1)
    
    def foreach_window(self, hwnd, lParam):
        if self.IsWindowVisible(hwnd):
            length = self.GetWindowTextLength(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            self.GetWindowText(hwnd, buff, length + 1)
            self.titles.append(buff.value)
        return True

    def close(self):
        self.stop()
        

class Worker(QtCore.QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.kwargs['progress_callback'] = self.signals.progress

    @QtCore.Slot()
    def run(self):
        try:
            result = self.fn(
                *self.args, **self.kwargs,
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class WorkerSignals(QtCore.QObject):
    finished = QtCore.Signal()
    error = QtCore.Signal(tuple)
    result = QtCore.Signal(object)
    progress = QtCore.Signal(int)

if __name__ == '__main__':
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    window = Server()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)