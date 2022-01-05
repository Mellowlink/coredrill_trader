import os
import kivy
import ccxt.async_support as ccxt_async
import asyncio
import pickle
import threading
from kivy.clock import mainthread
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivy.lang import Builder
from kivy.config import Config
from kivy.event import EventDispatcher
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
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
    amount_double = ObjectProperty(None)

    long_btn = ObjectProperty(None)
    short_btn = ObjectProperty(None)

    safety_helper_icon = ObjectProperty(None)

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

class EventLoopWorker(EventDispatcher):
    __events__ = ('on_pulse',)

    def __init__(self):
        super().__init__()
        self._thread = threading.Thread(target=self._run_loop)
        self._thread.daemon = True
        self.loop = None
        # the following are for the pulse() coroutine, see below
        self._default_pulse = [None]
        self._pulse = None
        self._pulse_task = None

    def _run_loop(self):
        self.loop = asyncio.get_event_loop_policy().new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._restart_pulse()

        self.loop.run_forever()

    def start(self):
        self._thread.start()

    def stop(self):
        self.loop.stop()

    #START: In Progress
    async def fetch_position(self) -> dict:
        positions, account, funding, symbol = await asyncio.gather(
            exchange.fapiPrivate_get_positionrisk(params={'symbol': 'ETHUSDT'}),
            exchange.fapiPrivate_get_account(),
            exchange.fapiPublic_get_fundingrate(),
            exchange.fapiPublic_get_ticker_price(params={'symbol': 'ETHUSDT'})
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
                        'leverage': 10.0}
        for e in funding:
            if e['symbol'] == 'ETHUSDT':
                position['funding_time'] = float(e['fundingTime'])
                position['predicted_funding_rate'] = float(e['fundingRate'])
                break
        for e in account['assets']:
            if e['asset'] == 'USDT':
                position['margin_cost'] = f"{float(e['positionInitialMargin']):.2f}"
                position['margin_ratio'] = (float(e['maintMargin']) / float(e['marginBalance']))*100
                position['equity'] = float(e['marginBalance'])
                position['wallet_balance'] = f"{float(e['walletBalance']):.2f} USDT"
                position['available_balance'] = float(e['availableBalance'])
                position['pos_pnl_pct'] = ((float(e['positionInitialMargin'])+float(position['pos_pnl']) - float(e['positionInitialMargin'])) / float(e['positionInitialMargin'])) * 100.0
                break

        # for key in position:
        #     print(f"{key}: {position[key]}")
        position['asset_price'] = symbol['price']
        position['safety_buffer_pct'] = float(position['margin_ratio']) * (float(position['leverage']) * 1.5)*-1

        return position

    async def pulse(self):

        for msg in self._pulse_messages():
            @mainthread
            def dispatch_position(position):
                self.dispatch('on_pulse', position)

            position = await self.fetch_position()
            dispatch_position(position)

            await asyncio.sleep(0.5) #TODO: Make the polling frequency configurable

    def _restart_pulse(self):
        """Helper to start/reset the pulse task when the pulse changes."""
        if self._pulse_task is not None:
            self._pulse_task.cancel()
        self._pulse_task = self.loop.create_task(self.pulse())

    def on_pulse(self, *_):
        pass

    def _pulse_messages(self):
        """A generator providing an inexhaustible supply of pulse messages."""
        while True:
            if isinstance(self._pulse, str) and self._pulse != '':
                pulse = self._pulse.split()
                yield from pulse
            else:
                yield from self._default_pulse

    #END: In Progress

class PromptCreds(BoxLayout):
    prompt_creds_key = ObjectProperty(None)
    prompt_creds_secret = ObjectProperty(None)

