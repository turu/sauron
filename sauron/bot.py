# -*- test-case-name: tests.test_sauronbot -*-
import os
import re
import time

from twisted.internet import protocol
from twisted.internet import reactor
from twisted.python import log
from twisted.words.protocols import irc
from sauron import urlextractor

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
    def connectionMade(self):
        """Called when a connection is made."""
        self.nickname = self.factory.nickname
        self.realname = self.factory.realname
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(self.factory.logdir, self.factory.channels)
        log.msg("[connected at %s]" % time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        """Called when a connection is lost."""
        irc.IRCClient.connectionLost(self, reason)
        log.msg("connectionLost {!r}".format(reason))

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
        self.logger.log("[{nick} has joined {channel}]".format(nick=self.nickname, channel=channel, ), channel)

    def privmsg(self, user, channel, msg):
        """Called when the bot receives a message."""
        sender_nick = user.split('!', 1)[0]
        self.logger.log(
            "received message on {channel}, by {sender}:\n {quote}".format(channel=channel, sender=sender_nick,
                                                                           quote=msg), channel)
        for match in urlextractor.parseText(msg):
            self.logger.log("url {url} found in message".format(url=match[1]), channel)
            self.__archivize(match[1], user, channel)

    def __archivize(self, match, user, channel):
        timestamp = time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time()))
        target_dir = self.factory.datadir + "/" + channel + "/" + timestamp + "_" + user + "_" + match
        self.logger.log("will archivize {match} under {dir}".format(match=match, dir=target_dir), channel)
        reactor.callWhenRunning(self.__full_local_scan, match, target_dir)
        reactor.callLater(3, self.__shallow_outer_scan, match, target_dir)

    def __full_local_scan(self, match, target_dir):
        out_dir = target_dir + "_local"
        os.system("wget -U " + USER_AGENT
                  + " --follow-ftp "
                  + "-r "
                  + "-N "
                  + "-l inf "
                  + "--no-remove-listing "
                  + "--convert-links "
                  + "-p "
                  + "-w 0.1 "
                  + "--random-wait "
                  + "-x "
                  + "-P " + out_dir
                  + " " + match
                  + " > " + out_dir + WGET_OUT
                  + " 2>&1")

    def __shallow_outer_scan(self, match, target_dir):
        out_dir = target_dir + "_outer"
        os.system("wget -U " + USER_AGENT
                  + " --follow-ftp "
                  + "-r "
                  + "-N "
                  + "-H "
                  + "-l 3 "
                  + "--no-remove-listing "
                  + "--convert-links "
                  + "-p "
                  + "-w 0.1 "
                  + "--random-wait "
                  + "-x "
                  + "-P " + out_dir
                  + " " + match
                  + " > " + out_dir + WGET_OUT
                  + " 2>&1")


class SauronBotFactory(protocol.ClientFactory):
    protocol = SauronBot

    def __init__(self, channels, nickname, realname, datadir, logdir):
        """Initialize the bot factory with our settings."""
        self.channels = channels
        self.nickname = nickname
        self.realname = realname
        self.datadir = datadir
        self.logdir = logdir