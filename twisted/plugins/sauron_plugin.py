from ConfigParser import ConfigParser
import os

from twisted.application.service import IServiceMaker, Service
from twisted.internet.endpoints import clientFromString
from twisted.plugin import IPlugin
from twisted.python import usage, log
from zope.interface import implementer

from sauron.bot import SauronBotFactory


class Options(usage.Options):
    optParameters = [
        ['config', 'c', 'settings.ini', 'Configuration file.'],
    ]


class SauronBotService(Service):
    _bot = None

    def __init__(self, endpoint, channels, nickname, realname, datadir, logdir):
        self._endpoint = endpoint
        self._channels = channels
        self._nickname = nickname
        self._realname = realname
        self._datadir = datadir
        self._logdir = logdir

    def startService(self):
        """Construct a client & connect to server."""
        from twisted.internet import reactor

        def connected(bot):
            self._bot = bot

        def failure(err):
            log.err(err, _why='Could not connect to specified server.')
            reactor.stop()

        client = clientFromString(reactor, self._endpoint)
        factory = SauronBotFactory(
            self._channels,
            self._nickname,
            self._realname,
            self._datadir,
            self._logdir
        )

        return client.connect(factory).addCallbacks(connected, failure)

    def stopService(self):
        """Disconnect."""
        if self._bot and self._bot.transport.connected:
            self._bot.transport.loseConnection()


@implementer(IServiceMaker, IPlugin)
class BotServiceMaker(object):
    tapname = "sauron"
    description = "The eye of the Sauron casts its shadow upon you..."
    options = Options

    def makeService(self, options):
        """Construct the sauron service."""
        config = ConfigParser()
        config.read([options['config']])

        channels = [c.strip() for c in config.get('irc', 'channels').split(',') if c.strip()]
        workdir = config.get('sauron', 'workdir')
        self.__prepare_directories(workdir, channels)

        return SauronBotService(
            endpoint=config.get('irc', 'endpoint'),
            channels=channels,
            nickname=config.get('irc', 'nickname'),
            realname=config.get('irc', 'realname'),
            datadir=workdir + "/data",
            logdir=workdir + "/logs"
        )

    def __prepare_directories(self, workdir, channels):
        if not os.path.exists(workdir):
            os.makedirs(workdir)
        logdir = workdir + "/logs"
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        datadir = workdir + "/data"
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        for channel in channels:
            datadir_channel = datadir + "/" + channel
            if not os.path.exists(datadir_channel):
                os.makedirs(datadir_channel)

# Now construct an object which *provides* the relevant interfaces
# The name of this variable is irrelevant, as long as there is *some*
# name bound to a provider of IPlugin and IServiceMaker.

serviceMaker = BotServiceMaker()