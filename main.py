import sys
from utils import listener
from utils import http_proxy

from gui import main_ui
from gui import add_service
from gui import delete_service

from gui import main_ui as gui
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QWidget, QPushButton
from PyQt5.QtCore import QThread, QObject, QTimer
from functools import partial

class MainWindow(QObject):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.app = QtWidgets.QApplication(sys.argv)
        self.MainWindow = QtWidgets.QMainWindow()
        self.ui = main_ui.Ui_MainWindow()
        self.ui.setupUi(self.MainWindow)
        self.table = self.ui.tableWidget

        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        for i in range(2, self.ui.tableWidget.columnCount()):
            self.ui.tableWidget.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)

        self.ui.tableWidget.setHorizontalHeaderLabels(["Number", "Type", "Bound Port", "Target IP", "Target Port", "Status", "Start/Stop"])

        self.service_list = []

        # self.service_list.append(listener.ListenerServer(5000, '127.0.0.1', 300))
        # self.service_list.append(listener.ListenerServer(5001, '127.0.0.1', 301))
        # self.service_list.append(http_proxy.HTTPProxyServer(5002))
        # self.update_table(self.service_list)
        # self.service_list.pop(0)
        # self.update_table(self.service_list)

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

        self.ui.addService.clicked.connect(self.as_onclick)
        self.ui.deleteService.clicked.connect(self.ds_onclick)

        self.MainWindow.show()
        sys.exit(self.app.exec_())

    def update_table(self, service_list):
        num_rows = self.table.rowCount()
        for i in range(0,num_rows):
            self.table.removeRow(0)

        for service in service_list:
            pos = self.table.rowCount()
            self.table.insertRow(pos)

            self.table.setItem(pos, 0,  QtWidgets.QTableWidgetItem(str(pos)))

            if type(service) == listener.ListenerServer:
                self.table.setItem(pos, 1,  QtWidgets.QTableWidgetItem("TCP Port Forward"))
                self.table.setItem(pos, 2,  QtWidgets.QTableWidgetItem(str(service.input_port)))
                self.table.setItem(pos, 3,  QtWidgets.QTableWidgetItem(str(service.target_ip)))
                self.table.setItem(pos, 4,  QtWidgets.QTableWidgetItem(str(service.target_port)))
            else:
                self.table.setItem(pos, 1,  QtWidgets.QTableWidgetItem("HTTP Proxy Server"))
                self.table.setItem(pos, 2,  QtWidgets.QTableWidgetItem(str(service.input_port)))
                self.table.setItem(pos, 3,  QtWidgets.QTableWidgetItem("-"))
                self.table.setItem(pos, 4,  QtWidgets.QTableWidgetItem(str(80)))

            btn = QPushButton(self.table)
            if service.stop_flag.is_set():
                btn.setText("Start")
                self.table.setItem(pos, 5,  QtWidgets.QTableWidgetItem("Stopped"))
                btn.clicked.connect(partial(self.start_onclick, service))
            else:
                btn.setText("Stop")
                self.table.setItem(pos, 5,  QtWidgets.QTableWidgetItem("Running"))
                btn.clicked.connect(partial(self.stop_onclick, service))

            self.table.setCellWidget(pos, 6, btn)
        return

    def start_onclick(self, service):
        service.start()
        self.update_table(self.service_list)

    def stop_onclick(self, service):
        service.stop()
        self.update_table(self.service_list)

    def as_onclick(self):
        self.aService = QtWidgets.QDialog()
        self.ui_as = add_service.Ui_aService()
        self.ui_as.setupUi(self.aService)
        self.ui_as.typeBox.addItems(['TCP Port Forward', 'HTTP Proxy Server'])

        self.ui_as.create.clicked.connect(self.as_create_onclick)
        self.ui_as.cancel.clicked.connect(self.as_cancel_onclick)
        self.aService.show()

    def as_create_onclick(self):
        type_of_service = self.ui_as.typeBox.currentIndex()
        bind_port = self.ui_as.bindPort.value()
        target_ip = self.ui_as.targetIP.text()
        target_port = self.ui_as.targetPort.value()
        num_workers = self.ui_as.workerNumber.value()

        if type_of_service == 0:
            service = listener.ListenerServer(input_port=bind_port,
                                    target_ip=target_ip,
                                    target_port=target_port,
                                    workers=num_workers)
        else:
            service = http_proxy.HTTPProxyServer(input_port=bind_port,
                                                workers=num_workers)

        self.service_list.append(service)
        self.update_table(self.service_list)
        self.aService.close()

    def as_cancel_onclick(self):
        self.aService.close()

    def ds_onclick(self):
        self.dService = QtWidgets.QDialog()
        self.ui_ds = delete_service.Ui_dService()
        self.ui_ds.setupUi(self.dService)

        count = 0
        for service in self.service_list:
            type_service = "Port Forward" if type(service) == listener.ListenerServer else "HTTP Proxy"
            self.ui_ds.comboBox.addItem("Number: {}, Type: {}, Bound Port: {}". format(count, type_service, service.input_port))
            count += 1

        self.ui_ds.dButton.clicked.connect(self.ds_delete_onclick)
        self.ui_ds.cButton.clicked.connect(self.ds_cancel_onclick)
        self.dService.show()

    def ds_delete_onclick(self):
        index = self.ui_ds.comboBox.currentIndex()
        self.service_list.pop(index)
        self.update_table(self.service_list)

        self.dService.close()

    def ds_cancel_onclick(self):
        self.dService.close()

if __name__ == '__main__':
    main_window = MainWindow()
    main_window.run()