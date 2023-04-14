#!/usr/bin/python3
# Time-stamp: <2023-04-14 19:55:10 (eh)>
# Python
import sys
import os
# Standard library
import time
import datetime
from datetime import timedelta
import calendar


# """ Concept of listing only sched. items that are later than now.
# Don't list items that are in the past. Hmmm. """

# We now have three trigger types. For cancel, list all (new command) we should
# return lists for each if there are jobs in those categories.

### Break out into parse and schedule modules.








# from typing import Callable
# import traceback
from itertools import chain
import logging
# import subprocess
# from subprocess import CalledProcessError
# from subprocess import run
# from subprocess import DEVNULL

# Third party
import parsedatetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from pytz import timezone
# import pdbr # debugger

triggers_to_formats = {CronTrigger: 'cron', DateTrigger: 'date',
                       IntervalTrigger: 'interval'}
formats_to_triggers = dict(map(reversed, triggers_to_formats.items()))
timed_triggers = ['cron', 'interval']
all_triggers = ['date', 'cron', 'interval']



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
minute_words = ['m', 'min', 'minute', 'minutes']
hour_words =  ['hr', 'hour', 'hours']
schedule_types = ['date', 'cron', 'interval']
time_words = list(chain(relative_time_words, abbrev_days, long_days))
repeat_words =['each', 'every', 'repeat', 'repeating']
parse_date_codes = [None, 'date', 'time', 'datetime']

colon = ':'
nothing = ''
newline = '\n'
space = ' '
alert_sound_file = '/home/eh/Customization/Sounds/Bong.wav'
utility_path = path = os.path.dirname(os.path.abspath(__file__))
X_display = ':0'
alert_program = f"{utility_path}/dialog.py"
tracing = None # for trace command
prepositions = ['at', 'on']

commands = ['all', 'test', 'status', 'crash', 'now', 'list',
            'ding', 'bong', 'chime']


def do_command(cmd_str: str)->str:
    # 8 October 2021: This needs to be a better parser, at least a bit.
    # 27 October: Now we have arguments and arguments_string
    # 15 November: Working to integrate APScheduler.
    # try:
    command, modifier, arguments = get_cmd(cmd_str)
    argument_string = ' '.join(arguments)
    full_string = space.join([command, modifier, argument_string])
    no_modifier = space.join([modifier, argument_string])

    if command == 'all':
        if q := do_command('list all'):
            return q
        else:
            return "No jobs at all"
    if command == 'test':
        return test()
    elif command == 'status':
        return status()
    elif command == 'crash':
        return f"{1/0}"
    elif command == 'now':
        return 'noop'
    elif command == 'list':

        q = jobs_list(modifier, argument_string)
        print(f"command line: list {modifier} {argument_string}")
        return q
    elif command in ['cancel', 'remove']:
        return cancel_jobs(modifier, argument_string)
    elif command == 'every':
        print(f"Every: {argument_string}")
        interval_value = modifier
        interval_name = arguments[0]
        interval_command = arguments[1:] # through end of line.
        print(f"Every {interval_value} {interval_name}: {interval_command}")
        return schedule_repeating_interval(interval_value, interval_name, interval_command)
    elif command == 'alert':
        alert(f"Alert! {no_modifier}")
    elif command in ['ding', 'bong', 'chime']:
        audible_alert()
        return('Bong!')
    elif command in ['canceled', 'removed']:
        return 'noop'
    elif command in ['sl', 'buy', 'purchase', 'shopping']:
        if modifier == 'list':
            return 'Shopping  list goes here.'
        return 'noop'
    elif command in ['purge', 'expunge']:
        return 'noop'
    elif command in ['min.', 'minutes']:
        return timer(command, arguments)
    elif command in ['sec.', 'seconds']:
        return 'noop'
    elif command in ['undo', 'restore']:
        return 'noop'
    # elif command == 'trace':
    #     global tracing
    #     tracing = tracefunc if tracing ==  else tracefunc
    #     sys.setprofile(tracing)
    #     return "Tracing {tracing}."
    elif command == 'shutdown':
        return shutdown()
    elif command == 'hourly':
        return schedule_hourly(argument_string, no_visual=True)
    elif command == 'cron' or command == 'c':
        return cron_jobs(argument_string)
    elif command in intervals:
        print(f"Command in intervals: {command}")
        return schedule_repeating_interval(argument_string)
    elif command in repeat_words:
        print(f"Command in repeat_words: {command}")
        return schedule_repeating_item(argument_string)
    elif command in ['sched', 'schedule'] or parse_date_from(full_string)[1]: # There is a schedule item.
        return schedule_item(cmd_str)
    else: # We did not match against a known command.
        msg = f"{command} is not a recognized command and no time field found in command line."
        info(msg)
        return msg

