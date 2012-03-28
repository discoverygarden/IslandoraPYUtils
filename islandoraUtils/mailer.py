"""
Created on Oct. 12 2011

@author: Jason MacWilliams, William Panting
@TODO: make the mail program parameterizable
@TODO: refactor to use property decorators
"""

import subprocess

def send_mail(addresses, subject, message):
    subprocess.Popen('echo "%s" | mailx -s "%s" %s' % (message, subject, addresses), shell=True, executable="/bin/bash")

    # XXX: we might want to attach the logfile or something else here. In that case the order of
    # the print statement and the sendmail should be reversed so the print statement doesn't appear
    # in the log

class mailer:
    def __init__(self, subject="", addresses=[]):
        if type(addresses) != list:
            return
        self.subject = subject
        self.addresses = addresses
        self.message = ""

    def add_address(self, address):
        if type(address) == str and not address in self.addresses:
            self.addresses.append(address)

    def remove_address(self, address):
        if type(address) == str and address in self.addresses:
            self.addresses.remove(address)

    def set_subject(self, subject):
        self.subject = subject

    def clear_message(self):
        self.message = ""

    def add_line(self, line):
        self.message = self.message + "\n" + line

    def add_string(self, string):
        self.message = self.message + string

    def send(self):
        if self.subject and self.addresses:
            send_mail(" ".join(self.addresses), self.subject, self.message)
        print("Email report sent")