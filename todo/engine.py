#!/usr/bin/python
import json
import csv
import os, sys
import time
import random
import hashlib
import datetime
import argparse
import requests
import nacl.secret
import nacl.utils
import uuid
import time, datetime
import base64
import re

from pprint import pprint

def isvalid_uuid4(val):
    UUID_PATTERN = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', re.IGNORECASE)
    return UUID_PATTERN.match(val)

def standard_hash(data):
    return hashlib.md5(data).hexdigest()

def standard_time(unix_timestamp):
    return datetime.datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d_%H:%M:%S")

def standard_date(unix_timestamp):
    return datetime.datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d")

def standard_date_to_unix(string):
    return float(datetime.datetime.strptime(string, "%Y-%m-%d_%H:%M:%S").strftime("%s"))

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
        self.id = str(uuid.uuid4())

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
        super(Record, self).__init__()
        self.record_dir = os.path.expanduser("~/.todo/records/")
        self.engine_dir = os.path.expanduser("~/.todo/")
        self.logfile = self.engine_dir + "todo.log"
        self.internal_state = self.engine_dir + "todo.state"


    def add_note(self, date, note):
        self.internal_state_check()
        self.log("Added note: %s, %s\n" % (note.title, standard_date(date)))
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
        if not os.path.isdir(self.record_dir):
            os.mkdir(self.engine_dir)
            os.mkdir(self.record_dir)

        filename = os.path.join(self.record_dir, standard_date(date) + '.json')
        json.dump(content, open(filename, "w"), indent=4, sort_keys=True)

    def print_tasklist(self, date=time.time()):
        self.internal_state_check()
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
        self.internal_state_check()
        record = self.load_record(date)
        self.log("Removed note: %s, %s\n" % (record['notes'][index]['title'] , standard_date(date)))
        record['notes'].pop(index)
        self.save_record(date, record)

    def check_index(self, date, index):
        self.internal_state_check()
        record = self.load_record(date)
        self.log("Checked note: %s, %s\n" % (record['notes'][index]['title'] , standard_date(date)))
        record['notes'][index]['isDone'] = not record['notes'][index]['isDone']
        self.save_record(date, record)

    def log(self, msg):
        with open(self.logfile, "a") as logfile:
            logfile.write(standard_time(time.time()) + "| " + msg)

    def load_state(self):
        if not os.path.isfile(self.internal_state):
            internal_state = {}
            internal_state['last_modified'] = time.time()
            internal_state['created'] = time.time()
            internal_state['last_action'] = time.time()

            return internal_state

        internal_state = json.load(open(self.internal_state, "r"))

        return internal_state

    def save_state(self, state):
        json.dump(state, open(self.internal_state, "w"), indent=4, sort_keys=True)

    def internal_state_check(self):
        internal_state = self.load_state()
        yesterday = float((datetime.datetime.fromtimestamp(internal_state['last_action']) - datetime.timedelta(days=1)).strftime("%s"))

        record_yesterday = self.load_record(internal_state['last_modified'])
        record_today = self.load_record(time.time())

        for i, note in enumerate(record_yesterday['notes']):
            if not note['isDone'] and note not in record_today['notes']:
                note['last_modified'] = standard_time(time.time())
                record_today['notes'].append(note)

        internal_state['last_modified'] = time.time()

        self.save_record(time.time(), record_today)
        self.save_state(internal_state)


