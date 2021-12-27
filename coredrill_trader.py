import os
import kivy
import ccxt.async_support as ccxt_async
import asyncio
import threading
from kivy.clock import mainthread
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.config import Config
from kivy.event import EventDispatcher
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

    def change_tx_amount(self, instance):
        print(instance.text)

    def change_tx_direction(self, instance):
        print(instance.text)

    def clear_pressed(self):
        print('Clear pressed')
        self.reset_buttons()

    def close_position(self):
        print('Close position pressed')


class EventLoopWorker(EventDispatcher):
    __events__ = ('on_pulse',)

    def __init__(self):
        super().__init__()
        self._thread = threading.Thread(target=self._run_loop)  # note the Thread target here
        self._thread.daemon = True
        self.loop = None
        # the following are for the pulse() coroutine, see below
        self._default_pulse = ['tick!', 'tock!']
        self._pulse = None
        self._pulse_task = None

    def _run_loop(self):
        self.loop = asyncio.get_event_loop_policy().new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._restart_pulse()
        # add cleanup code for tearing down event loop here
        self.loop.run_forever()

    def start(self):
        self._thread.start()

class CoreDrill(MDApp):

    async def fetch_position(self) -> dict:
        positions, account, funding = await asyncio.gather(
            self.exchange.fapiPrivate_get_positionrisk(params={'symbol': 'ETHUSDT'}),
            self.exchange.fapiPrivate_get_account(),
            self.exchange.fapiPublic_get_fundingrate()
        )
        if positions:
            position = {'size': float(positions[0]['positionAmt']),
                        'price': f"{float(positions[0]['entryPrice']):.2f}",
                        'liquidation_price': f"{float(positions[0]['liquidationPrice']):.2f}",
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
                position['funding_time'] = float(e['fundingTime'])
                position['predicted_funding_rate'] = float(e['fundingRate'])
                break
        for e in account['assets']:
            if e['asset'] == 'USDT':
                position['margin_cost'] = f"{float(e['positionInitialMargin']):.2f}"
                position['margin_ratio'] = f"{(float(e['maintMargin']) / float(e['marginBalance']))*100:.2f}%"
                position['equity'] = float(e['marginBalance'])
                position['wallet_balance'] = f"{float(e['walletBalance']):.2f} USDT"
                position['available_balance'] = f"{float(e['availableBalance']):.2f} USDT"
                position['pos_pnl_pct'] = ((float(e['positionInitialMargin'])+float(position['pos_pnl']) - float(e['positionInitialMargin'])) / float(e['positionInitialMargin'])) * 100.0
                break
        position['asset_price'] = ""
        self.pepe = position
        return position

    def init_ccxt(self):
        self.exchange = getattr(ccxt_async, 'binance')({'apiKey': key,
                                            'secret': secret,
                                            'options': {'defaultType': 'future'}})
        asyncio.run(self.fetch_position())

    def toggle_interface(self, state):
        self.root.ids.amount_small.disabled = not state
        self.root.ids.amount_medium.disabled = not state
        self.root.ids.amount_large.disabled = not state
        self.root.ids.long_btn.disabled = not state
        self.root.ids.short_btn.disabled = not state
        self.root.ids.clear_btn.disabled = not state
        self.root.ids.execute_btn.disabled = not state

    def reset_buttons(self):
        self.root.ids.amount_small.state = "normal"
        self.root.ids.amount_medium.state = "normal"
        self.root.ids.amount_large.state = "normal"
        self.root.ids.long_btn.state = "normal"
        self.root.ids.short_btn.state = "normal"

    def execute_pressed(self):
        print('Execute pressed')

        pulse_listener_labels = {
            "size": self.root.ids.pos_size,
            "price": self.root.ids.entry_price,
            "liquidation_price": self.root.ids.liq_price,
            "margin_cost": self.root.ids.pos_margin,
            "pos_pnl": self.root.ids.pos_pnl,
            "wallet_balance": self.root.ids.balance_full,
            "available_balance": self.root.ids.balance_available,
            "asset_price": self.root.ids.asset_price,
            "margin_ratio": self.root.ids.margin_ratio
        }

        for key in pulse_listener_labels:
            colored_text = ["size", "pos_pnl"]
            if key in colored_text:
                if self.pepe[key] > 0:
                    pulse_listener_labels[key].color = get_color_from_hex('#0ecb81')
                elif self.pepe[key] < 0:
                    pulse_listener_labels[key].color = get_color_from_hex('#d70c25')
                else:
                    pulse_listener_labels[key].color = get_color_from_hex('#ffffff')

            if key == "size":
                pulse_listener_labels[key].text = f"{self.pepe[key]:.3f} ETH"
            elif key == "pos_pnl":
                pulse_listener_labels[key].text = f"{self.pepe['pos_pnl']:.2f}({self.pepe['pos_pnl_pct']:.2f}%)"
            else:
                pulse_listener_labels[key].text = str(self.pepe[key])

        self.reset_buttons()

    def connect_exchange(self, instance):
        #TODO: proper credential check and connection logic
        has_credentials = True

        if not has_credentials:
            instance.active = False
            print(f'Initialise credentials here: {instance.active}')
        elif has_credentials and instance.active:
            self.root.ids.connection_status.text = "Connecting..."
            #try:
            self.init_ccxt()
            self.toggle_interface(instance.active)
            self.root.ids.connection_status.text = "Connected"
            #except Exception as e:
            #    print('Error connecting to exchange', e)

        else:
            self.root.ids.connection_status.text = "Connect"
            self.toggle_interface(instance.active)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_loop_worker = None

    def build(self):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        Window.size = (1024, 600)

        if not os.path.exists(config_path):
            os.makedirs(config_path)
            print("Created configuration folder.")

        return DashboardLayout()

    def start_event_loop_thread(self):
        if self.event_loop_worker is not None:
            return
        print("Running the asyncio EventLoop now...\n\n\n\n")
        self.event_loop_worker = worker =  EventLoopWorker()

        pulse_listener_labels = {
            "size": self.root.ids.pos_size,
            "price": self.root.ids.entry_price,
            "liquidation_price": self.root.ids.liq_price,
            "margin_cost": self.root.ids.pos_margin,
            "pos_pnl": self.root.ids.pos_pnl,
            "wallet_balance": self.root.ids.balance_full,
            "available_balance": self.root.ids.balance_available,
            "asset_price": self.root.ids.asset_price,
            "margin_ratio": self.root.ids.margin_ratio
        }

        def display_on_pulse(instance, position):
            for key in pulse_listener_labels:
                pulse_listener_labels[key].text = position[key]

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
