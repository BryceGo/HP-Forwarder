import sys
from utils import listener



def main():
    x = listener.ListenerServer(6000, '127.0.0.1', 3000)

    x.start_eternal_loop()

    pass


if __name__ == '__main__':
    main()
