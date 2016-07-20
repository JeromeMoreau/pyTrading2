import time
import zmq

class Server(object):
    def __init__(self,account,portfolio):

        self.account = account
        self.portfolio = portfolio

        self.socket,self.context = self._create_socket()

    def _create_socket(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind('tcp://*:5555')
        print('Socket created on port 5555')

        return socket,context

    def _start_server(self):
        while True:
            #Wait for connection
            message = self.socket.recv()
            time.sleep(1)
            #Send reply to the client
            if message == b'test_connection':
                self.socket.send_string("Connection OK")
            if message == b'get_trades':
                self.get_open_trades()

            #except:
        print('Server closing socket')
        self.socket.close()
        self.context.term()

    def get_open_trades(self):
        trades = self.portfolio.trades
        self.socket.send_pyobj(trades)