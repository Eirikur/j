#!/usr/bin/python3
"""July 2021 An incarnation of the Jeeves idea. Intended to be extensible.
Runs as a service, running its services as threads or subprocesses.
This file is the command-line client.
"""
Needs: means to screen out our own messages.


from sys import argv as arguments  # "I came here for an argument!"
import time
import threading
import queue
from typing import Callable
# Mine
from networking.udp import udp_broadcast as send
from networking.udp import udp_receive as receive

hour = 60 * 60

def loop(msg: str) -> None:
    while True:
        send(msg)
        receive(timeout=1)

def listener(q):
    while True:
        print('listener: about to block.')
        response = receive() # No timeout passed. This will block
        # print(f"listener: {response}")
        if response == "1":
            exit(0)
        elif response == "0":
            print("The server had a problem.")
            exit(1)
        elif response == None:
            print("Server sent a bad response: None")
            exit(1)
        elif isinstance(response, str):
            print(response)
            exit(0)

def background(job_func: Callable, *args, **kwargs):
    thread = None
    try:
        thread = threading.Thread(target=job_func, daemon=True, *args, **kwargs)
        thread.start()
    except Exception as e:
        print(e)
    return thread
    

def main(arguments) -> None:
    q = queue.Queue()
    background(listener, args=(q,)) # Want listener to start listening before we send anything.
    arguments.pop(0) # Strip off the command name.
    if len(arguments): # Syntax: lens g target
        command = arguments[0].lower()
    else:
        command = 'list'
        arguments = ['list']
    reload_flag = True if command == "reload" else False

    msg = " ".join([arg for arg in arguments[:]])
    if "LOOP" in arguments:
        loop(msg)
    else:
        tmp = send(msg)
    # print('Blocking on q.get()')
    # response = q.get()
    # print(f"Response: {response}")
        
    if reload_flag:
        background(listener, args=(q,))
        print('command was reload')
        time.sleep(5)
        send("status", timeout=5)
        # time.sleep(2)
        # print(receive(timeout=5))
    else:
        exit(0)


main(arguments)
