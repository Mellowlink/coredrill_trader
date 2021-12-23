import os
import kivy
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.core.window import Window

config_path = './config'

Builder.load_file('layouts/default.kv')

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

    def connect_exchange(self, instance):
        #TODO: proper credential check and connection logic
        has_credentials = False

        if not has_credentials:
            instance.active = False
            print(f'Initialise credentials here: {instance.active}')
        elif has_credentials and instance.active:
            print(f'OK to connect: {instance.active}')
        else:
            print(f'Connection off: {instance.active}')



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
    def build(self):
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        Window.size = (1024, 600)

        if not os.path.exists(config_path):
            os.makedirs(config_path)
            print("Created configuration folder.")

        return DashboardLayout()


if __name__ == '__main__':
    CoreDrill().run()