def scheduled_jobs(trigger, search_target):
    this_trigger = formats_to_triggers[trigger]
    print(f"trigs {trigger}  {this_trigger}")

    return [job for job in scheduler.get_jobs()
        if job.trigger == this_trigger and search_target in repr(job)]

def jobs_list(trigger, search_target):
    """
    list cron sound
    list all Steve
    """
    if not trigger: trigger = 'all'

    print(f"Trigger: {trigger}")
    print(f"Target string: {search_target}")
    report = ''

    if trigger == 'all':
        for trig in all_triggers:
            if jobs := scheduled_jobs(trig, search_target): # If we found jobs
                print(f"We found {len(jobs)} {trig} jobs.")
                report += formatted_jobs(trig, jobs) # Formats depend on the trigger type.
            else:
                 report += f" No {trig} jobs."
    else:
        trigger = trigger if trigger in timed_triggers else 'date'
        if jobs := scheduled_jobs(trigger, search_target):
            print(f"We found {len(jobs)} {trig} jobs.")
            report += formatted_jobs(trig, jobs) # Formats depend on the trigger type.
        else:
            report += f" No {trigger} jobs."

    return report

def cancel_jobs(modifier, arguments):
    # if len(arguments) >= 2:
    schedule_type = modifier # 'cancel cron bong'
    argument_string = space.join(arguments)
    print('schedule_type:', schedule_type)
    if schedule_type == 'cron' or schedule_type in intervals:
        return cancel_cron_jobs(argument_string)
    elif schedule_type == 'interval' or schedule_type in repeat_words:
        return cancel_interval_jobs(argument_string)
    else: # Cancelling a date-triggered event.
        return cancel_date_jobs(argument_string)


def timer(item: str)->str:
    "schedule a cron item as a timer."
    pass

def schedule_hourly(item:str, no_visual=False)->str:
    # no_visual is for hourly chimes.
    item = without_time_words(item)
    func = sound if no_visual else alert
    scheduler.add_job(sound, 'cron', hour='*', args=[item],
                            replace_existing=True)
    msg = f"Scheduled '{item}', repeating on the hour."
    print(msg)
    return msg

def schedule_repeating_item(item:str)->str:
    print(f"Schedule Repeating Item: {item}")
    target_date, parse_status = parse_date_from(item)
    hour = target_date.hour if not parse_status else time_string_in(item)
    # if not hour:
    #     print("No hour specified")
    item = without_time_words(item)
    trigger = 'cron' # Apscheduler trigger method.
    # Find the interval specifier
    interval_words = [word for word in intervals if word in item]
    if len(interval_words) > 1:
        msg = f"{interval_words}: Only one repeat interval can be specified."
        return msg
    else:
        interval = interval_words[0]

    # if interval == 'hourly':



def schedule_repeating_interval(interval_value, interval_name, interval_command)->str:
    interval_value = int(interval_value)
    if interval_name in minute_words:
        job = scheduler.add_job(alert, 'interval', minutes=interval_value, args=[interval_command],
                                replace_existing=True)
        return repr(job)
    elif interval_name in hour_words:
        job = scheduler.add_job(alert, 'interval', hours=interval_value, args=[inormterval_command],
                                replace_existing=True)
        return repr(job)
    else: # support days, weeks
        return f"Interval {interval_name} is not implemented yet."

    msg = f"Scheduled '{interval_command}', every {interval_value} {interval_name}."
    return msg # Failure is the early return, above.

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
        return f'There are no scheduled jobs matching "{target}"'

def cancel_interval_jobs(target: str)->str:
    if cancel_list := jobs_filter(interval_jobs_list(), target): # jobs filtered.
        [job.remove() for job in cancel_list]
        return canceled_text(formatted_cron_jobs(cancel_list))
    else:
        return f'There are no scheduled jobs matching "{target}"'

def status()->str:
    """Return some status information to the client.
       This was first needed so that the client
       could use it to test that the server had
       actually restarted."""
    msg = ['Server operational.',
           time.ctime()]
    return newline.join(msg)

def test ()->str:
    now = datetime.datetime.now()
    target_date = now + timedelta(minutes=1)
    # when = target_date.ctime()
    when = target_date.strftime("%H:%M")
    msg = "Scheduled Test Alert!"
    print(f"Command: {when} {msg}")
    return do_command(f"{when} {msg}")


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
    return jobs_list(date, target)
#     return formatted_date_jobs(jobs)
# else:
#     return "No current appointments."

def cron_jobs(target: str)->str:
    if jobs := jobs_filter(cron_jobs_list(), target):
        return formatted_cron_jobs(jobs)
    else:
        return 'No current cron jobs.'

def interval_jobs(target: str)->str:
    if jobs := jobs_filter(interval_jobs_list(), target):
        return formatted_interval_jobs(jobs)
    else:
        return "No current interval jobs"

def formatted_interval_jobs(jobs):
    pass

