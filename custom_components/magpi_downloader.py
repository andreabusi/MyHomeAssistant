"""
Download automatico dei nuovi numeri di MagPi
"""
import json
import urllib.request
import logging

# The domain of your component. Should be equal to the filename of the component.
DOMAIN = "magpi_downloader"
SERVICE_DOWNLOADER = "downloader"

# Variable for storing configuration parameters
CONFIGURATION_FILE = None
OUTPUT_PATH = None
MAGPI_ISSUES_URL = "https://www.raspberrypi.org/magpi-issues"
MAGPI_FILNAME = "MagPi"

# Configuration keys
KEY_CONFIGURATION = 'config_file'
KEY_OUTPUT = 'output_path'

# Shortcut for the logger
_LOGGER = logging.getLogger(__name__)


def setup(hass, config):
    """Setup components."""
    global CONFIGURATION_FILE, OUTPUT_PATH

    CONFIGURATION_FILE = config[DOMAIN][KEY_CONFIGURATION]
    OUTPUT_PATH = config[DOMAIN][KEY_OUTPUT]

    if CONFIGURATION_FILE is None:
        _LOGGER.error("Configuration file not specified!")
        return False
    
    if OUTPUT_PATH is None:
        _LOGGER.error("Output file not specified!")
        return False


    def download_and_notify(call):
        downloader(hass)

    hass.services.register(DOMAIN, SERVICE_DOWNLOADER, download_and_notify)
    return True


def download_new_issue(issue_number):
    try:
        file_name = create_filename(issue_number)
        file_url = "%s/%s" % (MAGPI_ISSUES_URL, file_name)
        output_path = "%s/%s" % (OUTPUT_PATH, file_name)
        urllib.request.urlretrieve(file_url, output_path)
    except Exception as e:
        return False

    return True


def send_notification(hass, issue_number):
    message = "Il nuovo numero di MagPi (issue #%s) è stato scaricato!" % issue_number
    service_data = { 'message': message }
    hass.services.call('notify', 'home_telegram', service_data, False)


def create_filename(issue_number):
    return "%s%s.pdf" % (MAGPI_FILNAME, issue_number)


def downloader(hass):
    # leggo la configurazione per sapere quale numero devo scaricare
    configuration = json.load(open(CONFIGURATION_FILE))
    issue_number = configuration["next_issue"]
    downloaded = download_new_issue(issue_number)
    if downloaded:
        # aggiorniamo il file di configurazione
        configuration["next_issue"] = issue_number + 1
        with open(CONFIGURATION_FILE, 'w') as outfile:
            json.dump(configuration, outfile)

        # inviamo una notifica Telegram
        send_notification(hass, issue_number)
