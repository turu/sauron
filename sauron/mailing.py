import abc
import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email.mime.text import MIMEText

from twisted.mail.smtp import sendmail


class MailServer(object):
    @abc.abstractmethod
    def send_mail(self, send_to, subject, text, files):
        """
        :type send_to: list
        :type subject: str
        :type text: str
        :type files: list
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def close(self):
        raise NotImplementedError()


class NoopMailServer(MailServer):
    def send_mail(self, send_to, subject, text, files):
        pass

    def close(self):
        pass


class DefaultMailServer(MailServer):
    def __init__(self, my_address, server="127.0.0.1", port=25, user=None, passwd=None):
        super(DefaultMailServer, self).__init__()
        self.__my_address = my_address
        self.__server = server
        self.__port = port
        self.__user = user
        self.__passwd = passwd
        self.__startup()

    def send_mail(self, send_to, subject, text, files=None):
        msg = MIMEMultipart(
            From=self.__my_address,
            To=COMMASPACE.join(send_to),
            Date=formatdate(localtime=True),
            Subject=subject
        )
        msg.attach(MIMEText(text))

        for f in files or []:
            with open(f, "rb") as fil:
                msg.attach(MIMEApplication(
                    fil.read(),
                    Content_Disposition='attachment; filename="%s"' % basename(f)
                ))

        self.__smtp.sendmail(self.__my_address, send_to, msg.as_string())

    def __startup(self):
        self.__smtp = smtplib.SMTP(host=self.__server, port=self.__port)
        self.__smtp.starttls()
        if self.__user is not None:
            self.__smtp.login(self.__user, self.__passwd)

    def close(self):
        self.__smtp.close()