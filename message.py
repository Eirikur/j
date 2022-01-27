# message.py, The message for the Polity networking system.
# 27 Jan 2022
from record import Record

msg =  {
    'version':  '',
    'type':  '',
    'to_id':  '',
    'from_id':  '',
    'my_number': 0,
    'reply_to': 0,
    'body_len': 0,
    'body': '',
    'body_checksum': 0,
    'reply_function': None
}

class Message(Record):
    def __init__(self):
        self.update(msg)
        pass
