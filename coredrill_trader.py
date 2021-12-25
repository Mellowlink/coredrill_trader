import os
import kivy
import ccxt.async_support as ccxt_async
import asyncio
import threading
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.core.window import Window

config_path = './config'
layout_path = 'layouts/default.kv'

class DashboardLayout(Widget):

    connection_status = ObjectProperty(None)
    connection_switch = ObjectProperty(None)

    balance_full = ObjectProperty(None)
    balance_available = ObjectProperty(None)

    asset_price = ObjectProperty(None)
    margin_ratio = ObjectProperty(None)

    amount_small = ObjectProperty(None)
    amount_medium = ObjectProperty(None)
    amount_large = ObjectProperty(None)

    long_btn = ObjectProperty(None)
    short_btn = ObjectProperty(None)

    pending_tx_size = ObjectProperty(None)
    pending_tx_margin = ObjectProperty(None)

    clear_btn = ObjectProperty(None)

    execute_btn = ObjectProperty(None)

    pos_size = ObjectProperty(None)
    entry_price = ObjectProperty(None)
    liq_price = ObjectProperty(None)
    pos_margin = ObjectProperty(None)
    pos_pnl = ObjectProperty(None)
    close_pos_btn = ObjectProperty(None)

    def reset_buttons(self):
        self.amount_small.state = "normal"
        self.amount_medium.state = "normal"
        self.amount_large.state = "normal"
        self.long_btn.state = "normal"
        self.short_btn.state = "normal"

    def toggle_interface(self, state):
        self.amount_small.disabled = not state
        self.amount_medium.disabled = not state
        self.amount_large.disabled = not state
        self.long_btn.disabled = not state
        self.short_btn.disabled = not state
        self.clear_btn.disabled = not state
        self.execute_btn.disabled = not state


    def connect_exchange(self, instance):
        #TODO: proper credential check and connection logic
        has_credentials = True

        if not has_credentials:
            instance.active = False
            print(f'Initialise credentials here: {instance.active}')
        elif has_credentials and instance.active:
            #try init exchange here
            print(f'OK to connect: {instance.active}')
            self.toggle_interface(instance.active)

            #exception handling here
        else:
            print(f'Connection off: {instance.active}')
            self.toggle_interface(instance.active)


    def change_tx_amount(self, instance):
        print(instance.text)

    def change_tx_direction(self, instance):
        print(instance.text)

    def clear_pressed(self):
        print('Clear pressed')
        self.reset_buttons()

    def execute_pressed(self):
        print('Execute pressed')
        self.reset_buttons()

    def close_position(self):
        print('Close position pressed')


class CoreDrill(MDApp):

    async def fetch_position(self) -> dict:
        positions, account, funding = await asyncio.gather(
            self.exchange.fapiPrivate_get_positionrisk(params={'symbol': 'ETHUSDT'}),
            self.exchange.fapiPrivate_get_account(),
            self.exchange.fapiPublic_get_fundingrate()
        )
        if positions:
            print('Position: \n') #test
            print(positions[0]) #test
            print('\n') #test
            position = {'size': float(positions[0]['positionAmt']),
                        'price': float(positions[0]['entryPrice']),
                        'liquidation_price': float(positions[0]['liquidationPrice']),
                        'pos_pnl': float(positions[0]['unRealizedProfit']),
                        'leverage': float(positions[0]['leverage'])}
        else:
            position = {'size': 0.0,
                        'price': 0.0,
                        'liquidation_price': 0.0,
                        'pos_pnl': 0.0,
                        'leverage': 1.0}
        for e in funding:
            if e['symbol'] == 'ETHUSDT':
                print('Funding: \n') #test
                print(e) #test
                print('\n') #test
                position['funding_time'] = float(e['fundingTime'])
                position['predicted_funding_rate'] = float(e['fundingRate'])
                break
        for e in account['assets']:
            if e['asset'] == 'USDT':
                print('Account: \n') #test
                print(e) #test
                print('\n') #test
                position['margin_cost'] = float(e['positionInitialMargin'])
                position['margin_ratio'] = float(e['maintMargin']) / float(e['marginBalance'])
                position['equity'] = float(e['marginBalance'])
                position['wallet_balance'] = float(e['walletBalance'])
                position['available_balance'] = float(e['availableBalance'])
                break
        print('Final position: \n') #test
        print(position) #test
        print('\n') #test

    def init_ccxt(self):
        self.exchange = getattr(ccxt_async, 'binance')({'apiKey': key,
                                            'secret': secret,
                                            'options': {'defaultType': 'future'}})
        asyncio.run(self.fetch_position())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_loop_worker = None

    def build(self):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        Window.size = (1024, 600)

        if not os.path.exists(config_path):
            os.makedirs(config_path)
            print("Created configuration folder.")

        self.init_ccxt()

        return DashboardLayout()

    def start_event_loop_thread(self):
        if self.event_loop_worker is not None:
            return
        print("Running the asyncio EventLoop now...\n\n\n\n")
        self.event_loop_worker = worker =  EventLoopWorker()
        #TODO: create labels object here
        #pulse_listener_label = self.root.ids.pulse_listener
        pulse_listener_labels = {
            "pos_size": self.root.ids.pos_size,
            "entry_price": self.root.ids.entry_price,
            "liq_price": self.root.ids.liq_price,
            "pos_margin": self.root.ids.pos_margin,
            "pos_pnl": self.root.ids.pos_pnl,
            "balance_full": self.root.ids.balance_full,
            "balance_available": self.root.ids.balance_available,
            "asset_price": self.root.ids.asset_price,
            "margin_ratio": self.root.ids.margin_ratio
        }

        def display_on_pulse(instance, text):
            pulse_listener_labels["pos_size"].text = text
            pulse_listener_labels["entry_price"].text = text
            pulse_listener_labels["liq_price"].text = text
            pulse_listener_labels["pos_margin"].text = text
            pulse_listener_labels["pos_pnl"].text = text
            pulse_listener_labels["balance_full"].text = text
            pulse_listener_labels["balance_available"].text = text
            pulse_listener_labels["asset_price"].text = text
            pulse_listener_labels["margin_ratio"].text = text

        # make the label react to the worker's `on_pulse` event:
        worker.bind(on_pulse=display_on_pulse)
        worker.start()

    def submit_pulse_text(self, text):
        worker = self.event_loop_worker
        if worker is not None:
            loop = self.event_loop_worker.loop
            # use the thread safe variant to run it on the asyncio event loop:
            loop.call_soon_threadsafe(worker.set_pulse_text, text)

if __name__ == '__main__':
    Builder.load_file(layout_path)
    CoreDrill().run()
