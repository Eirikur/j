#!/usr/bin/python3
"""July 2021 An incarnation of the Jeeves idea. Intended to be extensible.
Runs as a service, running its services as threads or subprocesses.
This file is the command-line client.
"""

from sys import argv as arguments  # "I came here for an argument!"
from contextlib import suppress
from queue import Empty
import time
# Mine
from polity import Polity

timeout = 2
hour = 60 * 60
space = ' '

def listener(p):
    response = None
    try:
        response = p.get(timeout=timeout)
    except Empty as e:
        print(f"Timed out at {timeout} seconds")
    if response != None:
        servers_message = response.body
        print(servers_message)
        exit(0)


def main(arguments) -> None:
    p = Polity()
    arguments = arguments[1:]
    if len(arguments): # Syntax: lens g target
        command = arguments[0].lower()
    else:
        command = 'list'
        arguments = ['list']
    reload_flag = True if command == "reload" else False
    cmd_line = space.join([arg for arg in arguments[:]])
    # print(f"Sending: {cmd_line}")
    p.send_cmd(cmd_line) # Message type defaults to CMD
    listener(p)


    if reload_flag:
        time.sleep(5)
        p.send_text("status")
        listener(p)
    else:
        exit(0)


main(arguments)
