""" Application entrypoint
"""

from ubuntui.ev import EventLoop
from ubuntui.palette import STYLES
from conjure.ui import ConjureUI
from conjure.juju import Juju
from conjure import async
from conjure import __version__ as VERSION
from conjure.controllers.welcome import WelcomeController
from conjure.controllers.finish import FinishController
from conjure.controllers.deploysummary import DeploySummaryController
from conjure.controllers.deploy import DeployController
from conjure.controllers.cloud import CloudController
from conjure.controllers.newcloud import NewCloudController
from conjure.controllers.jujucontroller import JujuControllerController
from conjure.controllers.bootstrapwait import BootstrapWaitController
from conjure.controllers.lxdsetup import LXDSetupController
from conjure.log import setup_logging
import json
import sys
import argparse
import os
import os.path as path
import uuid


class ApplicationException(Exception):
    """ Error in application
    """


class ApplicationConfig:
    """ Application config encapsulating common attributes
    used throughout the lifetime of the application.
    """
    def __init__(self):
        # Reference to entire UI
        self.ui = None
        # Global config attr
        self.config = None
        # CLI arguments
        self.argv = None
        # List of all known controllers to be rendered
        self.controllers = None
        # Current Juju model
        self.current_model = None
        # Current controller
        self.current_controller = None
        # Global session id
        self.session_id = os.getenv('CONJURE_TEST_SESSION_ID',
                                    str(uuid.uuid4()))
        # Logger
        self.log = None
        # Environment to pass to processing tasks
        self.env = os.environ.copy()


class Application:
    def __init__(self, argv, pkg_config, metadata):
        """ init

        Arguments:
        argv: Options passed in from cli
        pkg_config: path to solution config.json
        metadata: path to solutions metadata.json
        """
        self.app = ApplicationConfig()
        self.app.argv = argv
        self.metadata = metadata
        self.pkg_config = pkg_config
        self.app.ui = ConjureUI()

        with open(self.pkg_config) as json_f:
            config = json.load(json_f)

        with open(self.metadata) as json_f:
            config['metadata_filename'] = path.abspath(self.metadata)
            config['metadata'] = json.load(json_f)

        self.app.config = config

        self.app.controllers = {
            'welcome': WelcomeController(self.app),
            'clouds': CloudController(self.app),
            'newcloud': NewCloudController(self.app),
            'lxdsetup': LXDSetupController(self.app),
            'bootstrapwait': BootstrapWaitController(self.app),
            'deploy': DeployController(self.app),
            'deploysummary': DeploySummaryController(self.app),
            'jujucontroller': JujuControllerController(self.app),
            'finish': FinishController(self.app)
        }

        self.app.log = setup_logging(self.app.config['name'],
                                     self.app.argv.debug)

    def unhandled_input(self, key):
        if key in ['q', 'Q']:
            async.shutdown()
            EventLoop.exit(0)

    def _start(self, *args, **kwargs):
        """ Initially load the welcome screen
        """
        self.app.controllers['welcome'].render()

    def start(self):
        EventLoop.build_loop(self.app.ui, STYLES,
                             unhandled_input=self.unhandled_input)
        EventLoop.set_alarm_in(0.05, self._start)
        EventLoop.run()


def parse_options(argv):
    parser = argparse.ArgumentParser(prog="conjure-up")
    parser.add_argument('spell', help="Specify the Juju solution to "
                        "deploy, e.g. openstack")
    parser.add_argument('-d', '--debug', action='store_true',
                        dest='debug',
                        help='Enable debug logging.')
    parser.add_argument(
        '--version', action='version', version='%(prog)s {}'.format(VERSION))
    return parser.parse_args(argv)


def main():
    opts = parse_options(sys.argv[1:])

    if os.geteuid() == 0:
        print("")
        print("This should _not_ be run as root or with sudo.")
        print("")
        sys.exit(1)

    try:
        docs_url = "https://jujucharms.com/docs/stable/getting-started"
        juju_version = Juju.version()
        if int(juju_version[0]) < 2:
            print(
                "Only Juju v2 and above is supported, "
                "your currently installed version is {}.\n\n"
                "Please refer to {} for help on installing "
                "the correct Juju.".format(juju_version, docs_url))
            sys.exit(1)
    except Exception as e:
        print(e)
        sys.exit(1)

    metadata = path.join('/usr/share', opts.spell, 'metadata.json')
    pkg_config = path.join('/usr/share', opts.spell, 'config.json')

    if not path.exists(pkg_config) and not path.exists(metadata):
        print("Unable to find a Juju solution for {}".format(opts.spell))
        print("")
        yn = input("Would you like to install the solution "
                   "before proceeding? [Y/n] ")
        if "y" in yn or "Y" in yn or not yn:
            os.execl("/usr/share/conjure-up/do-apt-install",
                     "/usr/share/conjure-up/do-apt-install",
                     opts.spell)
        else:
            sys.exit(1)

    app = Application(opts, pkg_config, metadata)
    app.start()
