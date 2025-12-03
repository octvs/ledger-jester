import csv
import logging
import os
import re
import subprocess
from queue import Empty, Queue
from subprocess import PIPE, Popen
from threading import Thread

from ledger_jester.converter import Converter

csv.register_dialect(
    "ledger", delimiter=",", quoting=csv.QUOTE_ALL, escapechar="\\"
)


class Ledger:
    def filter_accounts(self, accts, exclude):
        accts_filtered = [a for a in accts if a != exclude]
        if accts_filtered:
            return accts_filtered[-1]
        else:
            return None

    def get_account_by_payee(self, payee, exclude):
        self.load_payees()
        return self.filter_accounts(self.payees.get(payee, []), exclude)

    def add_payee(self, payee, account):
        if payee not in self.payees:
            self.payees[payee] = []
        if account not in self.payees[payee]:
            self.payees[payee].append(account)

    def __init__(self, ledger_file=None, no_pipe=True):
        self._item = ""

        def enqueue_output(out, queue):
            buff = ""
            while buff is not None:
                buff = out.read(1)
                if buff is not None:
                    self._item += buff
                if self._item.endswith("] "):  # prompt
                    queue.put(self._item[0:-2])
                    self._item = ""
            out.close()

        self.use_pipe = (os.name == "posix") and not (no_pipe)
        self.args = ["ledger", "--args-only"]
        if ledger_file is not None:
            self.args += ["-f", ledger_file]
        if self.use_pipe:
            self.p = Popen(
                self.args,
                bufsize=1,
                stdin=PIPE,
                stdout=PIPE,
                universal_newlines=True,
                close_fds=True,
            )
            self.q = Queue()
            self.t = Thread(
                target=enqueue_output, args=(self.p.stdout, self.q)
            )
            self.t.daemon = True  # thread dies with the program
            self.t.start()
            # read output until prompt
            try:
                self.q.get(True, 5)
            except Empty:
                logging.error("Could not get prompt (]) from ledger!")
                logging.error("Received: %s" % (self._item))
                exit(1)

        self.payees = None

    @staticmethod
    def pipe_quote(a):
        def quote(s):
            s = s.replace("/", "\\\\/")
            s = s.replace("%", "")
            if not (re.match(r"^\w+$", s)):
                s = '"%s"' % (s)
            return s

        return [quote(s) for s in a]

    def run(self, cmd):
        if self.use_pipe:
            self.p.stdin.write("csv ")
            self.p.stdin.write(" ".join(Ledger.pipe_quote(cmd)))
            self.p.stdin.write("\n")
            logging.debug(" ".join(Ledger.pipe_quote(cmd)))
            try:
                return csv.reader(self.q.get(True, 5), dialect="ledger")
            except Empty:
                logging.error("Could not get prompt from ledger!")
                exit(1)
        else:
            cmd = self.args + ["csv"] + cmd
            return csv.reader(
                subprocess.check_output(
                    cmd, universal_newlines=True
                ).splitlines(),
                dialect="ledger",
            )

    def check_transaction_by_id(self, key, value):
        q = ["-E", "meta", "%s=%s" % (key, Converter.clean_id(value))]
        try:
            next(self.run(q))
            return True
        except StopIteration:
            return False

    def load_payees(self):
        # TODO: Use only related payees? Like a graph
        # If two candidates equal occurence include both
        # Maybe if the spending same amunt use the same xact
        if self.payees is None:
            self.payees = {}
            r = self.run(["show", "--actual"])
            for line in r:
                self.add_payee(line[2], line[3])

    def get_autosync_payee(self, payee, account):
        q = [
            account,
            "--last",
            "1",
            "--format",
            "%(quoted(payee))\n",
            "--limit",
            'tag("AutosyncPayee") == "%s"' % (payee),
        ]
        r = self.run(q)
        try:
            return next(r)[0]
        except StopIteration:
            return payee
