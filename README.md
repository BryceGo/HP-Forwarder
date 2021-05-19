# HP Forwarder
[![license](https://img.shields.io/github/license/mashape/apistatus.svg?maxAge=2592000)](./LICENSE)

# Description
HP Forwarder is an HTTP Proxy and Port Forwarder Server that uses an epoll edge triggered solution to provide a highly scalable server.
The server provides a multi-threaded solution that can handle up to 7000 simulataneous connections.

# Environment
- Python 3.8.5
- Ubuntu 20.04 LTS

Other versions of Linux would also work but have not been tested.

# Usage
The application can be run in gui mode or non-gui mode.
### User Interface
To run the application using the gui, use the following command.
```
sudo python3 port_forwarder.py
```
Once run, a user interface will show up.

[Insert picture here]
Click on the Add Service button to create a service and specify its parameters.
[Insert picture with Add Service Dialog]
You can specify 2 options, the TCP Port forwarder or the HTTP Proxy server.
You can set the desired options and click the create button.

### Non-Gui Mode
To run the forwarder without the gui, you must prepare a configuration file to tell the application the types of servers to start.

Below is a sample config file.
```
[Sample TCP Port Forward Server]
TYPE = TCPFORWARD
BIND_PORT = 6000
TARGET_IP = 192.168.1.90
TARGET_PORT = 6001
WORKERS = 30

[Sample HTTP Proxy Server]
TYPE = HTTPPROXY
BIND_PORT = 6001
WORKERS = 30
```
The values are:
- TYPE - Sets the type of service, TCPFORWARD or HTTPPROXY. TCPFORWARD for a TCP port forward service while HTTPROXY for an HTTP proxy service
- BIND_PORT - Sets the listening port number of the service
- TARGET_IP - Sets the target server’s IP address
- TARGET_PORT - Sets the target server’s port number
- WORKERS - Sets the number of threads to provide

The first stanza tells the program to create a TCP Port forwarding server from the ```TYPE``` attribute. On the other hand, the second stanza would be an HTTP proxy server.

Once you've made the configuration file, save it as a .ini file.
You can now run the port_forwarder without the gui using:
```
sudo python3 port_forwarder.py --file {ini_file} --nogui
```

You can also open the help menu by passing the -h parameter. 
The full parameter list is shown below:
```
Usage: sudo python3 port_forwarder.py [-h] [-f FILE] [-n]

--h, --help - shows this help message
-f FILE, --file FILE - specifies the config.ini file. When paired in GUI mode, this option loads the all the services in the config file.
-n, --nogui - sets the application to run in non-gui mode. When this is set, the --file option must be set as well.
```
