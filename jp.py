#!/usr/bin/python3
"""July 2021 An incarnation of the Jeeves idea. Intended to be extensible.
Runs as a service, running its services as threads or subprocesses.
Listens via nng."""

# use the atexit module to shut down things like profiling before exit()

# Fix: manage to use bidirectional sockets. 17 Nov. 2021`

# Add:
#    Get modified/created date.
#    Async check in sched loop? and reload.

#    New daemon watches files and moves them.

# import sys
import os
import time
import logging
import traceback
# import socket
# import ipaddress
# from typing import Callable, Iterable

# import cProfile, pstats, io
# from pstats import SortKey
# pr = cProfile.Profile()
# pr.active = False # My own attribute.

# Third Party
# import extended_exec_formatter

# part of this program
import jt
from polity import Polity
from message import Message, Body

version_of = 'Tue Oct 11 21:53:51 2022'

log_file_name = '/home/eh/Projects/j/j.log'
history_file = '/home/eh/Projects/j/history.log'

newline = '\n'
space = ' '

def set_up_logging():
    "docstring"
    # w%(filename)s Filename portion of pathname.
    # %(module)s Module (name portion of filename).
    # %(funcName)s Name of function containing the logging call.
    # %(lineno)d Source line number where the logging call was issued (if available).
    # Hack to make these aliases available despite
    # setting up logging in a function scope.
    global log, debug, info, error
    log = logging.getLogger('J')
    log.setLevel(logging.INFO);
    debug = log.debug
    info = log.info
    error = log.error

    # if dbg:
    #     formatter = extended_exec_formatter.ExtendedExceptionFormatter('%(asctime)s %(levelname)s - %(message)s')
    #     extended_exec_formatter.install_exec_handler()
    #     print('Extended logging is active.')
    # else:
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(funcName)s %(lineno)d - %(message)s')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter)
    log.addHandler(console)

    file = logging.FileHandler(log_file_name)
    file.setLevel(logging.INFO)
    file.setFormatter(formatter)
    log.addHandler(file)
    return log

log = set_up_logging()

def receiver_loop()->None:
    global P
    print('receiver_loop...')
    while True:
        msg = ''
        print('Message wait...')
        try:
            msg = P.get() # Blocking from Polity's output queue.
            print(f"receiver_loop received command: {msg.body}")
        except Exception as e:
            error(f"Receive error. {e}")
            exit()
        finally:
            if len(msg):
                try:
                    handle_request(msg) # Same line of text from the original system.
                except Exception as e:
                    print(e)
                finally:
                    reload()
                    continue
            else:
                print('Empty message!')
    print('Fell of the end! ##################################')

def reply(input_msg, text, status)->None: #FIXME
    if isinstance(text, list):
         text = newline.join(text)
    # if len(text) > 256:
    #     print('Ooops. Very long text is too long for reply...BUG!!!')
    #     text = 'Ooops. Very long text is too long for reply...BUG!!!'
    # # reply = f"Reply error: |{text}| {type(text)}"
    print('Will reply with:')
    print(text)


    P.reply(input_msg, text, status)
    # except Exception as e:
        # print(type(text), text)
        # print(f"Send error. {e}")

def reload():
    """Reload updated source file..."""
    # TODO Needs to shut down any threads or processes.
    jt.shutdown() # Shut down the scheduling system and any persistant things.
    print(f"Reloading from {__file__}.")
    os.execv(__file__,['nothing here'])  # Run a new iteration of the current script, providing any command line args from the current iteration.

def shutdown():
    reply("Will exit.")
    jt.shutdown()
    exit()

def profile():
    if pr.active:
        pr.disable()
        pr.active = False
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        ps.dump_stats('j-profile.dump')
        text = s.getvalue()
        print(text)
        with open('j-profile.txt', 'w') as f:
            f.write(text)
        msg = 'Profiling deactivated and profile dumped'
        print(msg)
        return(msg)
    else:
        pr.enable()
        return('Profiling enabled.')


def handle_request(input_msg):
    print(input_msg.body)

    cmd_string = str(input_msg.body) # Force a copy.
    cmd, modifier, remainder = jt.get_cmd(cmd_string)
    if cmd == 'reload':
        msg = 'Will reload.'
        reply(input_msg, msg, True)
        print(msg)
        reload()
    elif cmd == 'profile':
        return profile()
    elif cmd == 'debug':
        set_up_logging()
        msg = 'Debug mode activated. This only effects logging today.'
        print(msg)
        return(msg)
    elif cmd in ['exit', 'bye', 'shutdown']:
        jt.shutdown()
        msg = 'Shutting down.'
        reply(input_msg, msg, True)

        print(msg)
        exit()

    # Okay, let's try to do as asked...
    start = time.time()
    try:
        response=jt.command(cmd_string)
    except Exception as e:
        traceback.print_exc(file=open('j.traceback', 'w'))
        traceback.print_exc()
        tb = traceback.format_exc()
        response = tb # In the exception path, response was undefined.
        reply(input_msg, tb, False)
        input_msg.body = cmd_string

    elapsed = 1000 * (time.time() - start)
    cmd = input_msg['body']
    perf_msg = f"Performed '{cmd}' in {round(elapsed, 4)} milliseconds."
    print(perf_msg)
    with open(history_file, 'a') as f:
        f.write(newline.join([time.ctime(), input_msg.body, response, newline]))
    reply(input_msg, response, True) # Status always true for now.

def main()->None:
    jt.setup() # Initialization of scheduling module.
    receiver_loop()

if __name__ == '__main__':
    set_up_logging()
    global P
    P = Polity()
    main()
