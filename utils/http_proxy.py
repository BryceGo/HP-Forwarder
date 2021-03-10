from http.server import BaseHTTPRequestHandler
from io import BytesIO
import select
import socket
import threading
import errno
import sys

class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message

class HTTPProxyServer:
    def __init__(self, input_port, workers = 10):
        self.input_port = input_port

        self.bind_epoll = select.epoll()
        self.bind_socket = None
        self.inbound_connections = {}
        self.outbound_connections = {}

        self.inbound_epoll = select.epoll()
        self.outbound_epoll = select.epoll()

        self.stop_flag = threading.Event()

        self.inbound_workers = []
        self.outbound_workers = []

        self.number_of_workers= workers
        self.main_thread = None

    @staticmethod
    def create_connection(msg, port=80):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            request = HTTPRequest(msg)
        except Exception as e:
            print("Could not parse request")
            return None

        try:
            sock.connect((socket.gethostbyname(request.headers['host']), port))
            sock.setblocking(0)
            return sock
        except Exception as e:
            raise e
            return None

    def receive_and_send(self, sock, recv_list, send_list, inbound=True):
        outbound_events = select.EPOLLIN | select.EPOLLET | select.EPOLLERR | select.EPOLLHUP | select.EPOLLEXCLUSIVE
        while True:
            try:
                msg = sock.recv(2048)

                if msg == b'':
                    self.close_socket(sock, recv_list)
                    return
            except Exception as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                    return

            try:
                if not(sock.fileno() in recv_list):
                    return

                if inbound==False:
                    sock, out_sock = recv_list[sock.fileno()]
                    out_sock.sendall(msg)
                else:
                    out_sock = self.create_connection(msg)

                    if out_sock == None:
                        # self.close_socket(sock, recv_list)
                        self.close_sockets(out_sock, recv_list, send_list)
                        return

                    self.outbound_epoll.register(out_sock.fileno(), outbound_events)
                    self.outbound_connections[out_sock.fileno()] = [out_sock, sock]
                    self.inbound_connections[sock.fileno()][1].append(out_sock)
                    out_sock.sendall(msg)

            except Exception as e:
                return

    def close_sockets(self, sock, recv_list, send_list):
        if sock.fileno() == -1:
            return

        if sock.fileno() in recv_list:
            for out_sock in recv_list[sock.fileno()][1]:
                try:
                    del send_list[out_sock.fileno()]
                    out_sock.close()
                except Exception as e:
                    continue
        else:
            return
        self.close_socket(sock, recv_list)

    def close_socket(self, sock, recv_list):
        if sock.fileno() == -1:
            # File is already closed.
            return

        if sock.fileno() in recv_list:
            try:
                del recv_list[sock.fileno()]
                sock.close()
            except Exception as e:
                return
        return

    def worker_thread(self, inbound=True, max_events=500):
        if inbound == True:
            epoll = self.inbound_epoll
            recv_list = self.inbound_connections
            send_list = self.outbound_connections
        else:
            epoll = self.outbound_epoll
            recv_list = self.outbound_connections
            send_list = self.inbound_connections

        while not(self.stop_flag.is_set()):
            event_list = epoll.poll(timeout=1, maxevents=max_events)

            if self.stop_flag.is_set() == True:
                break

            for fd, event in event_list:
                try:
                    sock, out_sock = recv_list[fd]
                except Exception as e:
                    # Must have been deleted
                    continue

                if event & (select.EPOLLIN):
                    self.receive_and_send(sock, recv_list, send_list, inbound)
                elif event & (select.EPOLLERR | select.EPOLLHUP):
                    # self.close_socket(sock, recv_list)
                    if inbound == True:
                        self.close_sockets(sock, recv_list, send_list)
                    else:
                        self.close_socket(sock, recv_list)
                else:
                    print("Warning Unknown event detected.", fd, event)


    def start_eternal_loop(self):
        events = select.EPOLLIN | select.EPOLLET
        inbound_events = select.EPOLLIN | select.EPOLLET | select.EPOLLERR | select.EPOLLHUP | select.EPOLLEXCLUSIVE
        
        self.bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind_socket.setblocking(0)
        self.bind_socket.bind(('0.0.0.0', self.input_port))
        self.bind_socket.listen(socket.SOMAXCONN)

        self.bind_epoll.register(self.bind_socket.fileno(), events)

        while not(self.stop_flag.is_set()):
            event_list = self.bind_epoll.poll(1)

            if self.stop_flag.is_set() == True:
                break

            if len(event_list) == 0:
                continue

            while True:
                try:
                    sock, address = self.bind_socket.accept()

                    # Register to the invound epoll instance
                    self.inbound_epoll.register(sock.fileno(), inbound_events)
                    self.inbound_connections[sock.fileno()] = [sock, []]

                except Exception as e:
                    if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                        break
                    raise e


    def start(self):
        self.stop_flag.clear()

        for i in range(0,self.number_of_workers):
            self.inbound_workers.append(threading.Thread(target=self.worker_thread, args=(True, 500)))
            self.outbound_workers.append(threading.Thread(target=self.worker_thread, args=(False, 500)))

            self.inbound_workers[-1].start()
            self.outbound_workers[-1].start()

        self.main_thread = threading.Thread(target=self.start_eternal_loop)
        self.main_thread.start()

    def stop(self):
        self.stop_flag.set()
        for i in self.inbound_workers:
            i.join()
        self.inbound_workers.clear()

        for i in self.outbound_workers:
            i.join()
        self.outbound_workers.clear()

        self.main_thread.join()
        self.main_thread = None

    def get_inbound_connections(self):
        return len(self.inbound_connections)

    def get_outbound_connections(self):
        return len(self.outbound_connections)