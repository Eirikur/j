#!/usr/bin/python3
# 508 bytes is the max payload size for a single UDP packet
from uuid import uuid4
import socket

from typing import Callable
from threading import Thread
from queue import Queue
import struct
import bson

# This project's components.
from dotdict import DotDict, StrictDotDict

multicast_group = ('224.3.29.71', 10000)

IP_ADDRESS = '224.3.29.71'
PORT_NUMBER = 4242 # 8079 would be ASII 'PO'
TTL = 1
UUID = uuid4()
BUFFER_SIZE = 1024
UTF8 = 'utf-8'


message = StrictDotDict(



def background(job_func: Callable, *args, **kwargs):
    thread = None
    try:
        thread = Thread(target=job_func, daemon=True, *args, **kwargs)
        thread.start()
    except Exception as e:
        print(e)
    return thread

class Polity():
    """Houses the send and receive methods that are used to communicate
    in a Polity. May eventually house some Polity maintenance functions. """
    peers = {}

    def __init__(self, callback=None, queue=None, address=IP_ADDRESS, port=PORT_NUMBER, ttl=TTL):
        self.address = address
        self.port = port
        self.ttl = struct.pack('b', TTL)
        if callback:
            self.callback = callback
            self.listener = self.listener_callback
        else:
            self.queue = queue if queue else Queue() # Accept passed queue or create one.
            self.listener = self.listener_queue
            self.get = self.queue.get


        # Create the send socket.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind to the server address
        server_address = ('', 10000)
        s.bind(server_address)
        # Make the socket multicast-aware, and set TTL.
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl) # Change TTL (=20) to suit
        self.send_socket = s
        # Tell the operating system to add the socket to the multicast group
        # on all interfaces.
        group = socket.inet_aton(self.address)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.receive_socket = s # If this works, it's simpler.
        self.receive_queue = queue if queue else Queue()
        self.receive_thread = background(self.listener)

    def send(self, data):
        self.send_socket.sendto(self.pack(data), multicast_group)

    def receive(self):
        bytes, sender_addr = self.send_socket.recvfrom(BUFFER_SIZE)
        data = self.unpack(bytes)
        self.message_handler(data)
        return data

    def pack(self, data):
        "Pack up the data as if it were going on a long trip."
        return data.encode(UTF8)

    def unpack(self, data):
        "Unpack the data to be useful to the caller."
        return data.decode(UTF8)

    def enter(self):
        # Create the standard anounce message.
        self.send('Et in Arcadia, ego.')

    def listener_queue(self):
        while True:
            data = self.receive() # Blocks
            print(data)
            self.receive_queue.put(data)

    def listener_callback(self):
        self.callback(self.receive())

    def leave():
        self.send('BYE') # Something more formal?
        self.send_socket.close()

    def message_handler(self, message, address):
        if address not in  self.peers:

            self.peers.address = None # Do things here.


    def add_peer(address):
        pass


def self_test():
    p = Polity()
    message = 'Et in Arcadia ego.'
    p.send(message)
    response = p.receive()
    if message == response:
        print('No garbling.')
    else:
        print('We had a problem:')
        print(message)
        print(response)

    print('Done.')

if __name__ == '__main__':
    import sys

    self_test()
