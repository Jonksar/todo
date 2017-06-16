#!/usr/bin/python

import json
import csv
import os, sys
import time
import random
import hashlib
import datetime
import argparse

def standard_hash(data):
    return hashlib.md5(data).hexdigest()

def standard_time(unix_timestamp):
    return datetime.datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d_%H:%M:%S")

def standard_date(unix_timestamp):
    return datetime.datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d")

class PrintableObject(object):
    def __init__(self):
        pass

    def __str__(self):
        return "class name: " + self.__class__.__name__ + "\n\n(" + ", \n".join([str(k) + ": " + str(v) for k, v in self.__dict__.items()]) + ")"

    def __repr__(self):
        return self.__str__()

class TodoNote(PrintableObject):
    def __init__(self, title="Title", description=""):
        self.time_created = time.strftime("%Y-%m-%d-%H-%M-%S")
        self.last_modified = self.time_created
        self.isDone = False
        self.title = title
        self.description = description
        self.random_hash = hashlib.md5(os.urandom(32)).hexdigest()

    def to_dict(self):
        return self.__dict__

    def terminal_print(self):
        res = ""

        res += self.title
        # res += ', ' + self.description if self.description is not None or self.description is not '' else ''
        res += (50 - len(res)) * ' ' + ' /DONE/' if self.isDone else ''

        return res

class Record(PrintableObject):
    def __init__(self):
        self.record_dir = os.path.expanduser("~/.todo/records/")

    def add_note(self, date, note):
        filename = os.path.join(self.record_dir, standard_date(date) + '.json')
        record = self.load_record(date)
        record['notes'].append(note.to_dict())
        self.save_record(date, record)

    def load_record(self, date):
        filename = os.path.join(self.record_dir, standard_date(date) + '.json')

        # in case we don't yet have this file
        if not os.path.isfile(filename):
            return {'notes': []}

        return json.load(open(filename, "r"))

    def save_record(self, date, content):
        filename = os.path.join(self.record_dir, standard_date(date) + '.json')
        json.dump(content, open(filename, "w"), indent=4, sort_keys=True)

    def print_tasklist(self, date=time.time()):
        record = self.load_record(date)

        res = ""
        if len(record['notes']) != 0:
            res += "\n"

            for i, note in enumerate(record['notes']):
                # Convert json dict to object. hehe
                proxy = TodoNote()
                proxy.__dict__ = note

                res += "\n %d ) %s" % (i, proxy.terminal_print())
            res += "\n"

        else:
            res += "\n\nThis todo record is empty.\n"

        print res

    def remove_at_index(self, date, index):
        record = self.load_record(date)
        record['notes'].pop(index)
        self.save_record(date, record)

    def check_index(self, date, index):
            record = self.load_record(date)
            record['notes'][index]['isDone'] = not record['notes'][index]['isDone']
            self.save_record(date, record)

# class Engine(PrintableObject):
#     def __init__(self):
#         self.engine_dir = os.path.expanduser("~/.todo/")
#         self.logfile = self.engine_dir + "todo.log"
#         self.internal_state = self.engine_dir + "todo.state"
#
#         self.record = Record()
#
#     def log(self, msg):
#         with open(self.logfile, "a") as logfile:
#             logfile.write(standard_time(time.time()) + "| " + msg)
#
#     def check(self):
#
#     def load_state(self):
#         if not os.path.isfile(self.internal_state):
#
#         internal_state = json.load(open(self.internal_state, "r"))
#
#

