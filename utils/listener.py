import select
import socket
import threading
import errno

class ListenerServer:

    def __init__(self, input_port, target_ip, target_port, workers = 10):
        self.input_port = input_port
        self.target_ip = socket.gethostbyname(target_ip)
        self.target_port = target_port

        self.bind_epoll = select.epoll()
        self.bind_socket = None
        self.inbound_connections = {}
        self.outbound_connections = {}

        self.inbound_epoll = select.epoll()
        self.outbound_epoll = select.epoll()

        self.stop_flag = threading.Event()
        self.stop_flag.set()

        self.inbound_workers = []
        self.outbound_workers = []

        self.number_of_workers= workers
        self.main_thread = None


    @staticmethod
    def create_connection(ip_address, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((ip_address, port))
            sock.setblocking(0)

            return sock
        except Exception as e:
            return -1

    def receive_and_send(self, sock, recv_list, send_list):
        while True:
            try:
                msg = sock.recv(2048)

                if msg == b'':
                    self.close_sockets(sock, recv_list, send_list)
                    return

            except Exception as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                        return
                break

            try:
                if not(sock.fileno() in recv_list):
                    return

                sock, out_sock = recv_list[sock.fileno()]
                out_sock.send(msg)
            except Exception as e:
                return

    def close_sockets(self, sock, recv_list, send_list):
        if sock.fileno() == -1:
            # File is already closed.
            return

        if sock.fileno() in recv_list:
            try:
                sock, out_sock = recv_list[sock.fileno()]
                del recv_list[sock.fileno()]
                sock.close()
            except Exception as e:
                # Must have been deleted already.
                return
        else:
            return


        if out_sock.fileno() in send_list:
            try:
                del send_list[out_sock.fileno()]
                out_sock.close()
            except Exception as e:
                # Must have been deleted already.
                pass


    def worker_thread(self, inbound=True, max_events= 500):
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
                    self.receive_and_send(sock, recv_list, send_list)
                elif event & (select.EPOLLERR | select.EPOLLHUP):
                    self.close_sockets(sock, recv_list, send_list)
                else:
                    print("Warning Unknown event detected.", fd, event)


    def start_eternal_loop(self):
        events = select.EPOLLIN | select.EPOLLET
        inbound_events = select.EPOLLIN | select.EPOLLET | select.EPOLLERR | select.EPOLLHUP | select.EPOLLEXCLUSIVE
        outbound_events = select.EPOLLIN | select.EPOLLET | select.EPOLLERR | select.EPOLLHUP | select.EPOLLEXCLUSIVE

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
                    sock.setblocking(0)
                    out_sock = self.create_connection(self.target_ip, self.target_port)
                    if out_sock == -1:
                        sock.close()
                        continue

                    self.outbound_connections[out_sock.fileno()] = [out_sock, sock]
                    self.inbound_connections[sock.fileno()] = [sock, out_sock]

                    self.outbound_epoll.register(out_sock.fileno(), outbound_events)
                    self.inbound_epoll.register(sock.fileno(), inbound_events)

                except Exception as e:
                    if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                        break
                    raise e
        self.bind_socket.close()

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

        if self.main_thread != None:
            self.main_thread.join()
            self.main_thread = None

    def get_inbound_connections(self):
        return len(self.inbound_connections)

    def get_outbound_connections(self):
        return len(self.outbound_connections)