def jobs_filter(jobs: list, target:str)->list:
    if jobs and target: # Neither can be empty.
        print(jobs, target)
        job_reprs = [repr(job) for job in jobs]
        target = target.casefold()
        return [job for job in job_reprs if target in job.casefold()]
    elif jobs: # We have jobs but target is null, return all of them.
        return jobs
    else:
        return None



def formatted_cron_jobs(jobs: list)->str:
    pass
def formatted_jobs(trigger, jobs: list)->str:
    if trigger == 'date':
        today = datetime.datetime.now().date()
        return_string = "No current appointments."
        return_list = []

        if jobs:
            for job in jobs:
                job_type = job.name.capitalize()
                text = job.args[0]
                run_date = job.trigger.run_date
                date_string = run_date.ctime()[:-8] # Remove seconds and year
                list_entry = f"{date_string} - {text} - {job_type}"
                if run_date.date() == today:
                    list_entry = today_text(list_entry) # Apply rendering.
                return_list.append(list_entry)
            return newline.join(return_list)

    elif trigger == 'cron':
        ####### Only hourly works, see below.
        strings = []
        for job in jobs:
            for interval in intervals:
                if interval[:-2] in str(job.trigger):
                    print(interval, str(job.trigger))
                    if job.args == (None,):
                        msg = 'Anonymous job'
                    else:
                        msg = space.join(job.args)
                        strings.append(f"Hourly - {msg} - {job.name.capitalize()}")
        return newline.join(strings)

    elif trigger == 'interval':
        return newline.join([f"{str(job)}" for job in jobs])

    raise ValueError(trigger, jobs)



def schedule_item(item: str)->str:
    """"Parse string and schedule it as a job.
    """
    target_date, parse_status = parse_date_from(item)
    item = without_time_words(item)
    if item == None:
        print('Oooops!')

    now = datetime.datetime.now()
    target_hour, target_minute = target_date.hour, target_date.minute
    past = False
    if target_date <= now:
        past = True
        target_date = target_date + timedelta(days=1)
        warning = 'Job time was earlier today so it was scheduled for tommorrow.'
    # print(f"item: {item}")
    # print(newline.join([repr(job) for job in date_jobs_list()]))
    # match = [job for job in date_jobs_list() if job.trigger.run_date == target_date and job.args[0] == item]

    if jobs := scheduler.get_jobs():
        date_jobs = [job for job in jobs if job.trigger == DateTrigger]
        for job in date_jobs:
            print(f"job: {job}")
            print(item, job.args[0])
            if job.args[0] == item:
                print('debug: ', job.trigger.run_date.replace(tzinfo=None), target_date)
            if job.trigger.run_date.replace(tzinfo=None) == target_date: # Beware timezones! Use UTC!
                msg = 'That would be a duplicate.'
                print(msg)
                return msg

    # Site of the problem with ['this']
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
    visual_alert(msg)

def audible_alert()->None:
    # info(f"Bong! at {time.ctime()}")
    sound('Bong!')

def sound(msg: str)->None:
    # shell('/usr/bin/play', '-q', alert_sound_file, 'gain -20') # '/dev/null')
    print("Not emitting sound: {msg}")
    return

def audible_warning_alarm()->None:
    "Play a warning or klaxon sound until popup is dismissed."
    pass # No implementation yet.

def visual_alert(msg:str)->None:
    alert_dialog(msg)


def notify(msg: str)->bool:
    msg = f"'{msg} at {time.ctime()}'"
    shell_cmd(f"/usr/bin/notify-send '{msg}'")
    return True

def alert_dialog(msg: str)->bool:
    print('blocked: alert_dialog', msg)
    # subprocess.Popen([sys.executable, alert_program, f"{msg}"])


def shell_cmd(command: str):
    print(f"--Blocked--Command: {command}")
    result = None
    try:
        # result = run(command, capture_output=True, check=True, shell=True) #
        pass
    except CalledProcessError as e:
        print(e)
    except Exception as e:
        print(e)
        raise e('shell_cmd')


# def shell(*args)->bool:
#     os.putenv("DISPLAY", ":0")
#     return shell_cmd(args)


def shutdown():
    "Shut down to leave a clean state."
    # TODO persistent storage, other services.
    scheduler.shutdown()
    return "Scheduler has been shut down."

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
    do_command('meet Joe on Wednesday')
    # New today
    do_command('1400 daily hydrocortisone')
    do_command('hourly test alert from self-test')
    do_command('cron')
    do_command('cron hourly bong')
    do_command('list')
    do_command('cancel hourly alert')    # print()
    # print_jobs_filtered('test')
    # print()
    # print_jobs_filtered('simple')
    # print()
    # print('Cancel jobs containing test...')
    # cancel_jobs('test')
    # print()
    # print_jobs_filtered('')
    # do_command('tomorrow 0700 make early call')
    # canceled_list = do_command('cancel early')
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
