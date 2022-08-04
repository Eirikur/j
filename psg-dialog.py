#!/usr/bin/python3
import time
import PySimpleGUI as sg
from PySimpleGUI import POPUP_BUTTONS_NO_BUTTONS as absent
alert_persistance = 60*60*8 # 8 Hours
# My polity network system.
from polity import Polity


def popup(msg: str)->None:
    layout = [[sg.Text(msg, font='Hack 72')]]
    win = sg.Window(f"Alert at {time.ctime()}", layout,
                    # button_type = absent,
                    auto_close = True,
                    auto_close_duration = alert_persistance,
                    return_keyboard_events=True)
    time.sleep(1) # Stay visible for at least this long, even if a keystroke happens
    win.read()
    win.close()

def receiver_loop()->None:
    P = Polity()
    while True:
        print('receiver_loop...')
        try:
            msg = P.get() # Blocking from Polity's output queue.
            if msg.body:
                print(msg.body)
        except Exception as e:
            error(f"Receive error. {e}")
            exit()
        else:
            if len(msg):
                handle_request(msg) # Same line of text from the original system.
            else:
                print('Empty message!')

def handle_request(msg)->None:
    print(msg)
    print(msg.body)
    popup(msg.body)

def main()->None:
    receiver_loop() # Never exits. Shutdown isn't handled anywhere yet.

main()
