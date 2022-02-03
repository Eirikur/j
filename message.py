# message.py, The message for the Polity networking system.
# 27 Jan 2022
from record import Record, ConstantRecord

# class MsgType(Enum):
#     CQ     = auto()
#     REPLY  = auto()
#     BAD_ID = auto()




msg =  {
    'version':  float(),
    'polity': '',
    'type':  '',
    'to_id':  '',
    'from_id':  '',
    'from_ip': '',
    'my_number': 0,
    'reply_to': 0,
    'body_len': 0,
    'body': '',
    'body_checksum': 0
}

class Message(Record):
    """Record does all the magic of preventing new keys,
    and type-checking against the default values."""
    def __init__(self, source_dict={}):
        self.update(msg) # Template above
        self.update(source_dict) # Must be a dict, empty is okay.
        pass
