"""
Created on Oct. 12 2011

@author: Jason MacWilliams, William Panting
@TODO: make the mail program parameterizable
@TODO: refactor to use property decorators
"""

import subprocess

def send_mail(addrs, subject, message):
    print("Sending email (%s) to addresses: %s" % (subject, addrs))
    subprocess.Popen('echo "%s" | mailx -s "%s" %s' % (message, subject, addrs), shell=True, executable="/bin/bash")

    # XXX: we might want to attach the logfile or something else here. In that case the order of
    # the print statement and the sendmail should be reversed so the print statement doesn't appear
    # in the log

class mailer:
    def __init__(self, subject="", addrs=[]):
        if type(addrs) != list:
            return
        self.subject = subject
        self.addrs = addrs
        self.message = ""

    def add_address(self, addr):
        if type(addr) == str and not addr in self.addrs:
            self.addrs.append(addr)

    def remove_address(self, addr):
        if type(addr) == str and addr in self.addrs:
            self.addrs.remove(addr)

    def set_subject(self, subject):
        self.subject = subject

    def clear_message(self):
        self.message = ""

    def add_line(self, line):
        self.message = self.message + "\n" + line

    def add_string(self, string):
        self.message = self.message + string

    def send(self):
        if self.subject and self.addrs:
            send_mail(" ".join(self.addrs), self.subject, self.message)
        print("Email report sent")