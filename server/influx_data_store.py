from influxdb import InfluxDBClient

from trade_store.base_data_store import AbstractDataStore


class InfluxAbstractDataStore(AbstractDataStore):

    def __init__(self):
        self.client = self._get_connection()

    def _get_connection(self,db_adress='localhost'):
        client = InfluxDBClient('localhost', 8086, 'root', 'root', 'trades')
        return client

    def _trade_to_json(self,trade):
        """
        Converts a trade object to its json representation
        :param trade: Trade object
        :return: trade_json
        """
        trade_json = [
            {'measurement':"trades_event",
             'tags':{'strategy':trade.strategy},
             'fields':{
                'ticket':trade.ticket,
                'side':trade.side,
                'instrument':trade.instrument,
                'units':trade.units,
                'open_price':trade.open_price,
                'open_date':trade.open_date.strftime('%m/%d/%Y'),
                'strategy':trade.strategy,
                'stop_loss':trade.stop_loss,
                'take_profit':trade.take_profit,
                'trailing_stop':trade.trailing_stop,
                'close_date': None,
                'close_price':trade.close_price,
                'pnl':trade.pnl}
             }
        ]

        if trade.close_date is None:
            trade_json[0]['fields']['close_date']=None
        else:
            trade_json[0]['fields']['close_date']= trade.close_date.strftime('%m/%d/%Y')


        return trade_json


    def add_open_trade(self,trade):
        json = self._trade_to_json(trade)
        self.client.write_points(json)


    def add_close_trade(self,trade):
        json = self._trade_to_json(trade)
        self.client.write_points(json)

    def find_trade(self,trade):
        #TODO implement find trade using rs = client.query("select * from trades") and list(rs.get_points(...)
        rs = self.client.query("SELECT * FROM trades")
        rs.get_points(measurement='trades_event')

        print("find_trade() not yet implemented")
        pass

