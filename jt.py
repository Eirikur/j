#!/usr/bin/python3
"""
Concept of listing only sched. items that are later than now.
Don't list items that are in the past.
Hmmmm.
Obsolete: We should reload the kv store at midnight if we stay up through midnight.
          We can schedule a reload of the kv store!!!!!
"""
# Python
import sys
import os
# Standard library
import time
import datetime
from datetime import timedelta
import calendar

from typing import Callable
import traceback
from itertools import chain
import logging
from subprocess import Popen
from subprocess import DEVNULL

# Third party
import parsedatetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from pytz import timezone
# import pdbr # debugger

log = logging.getLogger('J.jt')
debug = log.debug
info = log.info
error = log.error

# Calendar words
long_days = calendar.weekheader(9).casefold().split()
abbrev_days = calendar.weekheader(3).casefold().split()
relative_time_words = ['morning', 'night', 'noon', 'today',
                       'tonight', 'tomorrow']
intervals = ['hourly', 'daily', 'weekly', 'monthly', 'yearly']
time_words = list(chain(relative_time_words, abbrev_days, long_days))
parse_date_codes = [None, 'date', 'time', 'datetime']

colon = ':'
nothing = ''
newline = '\n'
space = ' '
alert_sound_file = '/home/eh/Customization/Sounds/Bong.wav'
persistence_filename = 'j-persistence.json'
utility_path = path = os.path.dirname(os.path.abspath(__file__))
X_display = ':0'
alert_dialog = f"{utility_path}/psg-dialog.py"
tracing = None # for trace command
prepositions = ['at', 'on']

commands = ['test', 'status', 'crash', 'now', 'list',
            'ding', 'bong', 'chime']

def command(cmd_str: str)->str:
    # 8 October 2021: This needs to be a better parser, at least a bit.
    # 27 October: Now we have arguments and arguments_string
    # 15 November: Working to integrate APScheduler.
    # try:
        command, modifier, arguments = get_cmd(cmd_str)
        argument_string = ' '.join(arguments)
        full_string = space.join([command, argument_string])
        if command == 'test':
            return test()
        elif command == 'status':
            return status()
        elif command == 'crash':
            return 1/0
        elif command == 'now':
            return 'noop'
        elif command == 'list':
            if jobs := date_jobs(argument_string):
                return formatted_date_jobs(jobs)
            else:
                if argument_string:
                    return f"{argument_string} not found in scheduled jobs."
                else:
                    return "No jobs."

        elif command in ['ding', 'bong', 'chime']:
            audible_alert()
            return('Bong!')
        elif command in ['cancel', 'remove']:
            if len(arguments) >= 2:
                modifier = arguments[0] # 'cancel daily swimming'
                arguments = arguments[2:]
                argument_string = space.join(arguments)
                print('modifier:', modifier)
                if modifier == 'cron' or modifier in intervals:
                    return cancel_cron_jobs(argument_string)
            else: # Cancelling a date-triggered event.
                return cancel_date_jobs(argument_string)
        elif command in ['canceled', 'removed']:
            return 'noop'
        elif command in ['sl', 'buy', 'purschase', 'shopping']:
            if modifier == 'list':
                return 'Shopping list goes here.'
            return 'noop'
        elif command in ['purge', 'expunge']:
            return 'noop'
        elif command in ['min.', 'minutes']:
            return timer(command, arguments)
        elif command in ['sec.', 'seconds']:
            return 'noop'
        elif command in ['undo', 'restore']:
            return 'noop'
        elif command == 'trace':
            global tracing
            tracing = tracefunc if tracing == None else tracefunc
            sys.setprofile(tracing)
            return "Tracing {tracing}."
        elif command == 'shutdown':
            return shutdown()
        elif command == 'reload':
            return "jt.command received reload command!"
        elif command == 'hourly':
            return schedule_hourly(argument_string, no_visual=True)
        elif command == 'cron' or command == 'c':
            return cron_jobs(argument_string)
        elif command in intervals:
            print(f"Command in intervals: {command}")
            return schedule_repeating_item(argument_string)
        elif command in ['sched', 'schedule'] or parse_date_from(full_string)[1]: # There is a schedule item.
            return schedule_item(cmd_str)
        else: # We did not match against a known command.
            msg = f"{command} is not a recognized command and no time field found in command line."
            info(msg)
            return msg
    # except Exception as e:
    #     print('jt commmand: Unhandled: ', e)
    #     exception_type, exception_object, exception_traceback = exc_info()
    #     filename = exception_traceback.tb_frame.f_code.co_filename
    #     line_number = exception_traceback.tb_lineno
    #     stack_dump = traceback.format_stack()
    #     stack_dump = ''.join(stack_dump)
    #     msg = 'jt.command had a problem.'
    #     e = f"Exception type: {exception_type}"
    #     f =f"File name: {filename}"
    #     l = f"Line number: {line_number}"
    #     msg = newline.join([msg,e,f,l,stack_dump])
    #     print(msg)
    #     return msg 0


