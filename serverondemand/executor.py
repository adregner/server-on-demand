import re
import logging
from socket import timeout as sock_timeout

from paramiko import SSHClient
from paramiko.client import MissingHostKeyPolicy

logger = logging.getLogger(__name__)

class Executor(object):
    def __init__(self, hostname, username, key, debug=False):
        self.debug = debug
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(MissingHostKeyPolicy())
        self.client.connect(hostname, username=username, pkey=key,
                look_for_keys=False, compress=True)

        self.chan = self.client.invoke_shell()
        self.chan.settimeout(0.1)
        self.prompt_regex = "# $"
        self.read()

        self.set_prompt()

    def set_prompt(self):
        prompt = "fio8g3rfubsd97g34iu:# "
        self.chan.send('export PS1="%s" PS2=""\n' % prompt)
        self.prompt_regex = re.escape(prompt) + '$'
        self.read()

    def run(self, cmdline):
        """Run a command and piece out the console output."""
        # run the command
        cmdline += "; echo\n"
        self.chan.send(cmdline)

        # piece out the response
        response = self.read()
        m = re.match(re.escape(cmdline) + "(.*)" + self.prompt_regex, response)

        # always return something
        if m:
            return m.group(1)
        else:
            return response

    def recv(self, how_much = 1024):
        """Reads bytes from the session, catching timouts."""
        try:
            data = self.chan.recv(how_much)
            logger.debug("recv %d bytes: %s" % (len(data), repr(data)))
            return data
        except sock_timeout:
            return None

    def read(self):
        """Reads until the prompt is seen again."""
        data = ''
        buf = self.recv()

        while not re.search(self.prompt_regex, data):
            if buf is not None:
                data += buf
            buf = self.recv()

        logger.debug("returning buffer: %s" % data)
        return data

    def open_sftp(self):
        return self.client.open_sftp()

    def close(self):
        try: self.chan.close()
        except: pass

        try: self.client.close()
        except: pass

