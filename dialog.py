#!/usr/bin/python3
import time
from sys import argv as arguments # "I came here for an argument!"
import PySimpleGUI as sg
from PySimpleGUI import POPUP_BUTTONS_NO_BUTTONS as absent

from polity import Polity



alert_persistance = 60*60*8 # 8 Hours


win = None
def popup(msg:str)->None:
    layout = [[sg.Text(msg, font='Hack 72')]]
    global win
    win = sg.Window(f"Alert at {time.ctime()}", layout,
                    # button_type = absent,
                    auto_close = True,
                    auto_close_duration = alert_persistance,
                    return_keyboard_events=True)
    time.sleep(1) # Stay visible for at least this long, even if a keystroke happens
    event, values = win.read()
    win.close()
    return event, values


def main(arguments )->None:
    p = Polity()
    print('starting receiver_loop...')
    while True:
        msg = ''
        print('Message wait...')
        try:
            msg = p.get() # Blocking from Polity's output queue.
            print(f"receiver_loop received command: {msg.body}")
        except Exception as e:
            print(f"Receive error. {e}")
            exit()
        try:
            print(f"popup: {msg.body}")
            event, values = popup(msg.body)
        except Exception as e:
            print(f"Popup error. {e}")
            exit()
        print("from popup: {event} {values}")

main(arguments)