def timer(item: str)->str:
    "schedule a cron item as a timer."
    pass

def schedule_hourly(item:str, no_visual=False)->str:
    # no_visual is for hourly chimes.
    item = without_time_words(item)
    func = sound if no_visual else alert
    job = scheduler.add_job(sound, 'cron', hour='*', args=[item],
                            replace_existing=True)
    msg = f"Scheduled '{item}', repeating on the hour."
    print(msg)
    return msg

def schedule_daily(item:str)->str:
    target_date, parse_status = parse_date_from(item)
    hour = target_date.hour if parse_status else time_string_in(item)
    if not hour:
        return "No hour specified"
    item = without_time_words(item)
    trigger = 'cron' # Apscheduler trigger method.
    # Find the interval specifier
    interval_words = [word for word in intervals if word in item]
    if len(interval_words) > 1:
        msg = f"{interval_words}: Only one repeat interval can be specified."
        return msg
    else:
        interval = interval_words[0]

    if interval == 'hourly':
        print('hourly')
        job = scheduler.add_job(alert, 'cron', hour='*', args=[item],
                            replace_existing=True)
        msg = f"Scheduled '{item}', repeating on the hour."
        print(msg)
        return msg
    elif interval == 'daily':
        print('daily')
        # schedule call because we need hour=hour
        job = scheduler.add_job(alert, 'cron', hour=hour, args=[item]) #,id=str(int(time.time())), replace_existing=True)
        msg = f"Scheduled '{item}', daily at {hour}"
        print(msg)
        return msg

    elif interval == 'monthly':
        print('monthly')
        #schedule call
    elif interval == 'yearly':
        print('Wow, yearly!')
        #schedule call
    else:
        return f"Sorry, {interval} is not a repeat interval. This should never happen."

    msg = f"Scheduled '{item}' for {target_date.ctime()}"
    print(msg)
    return msg

def cancel_date_jobs(target: str)->str:
    if cancel_list := date_jobs(target): # jobs filtered.
        [job.remove() for job in cancel_list]
        return canceled_text(formatted_date_jobs(cancel_list))
    else:
        return f'There are no scheduled jobs matching "{target}"'

def cancel_cron_jobs(target: str)->str:
    if cancel_list := jobs_filter(cron_jobs_list(), target): # jobs filtered.
        [job.remove() for job in cancel_list]
        return canceled_text(formatted_cron_jobs(cancel_list))
    else:
        return 'There are no scheduled jobs matching "{target}"'


def status()->str:
    """Return some status information to the client.
       This was first needed so that the client
       could use it to test that the server had
       actually restarted."""
    msg = ['Server operational.',
           time.ctime()]
    return newline.join(msg)


# def setup_persistence(filename: str)->dict:
#     return PersistentDict(filename)

def test()->str:
    now = datetime.datetime.now()
    target_date = now + timedelta(minutes=1)
    # breakpoint()
    # when = target_date.ctime()
    when = target_date.strftime("%H:%M")
    msg = "fixed? Scheduled Test Alert!"
    print(f"when: {when}", f"{when} {msg}")
    return command(f"{when} {msg}")


def get_cmd(cmd_str: str)->str:
    # print(f"Command: {cmd_str}")
    words = cmd_str.split()
    modifier = ''
    arguments = words[1:]
    if len(words) == 0:
        return None
    elif len(words) > 1: # If there are two items, we can extract the second one.
        modifier = words[1].casefold()
        arguments = words[2:] # Arguments start at 2 now.
    #command is words[0]
    command = words[0].casefold()
    return command, modifier, arguments

