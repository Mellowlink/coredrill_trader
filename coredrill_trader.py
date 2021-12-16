import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton

class MyGridLayout(GridLayout):
    def __init__(self, **kwargs):
        super(MyGridLayout, self).__init__(**kwargs)

        # Set columns
        self.cols = 1
        # Add second gridlayout
        self.tx_percent_btns = GridLayout()
        self.tx_percent_btns.cols = 3
        self.tx_direction_btns = GridLayout()
        self.tx_direction_btns.cols = 2
        # self.tx_double_btn = GridLayout()
        # self.tx_double_btn.cols = 3
        self.tx_execute_btn = GridLayout()
        self.tx_execute_btn.cols = 1
        self.tx_current_pos = GridLayout()
        self.tx_current_pos.cols = 6

        self.add_widget(self.tx_percent_btns)
        self.add_widget(self.tx_direction_btns)
        # self.add_widget(self.tx_double_btn)
        self.add_widget(self.tx_execute_btn)
        self.add_widget(self.tx_current_pos)

        # Add tx amount buttons
        self.amount_small = ToggleButton(text="5%", group="tx_amount", font_size=16)
        self.amount_medium = ToggleButton(text="10%", group="tx_amount", font_size=16)
        self.amount_large = ToggleButton(text="15%", group="tx_amount", font_size=16)
        self.amount_small.bind(on_press=self.change_tx_amount)
        self.amount_medium.bind(on_press=self.change_tx_amount)
        self.amount_large.bind(on_press=self.change_tx_amount)
        self.tx_percent_btns.add_widget(self.amount_small)
        self.tx_percent_btns.add_widget(self.amount_medium)
        self.tx_percent_btns.add_widget(self.amount_large)

        # Add Buy & Sell buttons
        self.long_btn = ToggleButton(text="Buy/Long", group="tx_direction", font_size=16)
        self.short_btn = ToggleButton(text="Sell/Short", group="tx_direction", font_size=16)
        self.long_btn.bind(on_press=self.change_tx_direction)
        self.short_btn.bind(on_press=self.change_tx_direction)
        self.tx_direction_btns.add_widget(self.long_btn)
        self.tx_direction_btns.add_widget(self.short_btn)

        # Add Double button
        # self.tx_current_pos.add_widget(Label(text='', font_size=16))
        # self.double_btn = ToggleButton(text="Double", group="tx_amount", font_size=16)
        # self.double_btn.bind(on_press=self.change_tx_amount)
        # self.double_btn.add_widget(self.double_btn)
        # self.double_btn.add_widget(Label(text='', font_size=16))

        # Add Execute button
        self.execute_btn = Button(text="Execute", font_size=16)
        self.execute_btn.bind(on_release=self.execute_pressed)
        self.tx_execute_btn.add_widget(self.execute_btn)

        # Add current position info
        self.tx_current_pos.add_widget(Label(text='Size', font_size=14))
        self.tx_current_pos.add_widget(Label(text='Entry Price', font_size=14))
        self.tx_current_pos.add_widget(Label(text='Liq. Price', font_size=14))
        self.tx_current_pos.add_widget(Label(text='Margin', font_size=14))
        self.tx_current_pos.add_widget(Label(text='PNL(ROE %)', font_size=14))
        self.tx_current_pos.add_widget(Label(text='', font_size=14))

        self.pos_size = Label(text='0.138 TEST', font_size=14)
        self.entry_price = Label(text='4,037.54', font_size=14)
        self.liq_price = Label(text='4,897.83', font_size=14)
        self.pos_margin = Label(text='56.01', font_size=14)
        self.pos_pnl = Label(text='-1.96(-2.98%)', font_size=14)

        self.tx_current_pos.add_widget(self.pos_size)
        self.tx_current_pos.add_widget(self.entry_price)
        self.tx_current_pos.add_widget(self.liq_price)
        self.tx_current_pos.add_widget(self.pos_margin)
        self.tx_current_pos.add_widget(self.pos_pnl)

        self.close_pos_btn = Button(text="Close", font_size=14)
        self.close_pos_btn.bind(on_release=self.close_position)
        self.tx_current_pos.add_widget(self.close_pos_btn)

    def change_tx_amount(self, instance):
        print(instance.text)

    def change_tx_direction(self, instance):
        print(instance.text)

    def execute_pressed(self, instance):
        print('Execute pressed')

    def close_position(self, instance):
        print('Close position pressed')


class CoreDrill(App):
    def build(self):
        return MyGridLayout()


if __name__ == '__main__':
    CoreDrill().run()
