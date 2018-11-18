"""
Calendario della raccolta differenziata
"""
import json
import time
import logging
import homeassistant.components.group as group

# The domain of your component. Should be equal to the filename of the component.
DOMAIN = "home_recycling"
SENSOR_PREFIX = "binary_sensor." + DOMAIN + "_"
SERVICE_NOTIFICATION = "notification"
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
    #if not validate_config(config, {DOMAIN: [CONF_CALENDAR]}, _LOGGER):
    #    return False

    CALENDAR = config[DOMAIN][CONF_CALENDAR]

    # ToDo: check file exists
    if CALENDAR is None:
        _LOGGER.error("Calendar file does not exist")

        # Tell the bootstrapper that we failed to initialize and clear the
        # stored target id so our functions don't run.
        CALENDAR = None
        return False

    # Servizio di notifica per la raccolta del giorno dopo
    def notification(call):
        message = None

        tomorrow = time.localtime(time.time() + 24*3600)
        collections = get_waste_collection(tomorrow)
        if len(collections) == 0:
            message = "Oggi niente spazzatura da uscire!"
        else:
            message = "Spazzatura in ritiro domani:"
            for collection in collections:
                icon = get_icon_for_collection(collection)
                message += "\n%s %s️" % (icon, collection)
        
        service_data = { 'message': message }
        hass.services.call('notify', 'home_telegram', service_data, False)
    
    hass.services.register(DOMAIN, SERVICE_NOTIFICATION, notification)

    # Servizio di salvataggio degli stati della raccolta di domani
    def set_collections_state(call):
        # remove previous state
        all_collections = get_all_collections()
        for collection in all_collections:
            hass.states.remove(DOMAIN + "." + collection)

        # check for tomorrow waste collections
        tomorrow = time.localtime(time.time() + 24*3600)
        collections = get_waste_collection(tomorrow)
        binary_sensors = []
        for collection in collections:
            hass.states.set(DOMAIN + "." + collection, "yes", attributes = { "hidden": True })
            binary_sensors.append(SENSOR_PREFIX + collection)

        create_group(hass, binary_sensors)

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


def create_group(hass, entitiy_ids):
    if len(entitiy_ids) == 0:
        entitiy_ids.append(SENSOR_PREFIX + "empty")
    group.set_group(hass, 'home_recycling_group', name='Raccolta differenziata', entity_ids=entitiy_ids)


def get_icon_for_collection(collection):
    switcher = {
        "secco" : "🗑",
        "organico" : "🦴",
        "plastica" : "💈",
        "barattolame" : "🥫",
        "carta" : "📃"
    }
    return switcher[collection]