class NetworkingLayer:
    VERSION = 10
    def __init__(self, record=None):
        self.record = record

        # User details
        self.username = None
        self.password_hash = None

        # SecretBox for symmetric encryption
        self.box = None

    def init(self, username, password):
        # for use in terminal
        # self.username = raw_input("Logging in to TODO: \n\nusenrame: ")
        # self.password_hash = standard_hash(getpass.getpass("Please insert your password:\n" ))

        self.username = username
        self.password = password
        self.password_hash = standard_hash(password)

        # auth is already established
        if self.box is not None:
            return

        # TODO decode from base 16 first
        key = bin(int(self.password_hash, 16))[:nacl.secret.SecretBox.KEY_SIZE]

        # Establish secretbox
        self.box = nacl.secret.SecretBox(key)

        return

    def encrypt_data(self, data):
        if self.box is None:
            raise ValueError("Box is not initialized. Call init before you can encrypt data")

        nonce = nacl.secret.random(nacl.secret.SecretBox.NONCE_SIZE)
        encrypted = self.box.encrypt(data, nonce)

        return encrypted, nonce

    def decrypt_data(self, data):
        if self.box is None:
            raise ValueError("Box is not initialized. Call init before you can decrypt data")

        plaintext = self.box.decrypt(data)

        return plaintext

    def process_encrypted_note(self, note):

        if not note.has_key('encrypted'):
            Warning("Expected encrypted note, returned None instead")
            return None

        plaintext = self.decrypt_data(base64.b64decode(note['base64']))

        try:
            res_note = json.loads(plaintext)
            return res_note
        except ValueError:
            return None



    def full_sync(self):
        remote_notes_json = self.request_notes()
        remote_notes = json.loads(remote_notes_json)['data']

        print "remote: ", remote_notes

        remote_hashes = {}
        local_hashes = {}

        for note in remote_notes:
            processed_note = self.process_encrypted_note(note['data'])

            # Some decoding members failed
            if processed_note is None: continue
            remote_hashes[standard_hash(processed_note)] = processed_note

        # for note in local_notes:
        for root, dirs, files in os.walk(os.path.expanduser(self.record.record_dir)):
            for name in files:
                if name.endswith('.json'):
                    for note in json.load(open(os.path.join(root, name), 'r'))['notes']:
                        # get rid of legacy
                        if note.has_key('random_hash'):
                            note['id'] = str(uuid.uuid4()) # generates new random
                            note.pop('random_hash')

                        local_hashes[standard_hash(json.dumps(note, indent=4, sort_keys=True))] = note

        pprint(local_hashes.keys())
        pprint(remote_hashes.keys())

        # defines generator for list items not in remote_hashes
        for hash_not_in_remote in (_hash for _hash in local_hashes.keys() if _hash not in remote_hashes.keys()):
            self.upload_note(local_hashes[hash_not_in_remote])

        for hash_not_in_local in (_hash for _hash in remote_hashes.keys() if _hash not in local_hashes.keys()):
            self.save_note_locally(remote_hashes[hash_not_in_remote])

    def request_notes(self):
        r = requests.post(
                'https://data.adinfinitum.ee/store/todo/' + self.username,
                auth=(self.username, self.password),
                json = {
                    'method': "select",
                    'data': {
                        'type': 'note',
                        }
                    }
                )

        return r.text

    def save_note_locally(self, note):

        if isinstance(note, str):
            note = json.loads(note)

        note_date = standard_date(standard_date_to_unix(note['last_modified']))

        r = self.record.load_record(note_date)
        r['notes'].append(note)
        self.record.save_record(note_date, r)


    def upload_note(self, data):
        assert self.box is not None, "cannot construct json, box not constructed; use init"
        assert self.username is not None, "cannot construct json, username missing"
        assert self.password_hash is not None, "cannot construct json, passwordnot entered"

        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True, indent=4)

        encrypted_data, nonce = self.encrypt_data(data)

        r = requests.post(
                'https://data.adinfinitum.ee/store/todo/' + self.username,
                auth=(self.username, self.password),
                json = {
                    'method': 'insert',
                    'data': {
                        'id': str(uuid.uuid4()),
                        'version': self.VERSION,
                        'date': datetime.datetime.fromtimestamp(time.time()).isoformat(),
                        'meta': {},
                        'type': 'note',
                        'data': {'base64': base64.b64encode(encrypted_data),
                            'nonce': base64.b64encode(nonce),
                            'encrypted' : "nacl"}
                        }
                    }
                )

    def log(self, msg):
        pass
        """ with open(self.logfile, "a") as logfile:
            logfile.write(standard_time(time.time()) + "| " + msg) """

