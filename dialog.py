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
    win.read()
    win.close()

def main(arguments )->None:
    arguments = arguments[1:]
    message = ' '.join(arguments)
    popup(message)

main(arguments)
