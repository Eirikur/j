#!/usr/bin/python3
import time
import sys
from sys import argv as arguments # "I came here for an argument!"
from os import system as shell_cmd
import PySimpleGUI as sg
from PySimpleGUI import POPUP_BUTTONS_NO_BUTTONS as absent
alert_persistance = 60*60*8 # 8 Hours

browser = '~/Applications/firefox/firefox'
search_engine = 'https://www.google.com'
#search_route = '/search?client=firefox-b-1-d&q='
search_route = '/search?q='
to_dev_null = '&> /dev/null'
execution_mode = '& disown'
execution_mode = ''


# def popup(msg:str)->None:


#     sg.Popup(msg,
#              title=f"Alert at {time.ctime()}",
#              font='Hack 72',
#              # button_type = absent,
#              auto_close = True,
#              auto_close_duration = alert_persistance)

win = None
def popup(msg:str)->None:
    layout = [[sg.Text(msg, font='Hack 72')]]
    win = sg.Window(f"Alert at {time.ctime()}", layout,
                    # button_type = absent,
                    auto_close = True,
                    auto_close_duration = alert_persistance,
                    return_keyboard_events=True)
    time.sleep(1) # Stay visible for at least this long, even if a keystroke happens
    win.read()
    win.close()

def main(arguments)->bool:
    args = ' '.join(arguments[1:])
    # print(args)
    # popup(args)

    classy_text = sg.Text('Query:', font='Hack 20',
                          background_color='black',
                          text_color='white',
                          size=(6, 1))


    classy_input = sg.InputText(enable_events=True,
                          background_color='black',
                          text_color='white',
                          font='Hack 20')

    layout = [  #  [sg.Text('Input for Lens', font='Hack 20')],
                [classy_text, classy_input],
                # [sg.Input(key='-IN-', enable_events=True)],
                [sg.Button('Go', visible=False, bind_return_key=True)]  ]

    window = sg.Window('Lens Window', layout, no_titlebar=True,
                       size=(3140, 2160), location=(0, 0),
                       alpha_channel=.7, grab_anywhere=True,
                       finalize=True)
    window.BackgroundColor='black'
    classy_input.SetFocus()
    window.Maximize()

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Go'):
            print('vals:', values)
            window.close()
            go(values)

def go(arguments)->bool:
    arguments = arguments.pop(0)
    # joined = "'+'".join(arguments.split())
    # query = f"'{joined}'" # after joining, wrap in '
    # print(query)
    # search = f'"{search_engine}{search_route}{query}"'
    # cmd = ' '.join([browser,
    #                 search,
    #                 to_dev_null,
    #             execution_mode])
    verb = 'xdotool type'
    cmd = f"{verb} '{arguments}'"
    shell_cmd(cmd)
    print(cmd)
    cmd = 'xdotool key ctrl+m'
    shell_cmd(cmd)
    sys.exit(0)


main(arguments)
