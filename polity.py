#!/usr/bin/python3
# 508 bytes is the max payload size for a single UDP packet
"Check the Polity name."
"If this message is a CQ, save the time it was sent and time out if no responses are seen."
"SHORT_TIMEOUT = 5, LONG_TIMEOUT = 20"

from uuid import uuid4
import socket
from typing import Callable
from threading import Thread
from queue import Queue
import struct
import bson
import time
import random

# Components of this project
from message import Message
from record import Record, ConstantRecord

POLITY_VERSION = 0.1
multicast_group = ('224.3.29.71', 10000)
# IP_ADDRESS = '239.192.1.100'
MULTICAST_ADDRESS = '224.3.29.71'
PORT_NUMBER = 4242 # 8079 would be ASII 'PO' FIXME This is entirely unused.
TTL = 10
UUID = uuid4()
BUFFER_SIZE = 1024
UTF8 = 'utf-8'
HTTPS_PORT = 443
WAN_TARGET = ('8.8.8.8', HTTPS_PORT) # Google name service. This needs to be up.

def background(job_func: Callable, *args, **kwargs):
    thread = None
    try:
        thread = Thread(target=job_func, daemon=True, *args, **kwargs)
        thread.start()
    except Exception as e:
        print(e)
    return thread

class Polity():
    """Houses the send and receive m ethods that are used to communicate
    in a Polity. May eventually house some Polity maintenance functions. """
    peers = {}
    roles = frozenset(['CMD_LINE', 'UI', 'BRAIN', 'SOUND'])
    system_messages = (['CQ', 'IAM', 'RESEND', # Not exposed to clients.
                        'RELOAD', 'BADID', 'ACK', 'NAK'])
    msg_types = ['PLAY', 'CMD', 'SYS']
    def __init__(self, name='Polity', callback=None, queue=None,
                 multicast_address=MULTICAST_ADDRESS, port=PORT_NUMBER,
                 ttl=TTL, roles=[], monitor=False):
        self.polity_version = POLITY_VERSION
        self.polity = name
        self.roles = roles
        self.id = str(uuid4())
        self.multicast_address = multicast_address
        self.port = port
        self.ttl = struct.pack('b', ttl)
        self.sequence_number = 0
        self.monitor = monitor
        if callback:
            self.callback = callback
            self.listener = self.listener_callback
        else:
            self.queue = queue if queue else Queue() # Accept passed queue or create one.
            self.listener = self.listener_queue
            self.get = self.queue.get

        self.ip = self.ip_address()
        # Create the send socket.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        group = socket.inet_aton(self.multicast_address)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Re-use address.
        # Make the socket multicast-aware, and set TTL.
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl) # Change TTL (=20) to suit
        # Bind to the server address
        server_address = ('', 10000)
        s.bind(server_address)
        self.send_socket = s
        self.receive_socket = s # If this works, it's simpler.
        self.receive_thread = background(self.listener)
        self.timestamp = time.time()
        self.join_or_start_polity()

    def message(self, body='', type='TEXT', reply_to='')->dict:
        """Method for clients to call to get a Message object,
           pre-populated with useful default values."""
        msg =  {
            'version':    self.polity_version,
            'type':       type,
            'to_id':      b'',
            'from_id':    self.id,
            'from_ip':    self.ip,
            'my_number':  self.sequence_number,
            'reply_to':   reply_to,
            'body_len':   len(body),
            'body':       body,
            'body_checksum': 0,
            'reply_function': None
        }
        return Message(msg)

    def reply(self, msg):
        """Method for clients to call to get a reply Message object.
           The input msg is the message we want to reply to."""
        msg =  {
            'version':    self.polity_version,
            'type':       type,
            'to_id':      b'',
            'from_id':    self.id,
            'from_ip':    self.ip,
            'my_number':  self.sequence_number,
            'reply_to':   reply_to,
            'body_len':   len(body),
            'body':       body,
            'body_checksum': 0
        }
        return Message(msg)

    def announce(self)->None:
        msg =  {
            'version':    self.polity_version,
            'polity':     self.polity,
            'type':       'IAM',
            'to_id':      '',
            'from_id':    self.id,
            'from_ip':    self.ip,
            'my_number':  self.sequence_number,
            'reply_to':   0,
            'body_len':   0,
            'body':       '',
            'body_checksum': 0,
            'reply_function': None
        }
        self.send(msg)

    def join_or_start_polity(self)->None:
        msg =  {
            'version':    self.polity_version,
            'polity':     self.polity,
            'type':       'CQ',
            'to_id':      '',
            'from_id':    self.id,
            'from_ip':    self.ip,
            'my_number':  self.sequence_number,
            'reply_to':   0,
            'body_len':   0,
            'body':       '',
            'body_checksum': 0,
            'reply_function': None
        }
        self.send(msg)

    def ip_address(self)->str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(WAN_TARGET)
            return(sock.getsockname()[0])

    def send(self, data):
        self.print_values('Send', data)
        self.send_socket.sendto(self.pack(data), multicast_group)
        self.sequence_number += 1 # Increment for each message sent.

    def receive(self):
        bytes, sender_addr = self.receive_socket.recvfrom(BUFFER_SIZE)
        data = self.unpack(bytes)
        sender_addr = sender_addr[0]
        return self.message_handler(data, sender_addr)

    def print_values(self, id, msg)->None:
            m = [str(msg[key]) for key in msg if msg[key]]
            m = ' '.join(m)
            print(f"{id}: {m}")

    def pack(self, data):
        "Pack up the data as if it were going on a long trip."
        return bson.dumps(data) # .encode(UTF8)

    def unpack(self, data):
        "Unpack the data to be useful to the caller."
        return bson.loads(data)

    # def enter(self):
    #     # Create the standard anounce message.
    #     self.send('Et in Arcadia, ego.')

    def listener_queue(self):
        while True:
            data = self.receive() # Blocks
            if data:
                print(data)
                self.queue.put(data)

    def listener_callback(self):
        self.callback(self.receive())

    def leave(self)->None:
        self.send('BYE') # Something more forma55l?
        self.send_socket.close()

    def message_handler(self, message, address  ):
        msg = Record(message)
        if self.monitor:
            self.print_values('Receive', data)
        if msg.polity != self.polity: #
            # If this is from a different polity:
                # If we have no other members:
                    # Change our polity name.
                    self.polity = msg.polity
                    self.timestamp = time.time()
                    self.announce()
                    return None
        if msg.from_id == self.id:
            if address == self.ip: # id and ip match: Ignore own sends.
                return None
            else: # There's another node using this uuid4 id value!
                print('BAD ID because duplicate.')
                self.id = str(uuid4()) # Change our ID.
        self.peers[address] = msg # Do things here.
        # Real work starts here. Polity-private messages maintain the polity.
        if msg.type in self.system_messages:
            # print(f"System message {msg.type}")
            if msg.type == 'CQ':
                background(self.pause_then_announce)
                return None
        else: # Not a system message, must be a client message.
            return msg

    def pause_then_announce(self):
        random.seed()
        time.sleep(2 * random.random()) # Up to two seconds
        self.announce()

    # def reply(self, msg:ConstantRecord)->None:
    #     response = Record(msg) # We need to modify it.
    #     response.reply_to = msg.my_number # This is a reply to your message.
    #     response.to_id = msg.from_id
    #     response.from_id = self.id
    #     response.type = 'REPLY'
    #     self.send(response)

    # def add_peer(self, address):
    #     pass

def self_test():  # self-test should not be a system message! FIXME
    p = Polity()
    print(f"id: {p.id}")
    print()
    while True:
        msg = Message(p.get())
        print(f"Received: {msg.type} from {msg.from_id}.")


if __name__ == '__main__':
    self_test()
