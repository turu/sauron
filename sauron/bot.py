# -*- test-case-name: tests.test_sauronbot -*-
import os
import re
import socket
import time

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import utils
from twisted.internet.defer import Deferred
from twisted.python import log
from twisted.words.protocols import irc
from sauron import urlextractor
from sauron import mailing

WGET_OUT = "/wget.out"

USER_AGENT = "\"Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0\""


class MessageLogger:
    def __init__(self, logdir, channels):
        self.__filemap = {}
        for channel in channels:
            self.__filemap[channel] = open(logdir + "/" + channel + ".log", "a")

    def log(self, message, channel):
        """Write a message to the file."""
        timestamp = time.strftime("[%D %H:%M:%S]", time.localtime(time.time()))
        self.__filemap[channel].write('%s| %s\n' % (timestamp, message))
        self.__filemap[channel].flush()

    def close(self):
        for file in self.__filemap.itervalues():
            file.close()


class SauronBot(irc.IRCClient):
    irc.IRCClient.heartbeatInterval = 45

    def connectionMade(self):
        """Called when a connection is made."""
        self.nickname = self.factory.nickname
        self.realname = self.factory.realname
        irc.IRCClient.connectionMade(self)
        self.startHeartbeat()
        self.factory.resetDelay()
        self.logger = MessageLogger(self.factory.logdir, self.factory.channels)
        log.msg("[connected at %s]" % time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        """Called when a connection is lost."""
        irc.IRCClient.connectionLost(self, reason)
        log.msg("connectionLost {!r}".format(reason))
        self.makeConnection(self.transport)

    # callbacks for events

    def signedOn(self):
        """Called when bot has successfully signed on to server."""
        log.msg("Signed on")
        if self.nickname != self.factory.nickname:
            log.msg('Your nickname was already occupied, actual nickname is '
                    '"{}".'.format(self.nickname))
        for channel in self.factory.channels:
            self.join(channel)

    def joined(self, channel):
        """Called when the bot joins the channel."""
        channel = channel.strip().lower()
        self.logger.log("[{nick} has joined {channel}]".format(nick=self.nickname, channel=channel, ), channel)

    def privmsg(self, user, channel, msg):
        """Called when the bot receives a message."""
        channel = channel.strip().lower()
        sender_nick = user.split('!', 1)[0]
        self.logger.log("{sender}: {quote}".format(channel=channel, sender=sender_nick, quote=msg), channel)
        for match in urlextractor.parseText(msg):
            self.logger.log("url {url} found in message".format(url=match[1]), channel)
            self.__archivize(match[1], user, channel, msg)

    def __archivize(self, match, user, channel, msg):
        timestamp = time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time()))
        target_dir = self.factory.datadir + "/" + channel + "/" + timestamp + "_" + user + "_" + match
        self.logger.log("will archivize {match} under {dir}".format(match=match, dir=target_dir), channel)
        reactor.callWhenRunning(self.__full_local_scan, match, target_dir, msg)
        reactor.callLater(3, self.__shallow_outer_scan, match, target_dir, msg)

    def __full_local_scan(self, match, target_dir, msg):
        out_dir = target_dir + "_local"
        os.makedirs(out_dir)
        retcode = utils.getProcessValue("wget -U " + USER_AGENT
                                        + " --follow-ftp "
                                        + "-r "
                                        + "-N "
                                        + "-l 10 "
                                        + "--no-remove-listing "
                                        + "--no-parent "
                                        + "--convert-links "
                                        + "-p "
                                        + "-w 0.5 "
                                        + "--random-wait "
                                        + "-x "
                                        + "-P " + out_dir
                                        + " " + match
                                        + " > " + out_dir + WGET_OUT
                                        + " 2>&1")
        retcode.addCallback(self.__notify_by_email, match, out_dir, msg)

    def __shallow_outer_scan(self, match, target_dir, msg):
        out_dir = target_dir + "_outer"
        os.makedirs(out_dir)
        retcode = utils.getProcessValue("wget -U " + USER_AGENT
                                        + " --follow-ftp "
                                        + "-r "
                                        + "-N "
                                        + "-H "
                                        + "-l 3 "
                                        + "--no-remove-listing "
                                        + "--no-parent "
                                        + "--convert-links "
                                        + "-p "
                                        + "-w 0.5 "
                                        + "--random-wait "
                                        + "-x "
                                        + "-P " + out_dir
                                        + " " + match
                                        + " > " + out_dir + WGET_OUT
                                        + " 2>&1")
        retcode.addCallback(self.__notify_by_email, match, out_dir, msg)

    def __notify_by_email(self, return_code, match, download_root, msg):
        download_message = "Finished download of {match}\n.Stored under {root}\nDownload return code {code}\n\t- message:\n{msg}" \
            .format(match=match, root=download_root, code=return_code, msg=msg)
        log.msg(download_message)
        recipients = self.factory.mail_recipients
        subject = "Url {url} detected and downloaded".format(url=match)
        self.factory.mail_server.send_mail(recipients, subject, download_message)


class SauronBotFactory(protocol.ReconnectingClientFactory):
    protocol = SauronBot

    def __init__(self, channels, nickname, realname, datadir, logdir, mail_recipients, mail_server):
        """Initialize the bot factory with our settings."""
        self.mail_server = mail_server
        self.channels = channels
        self.nickname = nickname
        self.realname = realname
        self.datadir = datadir
        self.logdir = logdir
        self.mail_recipients = mail_recipients

    def clientConnectionLost(self, connector, reason):
        log.msg("Connection lost. Reconnecting...")
        protocol.ReconnectingClientFactory.clientConnectionLost(connector, reason)

    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed. Reconnecting...")
        protocol.ReconnectingClientFactory.clientConnectionFailed(connector, reason)




