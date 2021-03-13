import sys
import os
import psutil
import argparse
import signal
import threading

from utils import config
from utils import listener
from utils import http_proxy

from gui import main_ui
from gui import add_service
from gui import delete_service

from gui import main_ui as gui
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QWidget, QPushButton, QFileDialog
from PyQt5.QtCore import QThread, QObject, QTimer
from functools import partial

global SERVICE_LIST
global WAIT_EVENT
WAIT_EVENT = threading.Event()
SERVICE_LIST = []

def close_services():
    global SERVICE_LIST
    global WAIT_EVENT
    WAIT_EVENT.set()

    print("")
    print("Exiting Application...")
    for service in SERVICE_LIST:
        service.stop()
        sys.stdout.write(".")
        sys.stdout.flush()

    sys.stdout.write("\n")
    return


def signal_handler(sig, frame):
    close_services()

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

        self.config_file = ''
        self.timer = QTimer()
        self.timer.timeout.connect(self.ui_updater)
        self.timer.start(1000)

    def run(self):
        global SERVICE_LIST
        self.ui.addService.clicked.connect(self.as_onclick)
        self.ui.deleteService.clicked.connect(self.ds_onclick)
        self.ui.importConfig.clicked.connect(self.import_onclick)
        self.ui.browseFile.clicked.connect(self.browse_onclick)

        self.MainWindow.show()
        self.app.exec_()

        SERVICE_LIST += self.service_list
        close_services()

    def ui_updater(self):
        self.ui.cpuLoad.setText(str(psutil.cpu_percent()) + "%")
        self.ui.memLoad.setText(str(psutil.virtual_memory().percent) + "%")

    def update_console(self, text_value):
        self.ui.consoleOutput.append(text_value)

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

    def import_onclick(self):
        if self.config_file == '':
            self.update_console("No chosen file")
            return
        try:
            c = config.read_config(self.config_file)
            t_service_list = config.extract_services(c)
            self.service_list += t_service_list
            self.update_table(self.service_list)

        except Exception as e:
            self.update_console("Error importing {}".format(os.path.basename(self.config_file)))
            return

        self.update_console("Imported: {}".format(os.path.basename(self.config_file)))

    def browse_onclick(self):
        dlg = QFileDialog()
        filename,_ = QFileDialog.getOpenFileName(dlg, "Browse Configuration file","./", "Config file *.ini(*.ini);; Any file *.*(*.*)")
        if filename != '':
            self.config_file = filename
            self.update_console("Set config file as {}".format(os.path.basename(self.config_file)))

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
            self.update_console("TCP Listener Server added.")
        else:
            service = http_proxy.HTTPProxyServer(input_port=bind_port,
                                                workers=num_workers)
            self.update_console("HTTP Proxy Server added.")

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
        if index < 0:
            return
        self.service_list.pop(index)
        self.update_table(self.service_list)
        self.update_console("Deleted server at index {}".format(index))

        self.dService.close()

    def ds_cancel_onclick(self):
        self.dService.close()

def main():
    global SERVICE_LIST
    global WAIT_EVENT
    parser = argparse.ArgumentParser(description = "Port Forwarder")
    parser.add_argument('-f', '--file' , help='The config.ini file. Set this file to automatically import the file.', type=str)
    parser.add_argument('-n', '--nogui', help='Sets the application to run on the command line only. Must specify config file when set', action='store_true')

    args = parser.parse_args()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if(args.nogui == True):
        if args.file == None:
            print("Error, config file not set!")
            print("Config file must be set with --nogui mode.")
            return

        if not(os.path.exists(args.file)):
            print("Error, config file does not exist!")
            return

        try:
            c = config.read_config(args.file)
            SERVICE_LIST += config.extract_services(c)
        except Exception as e:
            print("Error reading config file!")
            return

        for service in SERVICE_LIST:
            service.start()
            type_of_service = "TCP Port Forward" if type(service) == listener.ListenerServer else "HTTP Proxy Server"
            print("Started running {}.".format(type_of_service))
            print("Running on port: {}".format(service.input_port))

            if type(service) == listener.ListenerServer:
                print("Target IP: {}".format(service.target_ip))
                print("Target Port: {}".format(service.target_port))
            print("-------")

        print("All services are running...")
        WAIT_EVENT.wait()

    else:
        main_window = MainWindow()
        
        if args.file != None and os.path.exists(args.file):
            main_window.config_file = args.file
            main_window.import_onclick()

        main_window.run()

if __name__ == '__main__':
    main()