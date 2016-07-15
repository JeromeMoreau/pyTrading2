import oandapy
from events import TickEvent
import calendar
from datetime import datetime

class Streaming(oandapy.Streamer):
    def __init__(self,instruments_list,account,data_handler,event_handler):
        """

        :param instruments_list:
        :param account:
        :param data_handler:
        :param event_handler:
        :return:
        """
        super(Streaming,self).__init__(environment=account.environment,access_token=account.token)
        self.instruments_list = instruments_list
        self.account=account
        self.data_handler = data_handler
        self.event_handler = event_handler

    def add_instrument(self,instrument):
        # Used by data_handler to add an instrument to instrument_list
        self.instruments_list.append(instrument)

    def stream_prices(self):
        self.rates(account_id=self.account.id,instruments=str(','.join(self.instruments_list)))

    def stream_events(self):
        self.events(ignore_heartbeat=False)

    def on_success(self, data):
        if 'tick' in data:
            time=datetime.strptime(data['tick']['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
            params={'instrument':data['tick']['instrument'],
                    'time':time,
                    'bid':data['tick']['bid'],
                    'ask':data['tick']['ask'],
                    'epoch':int(calendar.timegm(time.timetuple()))}
            tick_event=TickEvent(**params)
            self.data_handler.process_tick(tick_event)

        elif 'transaction' in data:
            print('received event')
            self.event_handler.process_event(data.get('transaction'))

    def on_error(self, data):
        print('Streaming: Error with the feed: %s' %data)