from utils import listener
from utils import http_proxy
import configparser

def read_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return config

def extract_services(config):
    service_list = []
    for server in config.keys():
        service = None
        try:
            if config[server]['TYPE'].lower() == 'TCPFORWARD'.lower():
                bind_port = int(config[server]['BIND_PORT'])
                target_ip = config[server]['TARGET_IP']
                target_port = int(config[server]['TARGET_PORT'])
                workers = int(config[server]['WORKERS']) if 'WORKERS' in config[server] else 10

                service = listener.ListenerServer(input_port=bind_port,
                                                    target_ip=target_ip,
                                                    target_port=target_port,
                                                    workers=workers)

            elif config[server]['TYPE'].lower() == 'HTTPPROXY'.lower():
                bind_port = int(config[server]['BIND_PORT'])
                workers = int(config[server]['WORKERS']) if 'WORKERS' in config[server] else 10

                service = http_proxy.HTTPProxyServer(input_port=bind_port,
                                                    workers=workers)

            else:
                print("Error, unknown type from config server {}".format(server))
                continue

            service_list.append(service)

        except Exception as e:
            if server != "DEFAULT":
                print("Error in service {}".format(server))
            continue
    return service_list




