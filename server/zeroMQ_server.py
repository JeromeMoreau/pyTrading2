import time
import zmq
import pandas as pd
import threading

class ZMQServer(object):
    def __init__(self,portfolio,port='5555'):

        self.portfolio = portfolio
        self.alive = False

        self.socket,self.context = self._create_socket(port)

    def _create_socket(self,port):
        context = zmq.Context.instance()
        socket = context.socket(zmq.REP)
        socket.bind('tcp://*:'+port)
        print('Socket created on port %s' %port)

        return socket,context

    def startAsync(self):
        self.alive = True
        zmq_thread = threading.Thread(target=self._start_server)
        zmq_thread.start()

    def _start_server(self):

        while self.alive==True:

            try:
                message = self.socket.recv(zmq.NOBLOCK)
                time.sleep(5)
                print("Received request: %s" % message)
                #Send reply to the client
                if message == b'test_connection':
                    self.socket.send_string("Connection OK")
                if message == b'get_trades': self.get_opened_trades()
                if message == b'close_server': self.CloseServer()


            except:
                pass

        print('Server closing socket')
        self.socket.close()
        self.context.term()

    def CloseServer(self):
        print("Stoping the server")
        self.alive = False
        if(self.socket.closed == False):
            self.socket.close()
        if self.zmq_thread and self.zmq_thread.is_alive() == True:
            self.zmq_thread.join()



    def get_opened_trades(self):
        portfolio_trades = self.portfolio.trades

        trades = pd.DataFrame(data= ((tr.ticket, tr.strategy, tr.open_date, tr.instrument, tr.side, tr.open_price,
                                      tr.stop_loss, tr.units, tr.close_date, tr.close_price, tr.MAE, tr.MFE,
                                      tr.pnl) for tr in portfolio_trades),
                                           columns=['ticket','strategy','open_date','symbol','direction',
                                                    'open_price','stop_loss','units','close_date',
                                                    'close_price','MAE','MFE','profit'])

        self.socket.send_pyobj(trades)