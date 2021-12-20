import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.core.window import Window

Builder.load_file('layouts/default.kv')

class DashboardLayout(Widget):

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

    def execute_pressed(self):
        print('Execute pressed')

    def close_position(self):
        print('Close position pressed')


class CoreDrill(App):
    def build(self):
        Window.size = (1024, 600)
        return DashboardLayout()


if __name__ == '__main__':
    CoreDrill().run()