def time_string(word: str)->str:
    # Try to make a 00:00 time string out of word.
    if word is None:
        return ''
    word = ''.join([c for c in word if c in "0123456789"])
    if word.isdigit() and len(word) >= 3:
        minutes = word[-2:] # The right hand two digits
        hours = word[:-2]
        word = f"{int(hours):02}:{int(minutes):02}"
        return word
    else:
        return ''

def is_a_time(word: str)->bool:
    if word := time_string(word):
        return True
    else:
        return False


def date_jobs(target: str)->str:
    return jobs_filter(date_jobs_list(), target)


def cron_jobs(target: str)->str:
    if jobs := jobs_filter(cron_jobs_list(), target):

        return formatted_cron_jobs(jobs)
    else:
        return 'No current cron jobs.'

def date_jobs_list()->list:
    return [job for job in scheduler.get_jobs() if isinstance(job.trigger, DateTrigger)]
def cron_jobs_list()->list:
    if jobs := [job for job in scheduler.get_jobs() if isinstance(job.trigger, CronTrigger)]:
        return jobs
    else:
        return None

def jobs_filter(jobs: list, target:str)->list:
    if jobs and target: # Neither can be empty.
        target = target.casefold()

        return [job for job in jobs if target in job.args[0].casefold()]
    elif jobs: # We have jobs but target is null, return all of them.
        return jobs or f"No jobs matching '{target}'."

def formatted_cron_jobs(jobs: list)->str:
    if not jobs:
        return "No jobs passed into formatted_cron_jobs()."
    strings = []
    for job in jobs:
        # if when := [interval[:-] for interval in intervals if interval in str(job.trigger)]: # Remove 'ly'4
        for interval in intervals:
            # print(interval, str(job.trigger))
            if interval[:-2] in str(job.trigger):
                print(interval, str(job.trigger))
                strings.append(f"Hourly - {space.join(job.args)} - {job.name.capitalize()}")
    return newline.join(strings)

def formatted_date_jobs(jobs: list)->str:
    today = datetime.datetime.now().date()
    return_list = []
    for job in jobs:
        job_type = job.name.capitalize()
        text = job.args[0]
        run_date = job.trigger.run_date
        date_string = run_date.ctime()[:-8] # Remove seconds and year
        list_entry = f"{date_string} - {text} - {job_type}"
        if run_date.date() == today:
            list_entry = today_text(list_entry)
        return_list.append(list_entry)
    return newline.join(return_list)


def schedule_item(item: str)->str:
    """"Parse string and schedule it as a job.
    """
    target_date, parse_status = parse_date_from(item)
    item = without_time_words(item)
    now = datetime.datetime.now()
    past = False
    item = without_time_words(item)
    if target_date <= now:
        past = True
        target_date = now + timedelta(days=1)
        warning = 'Job time was earlier today so it was scheduled for tommorrow.'
    match = [job for job in date_jobs_list() if job.trigger.run_date.date() == target_date.date() and job.args[0] == item]
    if match: # This code needs to be here because the date is adjusted.
        msg = 'That would be a duplicate.'
        print(msg)
        return msg
    job = scheduler.add_job(alert, 'date', run_date=target_date, args=[item],
                            id=str(int(time.time())), replace_existing=True)
    msg = f"Scheduled '{item}' for {target_date.ctime()}"
    if past:
        msg = newline.join([msg, warning])
    print(msg)
    return msg

def time_string_in(text: str)->str:
    # Returns the first time string found in command.
    # Used by the default scheduler command. Having a time means schedule this.
    text = text.split()
    if len(text) < 2:
        return None
    for index, word in enumerate(text):
        if is_a_time(word):
            return time_string(word)
    return ''

def without_time_string(command: str)->str:
    if command:
        cmd = ' '.join([word for word in command.split() if not is_a_time(word)])
        return cmd
    else:
        return command

def without_time_words(text: str)->str:
    if text:
        text = without_time_string(text).split()
        for index, word in enumerate(text):
            word = word.casefold()
            if word in time_words:
                if index > 0:
                    if text[index - 1] in prepositions:
                        del text[index - 1]
        return space.join([word for word in text if word.casefold() not in time_words])

