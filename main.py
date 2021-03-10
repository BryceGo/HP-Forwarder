import sys
from utils import listener
from utils import http_proxy

from gui import main_ui

from gui import main_ui as gui
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QWidget
from PyQt5.QtCore import QThread, QObject, QTimer

def update_table(service_list, table):
    table.clearContents()
    for service in service_list:
        pos = table.rowCount()
        table.insertRow(pos)

        table.setItem(pos, 0,  QtGui.QTableWidgetItem(str(pos)))

        if type(service) == listener.ListenerServer:
            table.setItem(pos, 1,  QtGui.QTableWidgetItem("TCP Port Forward"))
            table.setItem(pos, 2,  QtGui.QTableWidgetItem(str(service.input_port)))
            table.setItem(pos, 3,  QtGui.QTableWidgetItem(str(service.target_ip)))
            table.setItem(pos, 4,  QtGui.QTableWidgetItem(str(service.target_port)))
            table.setItem(pos, 5,  QtGui.QTableWidgetItem(str(service.stop_flag.is_set())))
        else:
            table.setItem(pos, 1,  QtGui.QTableWidgetItem("HTTP Proxy Server"))
            table.setItem(pos, 2,  QtGui.QTableWidgetItem(str(service.input_port)))
            table.setItem(pos, 3,  QtGui.QTableWidgetItem("-"))
            table.setItem(pos, 4,  QtGui.QTableWidgetItem(str(80)))
            table.setItem(pos, 5,  QtGui.QTableWidgetItem(str(service.stop_flag.is_set())))
    return

class MainWindow(QObject):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = QtWidgets.QMainWindow()
        self.ui = main_ui.Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)
        self.table = self.ui.tableWidget

        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        for i in range(1, self.ui.tableWidget.columnCount()):
            self.ui.tableWidget.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

        self.ui.tableWidget.setHorizontalHeaderLabels(["Number", "Type", "Bound Port", "Target IP", "Target Port", "Status"])

        self.service_list = []
        self.service_list.append(listener.ListenerServer(5000, '127.0.0.1', 300))
        self.service_list.append(listener.ListenerServer(5001, '127.0.0.1', 301))
        self.service_list.append(listener.ListenerServer(5002, '127.0.0.1', 302))
        update_table(self.service_list, self.table)
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.ui_updater)
        # self.timer.start(500)

    def run(self):
        # self.ui.b_start.clicked.connect(self.start_onclick)
        # self.ui.b_stop.clicked.connect(self.stop_onclick)
        # self.ui.b_reload.clicked.connect(self.reload_onclick)

        # self.ui.s_drop_rate.sliderReleased.connect(self.set_drop_rate)
        # self.ui.s_delay_rate.sliderReleased.connect(self.set_delay_rate)
        # self.ui.s_delay.sliderReleased.connect(self.set_delay)

        # self.ui.s_drop_rate.valueChanged.connect(self.print_drop_rate)
        # self.ui.s_delay_rate.valueChanged.connect(self.print_delay_rate)
        # self.ui.s_delay.valueChanged.connect(self.print_delay)

        self.MainWindow.show()
        sys.exit(self.app.exec_())

    # def start_onclick(self):
    #     self.network_emulator.stop = False
    #     self.network_emulator.start()
    #     self.terminal_queue.put("Start button pressed.")

    # def stop_onclick(self):
    #     self.network_emulator.stop_services()
    #     self.terminal_queue.put("Stop button pressed.")

    # def reload_onclick(self):
    #     settings.initialize("EMULATOR")
    #     self.terminal_queue.put("Reloading configuration...")

    # # Drop Rate
    # def set_drop_rate(self):
    #     value = self.ui.s_drop_rate.value()/10
    #     self.network_emulator.set_drop_rate(value)
    #     print(value)

    # def print_drop_rate(self):
    #     value = self.ui.s_drop_rate.value()/10
    #     self.ui.l_drop_rate.setText(str(value) + " %")

    # # Packet Delay Rate
    # def set_delay_rate(self):
    #     value = self.ui.s_delay_rate.value()/10
    #     self.network_emulator.set_packet_delay(value)

    # def print_delay_rate(self):
    #     value = self.ui.s_delay_rate.value()/10
    #     self.ui.l_delay_rate.setText(str(value) + " %")

    # # Delay in ms
    # def set_delay(self):
    #     value = self.ui.s_delay.value()
    #     self.network_emulator.set_delay(value)

    # def print_delay(self):
    #     value = self.ui.s_delay.value()
    #     self.ui.l_delay.setText(str(value) + " ms")

    # def ui_updater(self):
    #     if self.network_emulator.isRunning():
    #         self.ui.l_status.setText("STATUS: RUNNING")
    #     else:
    #         self.ui.l_status.setText("STATUS: NOT RUNNING")

    #     while not(self.graph1_queue.empty()) or not(self.graph2_queue.empty()):
    #         if not(self.graph1_queue.empty()):
    #             value = self.graph1_queue.get()
    #             self.graph1_y.append(value)
    #             self.graph1_y.pop(0)

    #         if not(self.graph2_queue.empty()):
    #             value = self.graph2_queue.get()
    #             self.graph2_y.append(value)
    #             self.graph2_y.pop(0)
    #     self.curve1.setData(self.graph1_x, self.graph1_y)
    #     self.curve2.setData(self.graph2_x, self.graph2_y)

    #     # Terminal Updater
    #     while not(self.terminal_queue.empty()):
    #         data = self.terminal_queue.get()

    #         if data == 'Packet dropped':
    #             self.drop_count += 1
    #             continue

    #         if data == 'Packet delayed':
    #             self.delay_count += 1
    #             continue

    #         if data == 'EOT packet detected. Services switching...':
    #             self.eot_count += 1

    #         self.ui.terminal.append(data)

    #     self.ui.l_dropped.setText("Packets Dropped: {}".format(self.drop_count))
    #     self.ui.l_delayed.setText("Packets Delayed: {}".format(self.delay_count))
    #     self.ui.l_eot.setText("EOT Packets Detected: {}".format(self.eot_count))


if __name__ == '__main__':
    main_window = MainWindow()
    main_window.run()