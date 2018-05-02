"""
Calendario della raccolta differenziata
"""
import json
import time
import logging

# The domain of your component. Should be equal to the filename of the component.
DOMAIN = "home_recycling"
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
        title = "Spazzatura"
        message = None

        tomorrow = time.localtime(time.time() + 24*3600)
        collections = get_waste_collection(tomorrow)
        if len(collections) == 0:
            message = "Oggi niente spazzatura da uscire!"
        else:
            message = "Spazzatura in ritiro domani:"
            for collection in collections:
                message += "\n ❗️" + collection
        
        service_data = { 'message': message }
        hass.services.call('notify', 'home_telegram', service_data, False)
    
    hass.services.register(DOMAIN, SERVICE_NOTIFICATION, notification)

    # Servizio di salvataggio della raccolta del giorno dopo
    def set_collections_state(call):
        # remove previous state
        all_collections = get_all_collections()
        for collection in all_collections:
            hass.states.remove(DOMAIN + "." + collection)

        # check for tomorrow waste collections
        tomorrow = time.localtime(time.time() + 24*3600)
        collections = get_waste_collection(tomorrow)
        for collection in collections:
            hass.states.set(DOMAIN + "." + collection, "yes")

        if len(collections) == 0:
            hass.states.set(DOMAIN + ".empty", "yes")
        else:
            hass.states.set(DOMAIN + ".empty", "no")

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