class CoreDrill(MDApp):

    #dialog box object to input API credentials
    prompt_creds = None

    def init_ccxt(self):
        #TODO: global variable lol? i can probably think of a better way to persist this object between classes
        global exchange
        exchange = getattr(ccxt_async, 'binance')({'apiKey': self.creds['key'],
                                            'secret': self.creds['secret'],
                                            'options': {'defaultType': 'future'}})
        global last_price
        last_price = None

    def clear_position_labels(self):
        self.root.ids.pos_size.text = ""
        self.root.ids.entry_price.text = ""
        self.root.ids.liq_price.text = ""
        self.root.ids.pos_margin.text = ""
        self.root.ids.pos_pnl.text = ""

    def reset_buttons(self):
        self.root.ids.amount_small.state = "normal"
        self.root.ids.amount_medium.state = "normal"
        self.root.ids.amount_large.state = "normal"
        self.root.ids.amount_double.state = "normal"
        self.root.ids.long_btn.state = "normal"
        self.root.ids.short_btn.state = "normal"
        self.root.ids.pending_tx_size.text = "-"
        self.root.ids.pending_tx_margin.text = "-"

        self.pending_tx = {"percent": 0, "size": 0, "margin": 0, "direction": 0}

    def toggle_interface(self, state):
        self.reset_buttons()
        self.root.ids.amount_small.disabled = not state
        self.root.ids.amount_medium.disabled = not state
        self.root.ids.amount_large.disabled = not state
        self.root.ids.amount_double.disabled = True
        self.root.ids.long_btn.disabled = not state
        self.root.ids.short_btn.disabled = not state
        self.root.ids.clear_btn.disabled = not state
        self.root.ids.execute_btn.disabled = True #only enabled when complete pending tx is ready

    def toggle_safety_icon(self, enabled, in_profit = None):
        if enabled:
            alert_reason = ""
            color = None
            if in_profit:
                alert_reason = "Position in profit"
                color = get_color_from_hex('#0ecb81')
            else:
                alert_reason = "Entry price too close"
                color = get_color_from_hex('#f0b600')

            tooltip_text = f"{alert_reason}, position increase disabled"
            self.root.ids.safety_helper_icon.tooltip_text = tooltip_text
            self.root.ids.safety_helper_icon.tooltip_text_color = color
            self.root.ids.safety_helper_icon.text_color = color
        else:
            self.root.ids.safety_helper_icon.tooltip_text = ""
            self.root.ids.safety_helper_icon.text_color = (0,0,0,0)

    def calculate_pending_tx(self):
        self.pending_tx['margin'] = float(self.position['available_balance']) * self.pending_tx['percent']
        self.pending_tx['size'] = round(self.pending_tx['margin'] / float(self.position['asset_price']) * self.pending_tx['direction'] * 10.0, 3) #TODO: 10x leverage, change this to be pulled from config in the future
        self.root.ids.pending_tx_size.text = f"{self.pending_tx['size']:.3f} ETH"
        self.root.ids.pending_tx_margin.text = f"{self.pending_tx['margin']:.2f} USDT"

    def change_tx_amount_pct(self, instance, percent):
        if self.position is not None:
            self.pending_tx['percent'] = percent
            if self.pending_tx['percent'] > 0 and self.pending_tx['direction'] != 0:
                self.calculate_pending_tx()
        else:
            setattr(instance, 'state', 'normal')

    #TODO: Refactor, there's 90% duplication with calculate_pending_tx() and change_tx_amount_pct()
    def change_tx_amount_double(self, instance):
        if self.position is not None:
            self.pending_tx['margin'] = float(self.position['pos_margin'])
            self.pending_tx['size'] = round(self.pending_tx['margin'] / float(self.position['asset_price']) * self.pending_tx['direction'] * 10.0, 3) #TODO: 10x leverage, change this to be pulled from config in the future

            self.root.ids.pending_tx_size.text = f"{self.pending_tx['size']:.3f} ETH"
            self.root.ids.pending_tx_margin.text = f"{self.pending_tx['margin']:.2f} USDT"
        else:
            setattr(instance, 'state', 'normal')

    def change_tx_direction(self, instance, multiplier):
        if self.position is not None:
            self.pending_tx['direction'] = multiplier
            if self.pending_tx['percent'] > 0 and self.pending_tx['direction'] != 0:
                self.calculate_pending_tx()
        else:
            setattr(instance, 'state', 'normal')

    def load_credentials(self):
        with open(f'{config_path}/core.drill', 'rb') as file:
            self.creds = pickle.load(file)
            print("Core Drill found.\nInitializing...")

    def save_credentials(self, instance):
        new_key = self.prompt_creds_layout.ids.prompt_creds_key
        new_secret = self.prompt_creds_layout.ids.prompt_creds_secret

        #TODO: Fix the strange UI bug where the error color
        # only appears when refocusing the input field
        if len(new_key.text) != 64:
            new_key.error = True
        else:
            new_key.error = False
        if len(new_secret.text) != 64:
            new_secret.error = True
        else:
            new_secret.error = False
        if new_key.error or new_secret.error:
            return

        key_data = {
        "key": new_key.text,
        "secret": new_secret.text
        }
        with open(f'{config_path}/core.drill', 'wb') as file:
            pickle.dump(key_data, file, protocol=pickle.HIGHEST_PROTOCOL)

        self.load_credentials()
        self.prompt_creds.dismiss()

    def clear_pressed(self):
        self.reset_buttons()

    def execute_pressed(self):
        #TODO: Execute order here
        self.reset_buttons()

    def dismiss_close_prompt(self, instance):
        self.prompt_close.dismiss()

    def close_position(self, instance):
        self.dismiss_close_prompt(instance)
        symbol = 'ETH/USDT'
        type = 'market'
        side = 'sell' if self.position['size'] > 0 else 'buy'
        amount = self.position['size']
        price = None
        params = {'reduceOnly': 'true'}

        try:
            # closing_order = exchange.create_order(symbol, type, side, amount, price, params)
            # print(closing_order)
            print('confirm close pos')
        except Exception as e:
            print(type(e).__name__, str(e))

    def prompt_close_position(self):
        self.prompt_close = MDDialog(
            title="Close position?",
            text="This will close your current position at the market price.",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=get_color_from_hex('#ffffff'),
                    on_release=self.dismiss_close_prompt
                ),
                MDRaisedButton(
                    text="CLOSE",
                    font_size=16,
                    theme_text_color="Custom",
                    text_color=get_color_from_hex('#ffffff'),
                    md_bg_color=get_color_from_hex('#0ecb81') if self.position['pos_pnl_pct'] > (self.position['leverage']/5) else get_color_from_hex('#f6465d'),
                    on_release=self.close_position
                ),
            ],
        )
        self.prompt_close.open()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_loop_worker = None
        self.position = None
        # self.safety_anim = None
        self.pending_tx = {"percent": 0, "size": 0, "margin": 0, "direction": 0}

    def build(self):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        Window.size = (1024, 600)
        self.theme_cls.theme_style = "Dark"
        self.title = "Core Drill Trader"
        self.icon = "logo.png"

        return DashboardLayout()

    def on_start(self, **kwargs):
        if not os.path.exists(config_path):
            os.makedirs(config_path)
            print("Created configuration folder.")
        if not os.path.isfile(f"{config_path}/core.drill"):
            print("No Core Drill found, please insert key.")
            if not self.prompt_creds:
                self.prompt_creds_layout = PromptCreds()
                self.prompt_creds = MDDialog(
                    title = "[color=999999]Configure your Core Drill API key and secret:[/color]",
                    type = "custom",
                    md_bg_color = get_color_from_hex('#1E2026'),
                    auto_dismiss = False,
                    content_cls = self.prompt_creds_layout,
                    buttons = [
                        MDFlatButton(
                            text = "SAVE",
                            font_size = 16,
                            theme_text_color = "Custom",
                            text_color = get_color_from_hex('#ffffff'),
                            on_release = self.save_credentials,
                        ),
                    ],
                )

            self.prompt_creds.open()
        else:
            self.load_credentials()

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
            self.position = position
            if exchange is None:
                print('No exchange connected.')
                return
            if position is None:
                print('No position info detected.')
                return
            if position["size"] != 0:
                if position["size"] > 0:
                    self.root.ids.short_btn.disabled = True
                elif position["size"] < 0:
                    self.root.ids.long_btn.disabled = True

                #TODO: make this safety mode check configurable
                if position["pos_pnl_pct"] > position["safety_buffer_pct"]:
                    self.toggle_interface(False)
                    self.root.ids.amount_double.disabled = True
                    # if self.safety_anim is None:
                    #     self.safety_anim = Animation(font_size = 36, duration = 0.4) + Animation(font_size = 32, duration = 0.1)
                    #     self.safety_anim.repeat = True
                    #     self.safety_anim.start(self.root.ids.safety_helper_icon)

                    self.toggle_safety_icon(True, position["pos_pnl_pct"] > 0)
                else:
                    self.toggle_interface(True)
                    self.toggle_safety_icon(False)
                    self.root.ids.amount_double.disabled = False
                    # self.safety_anim.stop(self.root.ids.safety_helper_icon)
                    # self.safety_anim = None

                self.root.ids.close_pos_btn.disabled = False
                for key in pulse_listener_labels:
                    #TODO: think of a better way to check expected text color
                    colored_text = ["size", "pos_pnl"]
                    if key in colored_text:
                        if position[key] > 0:
                            pulse_listener_labels[key].color = get_color_from_hex('#0ecb81')
                        elif position[key] < 0:
                            pulse_listener_labels[key].color = get_color_from_hex('#f6465d')
                        else:
                            pulse_listener_labels[key].color = get_color_from_hex('#ffffff')

                    #TODO: do something better than checking these string literals
                    if key == "size":
                        pulse_listener_labels[key].text = f"{position[key]:.3f} ETH"
                    elif key == "pos_pnl":
                        pulse_listener_labels[key].text = f"{position[key]:.2f}({position['pos_pnl_pct']:.2f}%)"
                    elif key == "margin_ratio":
                        pulse_listener_labels[key].text = f"{position[key]:.2f}%"
                    elif key == "available_balance":
                        pulse_listener_labels[key].text = f"{float(position[key]):.2f} USDT"
                    elif key == "asset_price":
                        global last_price
                        pulse_listener_labels[key].text = f"{float(position[key]):.2f}"
                        if last_price is not None:
                            if float(last_price) > float(position[key]):
                                pulse_listener_labels[key].color = get_color_from_hex('#f6465d')
                            elif float(last_price) < float(position[key]):
                                pulse_listener_labels[key].color = get_color_from_hex('#0ecb81')
                            else:
                                pulse_listener_labels[key].color = get_color_from_hex('#ffffff')
                        last_price = position[key]
                    else:
                        pulse_listener_labels[key].text = str(position[key])
            else:
                self.clear_position_labels()
                self.root.ids.short_btn.disabled = False
                self.root.ids.long_btn.disabled = False
                self.root.ids.close_pos_btn.disabled = True
                self.root.ids.amount_double.disabled = True

            if self.pending_tx['size'] != 0:
                self.root.ids.execute_btn.disabled = False
            else:
                self.root.ids.execute_btn.disabled = True

            if position['available_balance'] >= self.pending_tx['margin']:
                self.root.ids.pending_tx_margin.color = get_color_from_hex('#ffffff')
            else:
                self.root.ids.pending_tx_margin.color = get_color_from_hex('#f6465d')
                # self.root.ids.execute_btn.disabled = True

        worker.bind(on_pulse=display_on_pulse)
        worker.start()

    def connect_exchange(self, instance):
        #TODO: proper credential check and connection logic
        has_credentials = True

        if not has_credentials:
            instance.active = False
            print(f"Initialise credentials here: {instance.active}")
        elif has_credentials and instance.active:
            self.root.ids.connection_status.text = "Connecting..."
            try:
                self.init_ccxt()
                self.toggle_interface(instance.active)
                self.root.ids.connection_status.text = "Connected"
                self.start_event_loop_thread()
            except Exception as e:
                print('Error connecting to exchange', e)

        else:
            exchange = None
            self.event_loop_worker.stop()
            self.event_loop_worker = None
            self.root.ids.connection_status.text = "Connect"
            self.root.ids.balance_full.text = "-"
            self.root.ids.balance_available.text = "-"
            self.root.ids.asset_price.text = "-"
            self.root.ids.asset_price.color = get_color_from_hex('#ffffff')
            self.root.ids.margin_ratio.text = "-"
            self.clear_position_labels()
            self.root.ids.close_pos_btn.disabled = True
            self.toggle_interface(instance.active)
            self.toggle_safety_icon(False)

if __name__ == '__main__':
    Builder.load_file(layout_path)
    CoreDrill().run()