def alert_novisual(msg:str)->None:
    log_msg = f"{msg} {time.ctime()}"
    notify(log_msg)
    debug(log_msg)
    audible_alert()


def alert(msg:str)->None:
    log_msg = f"{msg} {time.ctime()}"
    notify(log_msg)
    debug(log_msg)
    # Use a thread to not have to wait before display of popup.
    sound(msg)
    # Need a thread because in order to close the window, it
    # must be able to respond to the close box. Can't use nowait.
    visual_alert(msg)

def audible_alert()->None:
    # info(f"Bong! at {time.ctime()}")
    sound('Bong!')

def sound(msg: str)->None:
    shell('aplay', alert_sound_file, '2>&1 /dev/null')

def audible_warning_alarm()->None:
    "Play a warning or klaxon sound until popup is dismissed."
    pass # No implementation yet.

def visual_alert(msg:str)->None:
    """
    Use private popup program to display the visible
    Alert. Use & to avoid waiting. """
    shell('notify-send', alert_dialog)
    os.putenv("DISPLAY", ":0")
    shell(alert_dialog, msg)

def notify(msg: str)->bool:
    msg = f"'{msg} at {time.ctime()}'"
    shell('notify-send', msg)
    return True

def shell_cmd(cmd_args: list)->None:
    # December 9 2021: No wait, no return value.
    Popen(cmd_args, stdout=DEVNULL, stderr=DEVNULL)

def shell(*args)->bool:
    args = list(args) # Comes in as a tuple from *args.
    os.putenv("DISPLAY", ":0")
    return shell_cmd(args)

def shutdown():
    "Shut down to leave a clean state."
    # TODO persistent storage, other services.
    scheduler.shutdown()

# Set up our persistent storage.
# kv = setup_persistence(persistence_filename)

def tracefunc(frame, event, arg, indent=[0]):
    if event == "call":
        indent[0] += 2
        print("-" * indent[0] + "> call function", frame.f_code.co_name)
    elif event == "return":
        print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
        indent[0] -= 2
        return tracefunc

def canceled_text(text: str)->str:
    "Wrap the string in ANSI escape sequences to set the rendering."
    # 9 == strikethrough, 2 = dim.
    return f"\033[9;2m{text}\033[0m"

def today_text(text: str)->str:
    "Wrap the string in ANSI escape sequences to set the rendering."
    # 1 means bold.
    return f"\033[1m{text}\033[0m"

def scheduler_setup():
    localtime = timezone('US/Eastern')
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
    }
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 20} #,
        # 'processpool': ProcessPoolExecutor(max_workers=5)
    }
    job_defaults = {
        'coalesce': False,
        'max_instances': 3
    }
    scheduler = BackgroundScheduler()
    scheduler.configure(jobstores=jobstores, executors=executors,
                        job_defaults=job_defaults, timezone=localtime)
    scheduler.start()
    return scheduler

def self_test():
    setup()
    def print_jobs_filtered(search: str):
        print(f'Should print jobs containing: {search}')
        jobs = job_list(search)
        print(formatted_job_list(jobs))

    schedule_item('0300 a simple item in the past')
    # schedule_item('2330 a simple item in the future.')
    command('meet Joe on Wednesday')
    # New today
    command('1400 daily hydrocortisone')
    command('hourly test alert from self-test')
    command('cron')
    command('cron hourly bong')
    command('list')
    command('cancel hourly alert')    # print()
    # print_jobs_filtered('test')
    # print()
    # print_jobs_filtered('simple')
    # print()
    # print('Cancel jobs containing test...')
    # cancel_jobs('test')
    # print()
    # print_jobs_filtered('')
    # command('tomorrow 0700 make early call')
    # canceled_list = command('cancel early')
    # print('Canceled:')
    # print(canceled_list)

def setup()->bool: # Used by j.py, so don't add arguments.
    global parse_date_from
    parse_date_from = parsedatetime.Calendar().parseDT # One time setup.
    print('Starting APScheduler...')
    global scheduler
    scheduler = scheduler_setup()
    return True

if __name__ == '__main__':
    self_test()
