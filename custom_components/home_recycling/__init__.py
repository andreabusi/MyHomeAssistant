"""
Calendario della raccolta differenziata
"""
import json
import time
import logging

# The domain of your component. Should be equal to the filename of the component.
DOMAIN = "home_recycling"
SERVICE_COLLECTION = "collections_state"

# Configuration keys
CONF_CALENDAR = 'calendar'

# Variable for storing configuration parameters.
CALENDAR = None

# Shortcut for the logger
_LOGGER = logging.getLogger(__name__)

def setup(hass, config):
    """Setup components."""
    global CALENDAR

    # Validate that all required config options are given.
    CALENDAR = config[DOMAIN][CONF_CALENDAR]

    # check if file exists
    if CALENDAR is None:
        _LOGGER.error("Calendar file does not exist")

        # Tell the bootstrapper that we failed to initialize and clear the
        # stored target id so our functions don't run.
        CALENDAR = None
        return False


    # Servizio di salvataggio degli stati della raccolta di domani
    def set_collections_state(call):
        # check for tomorrow waste collections
        state = "off"
        pickup_date = time.localtime(time.time() + 24*3600)
        collections = get_waste_collection(pickup_date)
        collection_icons = []

        if len(collections) > 0:
            state = "on"
            for collection in collections:
                icon = get_icon_for_collection(collection)
                collection_icons.append("%s %s️" % (icon, collection))

        SENSOR_NAME = "sensor." + DOMAIN
        attributes = { "collections": collections, "collections_icons": collection_icons, "pickup_date": time.strftime("%d-%m-%Y", pickup_date) }
        hass.states.set(SENSOR_NAME, state, attributes)

    hass.services.register(DOMAIN, SERVICE_COLLECTION, set_collections_state)

    # Return boolean to indicate that initialization was successfully.
    return True


def get_waste_collection(date):
    month = time.strftime("%m", date) 
    day = time.strftime("%d", date)

    json_calendar = json.load(open(CALENDAR))
    todayRaccolte = []

    for raccolta in json_calendar.keys():
        raccoltaCalendario = json_calendar[raccolta]
        raccoltaMese = raccoltaCalendario[int(month) - 1]
        raccoltaGiorni = raccoltaMese["" + month]
        if day in raccoltaGiorni:
            todayRaccolte.append(raccolta)

    return todayRaccolte


def get_all_collections():
    json_calendar = json.load(open(CALENDAR))
    return json_calendar.keys()


def get_icon_for_collection(collection):
    switcher = {
        "secco" : "🗑",
        "organico" : "🦴",
        "plastica" : "💈",
        "barattolame" : "🥫",
        "carta" : "📃",
        "vetro" : "🍾"
    }
    return switcher[collection]