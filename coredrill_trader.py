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
            position = {'size': float(positions[0]['positionAmt']),
                        'price': float(positions[0]['entryPrice']),
                        'liquidation_price': float(positions[0]['liquidationPrice']),
                        'leverage': float(positions[0]['leverage'])}
        else:
            position = {'size': 0.0,
                        'price': 0.0,
                        'liquidation_price': 0.0,
                        'leverage': 1.0}
        for e in funding:
            if e['symbol'] == 'ETHUSDT':
                position['funding_time'] = float(e['fundingTime'])
                position['predicted_funding_rate'] = float(e['fundingRate'])
                break
        for e in account['assets']:
            if e['asset'] == 'USDT':
                position['margin_cost'] = float(e['positionInitialMargin'])
                position['equity'] = float(e['marginBalance'])
                position['wallet_balance'] = float(e['walletBalance'])
                position['available_balance'] = float(e['availableBalance'])
                break
        print('Final position: ') #test
        print(position)

    def init_ccxt(self):
        self.exchange = getattr(ccxt_async, 'binance')({'apiKey': key,
                                            'secret': secret,
                                            'options': {'defaultType': 'future'}})
        asyncio.run(self.fetch_position())

    def build(self):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        Window.size = (1024, 600)

        if not os.path.exists(config_path):
            os.makedirs(config_path)
            print("Created configuration folder.")

        self.init_ccxt()

        return DashboardLayout()


if __name__ == '__main__':
    Builder.load_file(layout_path)
    CoreDrill().run()
