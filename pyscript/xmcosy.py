import base64
import struct
from datetime import datetime, timezone

# --- CONFIGURA QUESTI VALORI ---
DEVICE_ID = "bfc77ffe2caf9ac5a5dmnr"          # Tuya device id della lampada
DP51_SENSOR = "sensor.lampada_sala_localtuya_dp51"   # entita' sensor di Local Tuya che espone il DP 51
POWER_SWITCH = "switch.lampada_sala_localtuya_power"  # entita' switch di Local Tuya che espone il DP 20
# ------------------------------------

DP_RAW = 51       # datapoint con lo stato dei due ring (base64)
DP_POWER = 20     # on/off generale

SEND_DELAY = 0.3      # s: i comandi che arrivano entro questo intervallo partono come un solo invio
CONFIRM_TIMEOUT = 4   # s: attesa della conferma della lampada prima di ripetere l'invio
SEND_ATTEMPTS = 3

# stati pyscript che espongono i campi decodificati, letti dalle template light
STATES = {
    "rgb_on": "pyscript.xmcosy_rgb_on",
    "white_on": "pyscript.xmcosy_white_on",
    "hue": "pyscript.xmcosy_hue",
    "sat": "pyscript.xmcosy_sat",
    "rgb_bright": "pyscript.xmcosy_rgb_bright",
    "white_bright": "pyscript.xmcosy_white_bright",
    "white_temp": "pyscript.xmcosy_white_temp",
}

# valori usati solo se non esiste ancora nessuno stato noto
DEFAULTS = {"rgb_on": False, "white_on": False, "hue": 240, "sat": 1000,
            "rgb_bright": 1000, "white_bright": 1000, "white_temp": 0}


def _as_state(v):
    return ("on" if v else "off") if isinstance(v, bool) else v


# gli stati pyscript sono lo stato di riferimento dei comandi e devono sopravvivere ai riavvii:
# dopo un riavvio LocalTuya non rilegge il DP51, che resta unavailable fino al prossimo comando
for _key, _entity in STATES.items():
    state.persist(_entity, default_value=_as_state(DEFAULTS[_key]))


def _clamp(v, lo, hi):
    return max(lo, min(hi, int(v)))


def _decode(b64):
    flag, h, s, rgb_v, white_v, white_t = struct.unpack(">6H", base64.b64decode(b64))
    return {
        "rgb_on": bool(flag & 2),     # bit1 = ring RGB
        "white_on": bool(flag & 1),   # bit0 = ring bianco
        "hue": h,                     # 0-360
        "sat": s,                     # 0-1000
        "rgb_bright": rgb_v,          # 0-1000
        "white_bright": white_v,      # 0-1000
        "white_temp": white_t,        # 0=caldo, 1000=freddo
    }


def _encode(d):
    flag = 4 + (2 if d["rgb_on"] else 0) + (1 if d["white_on"] else 0)
    raw = struct.pack(
        ">6H",
        flag,
        _clamp(d["hue"], 0, 360),
        _clamp(d["sat"], 0, 1000),
        _clamp(d["rgb_bright"], 0, 1000),
        _clamp(d["white_bright"], 0, 1000),
        _clamp(d["white_temp"], 0, 1000),
    )
    return base64.b64encode(raw).decode()


def _publish(d):
    for key, entity in STATES.items():
        state.set(entity, _as_state(d[key]))


# (valore, istante) dell'ultimo DP20 inviato
_power_sent = None

# numero dell'ultimo stato pubblicato: un invio superato da uno piu' recente non parte
_send_seq = 0


def _power_off():
    # lo switch si aggiorna solo quando la lampada conferma: fino ad allora vale l'ultimo comando
    # inviato, altrimenti un secondo comando ravvicinato vedrebbe ancora lo stato precedente
    sw = state.get(POWER_SWITCH)
    if _power_sent is not None and _power_sent[1] > sw.last_changed:
        return not _power_sent[0]
    return sw == "off"


def _current():
    # ricostruisce lo stato dagli ultimi valori pubblicati
    d = {}
    for key, entity in STATES.items():
        try:
            v = state.get(entity)
            d[key] = (v == "on") if isinstance(DEFAULTS[key], bool) else int(v)
        except Exception:
            d[key] = DEFAULTS[key]
    # a lampada spenta nessun ring e' acceso, qualunque cosa dica l'ultimo stato
    if _power_off():
        d["rgb_on"] = False
        d["white_on"] = False
    return d


def _sync_from_dp51(value):
    if value in (None, "unknown", "unavailable", ""):
        return
    try:
        _publish(_decode(value))
    except Exception as e:
        log.warning(f"xmcosy: decode DP51 fallita ({value!r}): {e}")


@state_trigger(DP51_SENSOR)
def xmcosy_on_dp51_change(value=None):
    _sync_from_dp51(value)


def _send(seq, d):
    # due coppie DP51/DP20 ravvicinate (light.turn_off sui due ring) la lampada non le regge: spegne
    # i ring ma resta alimentata, o non esegue niente. Si lasciano arrivare i comandi ravvicinati,
    # si invia solo l'ultimo stato e lo si ripete finche' la lampada non lo conferma
    task.sleep(SEND_DELAY)
    if seq != _send_seq:
        return
    any_on = d["rgb_on"] or d["white_on"]
    expected = "on" if any_on else "off"
    for attempt in range(1, SEND_ATTEMPTS + 1):
        localtuya.set_dp(device_id=DEVICE_ID, dp=DP_RAW, value=_encode(d))
        localtuya.set_dp(device_id=DEVICE_ID, dp=DP_POWER, value=any_on)
        # state_hold: lo switch deve restare nello stato atteso, non solo passarci
        res = task.wait_until(state_trigger=f"{POWER_SWITCH} == '{expected}'",
                              state_hold=1, timeout=CONFIRM_TIMEOUT)
        if res["trigger_type"] != "timeout" or seq != _send_seq:
            return
        log.warning(f"xmcosy: la lampada non ha confermato DP20={any_on} "
                    f"(invio {attempt}/{SEND_ATTEMPTS})")


@time_trigger("startup")
def xmcosy_sync_on_startup():
    # dopo un reload di pyscript il DP51 e' gia' leggibile: recupera eventuali cambi arrivati
    # mentre pyscript era fermo (dopo un riavvio di HA e' unavailable e restano gli stati salvati)
    try:
        _sync_from_dp51(state.get(DP51_SENSOR))
    except NameError:
        pass


@service
def xmcosy_set(ring=None, power=None, hue=None, sat=None, brightness=None, color_temp=None):
    """Imposta uno dei due ring preservando lo stato dell'altro.

    ring: 'rgb' oppure 'white'
    power: true/false
    hue: 0-360            (solo rgb)
    sat: 0-1000           (solo rgb)
    brightness: 0-1000
    color_temp: 0-1000    (solo white, 0=caldo 1000=freddo)
    """
    global _power_sent, _send_seq

    # si parte dagli stati pyscript e non dal sensore DP51: quello si aggiorna solo quando la
    # lampada conferma, e un secondo comando ravvicinato (light.turn_off sui due ring, che HA
    # esegue in parallelo) ripartirebbe dal valore vecchio annullando il primo
    d = _current()

    if ring == "rgb":
        if power is not None:
            d["rgb_on"] = bool(power)
        if hue is not None:
            d["hue"] = int(hue)
        if sat is not None:
            d["sat"] = int(sat)
        if brightness is not None:
            d["rgb_bright"] = int(brightness)
    elif ring == "white":
        if power is not None:
            d["white_on"] = bool(power)
        if brightness is not None:
            d["white_bright"] = int(brightness)
        if color_temp is not None:
            d["white_temp"] = int(color_temp)
    else:
        log.warning(f"xmcosy_set: ring non valido {ring!r}")
        return

    # gestione on/off generale: spento solo se entrambi i ring sono spenti
    any_on = d["rgb_on"] or d["white_on"]

    # stato aggiornato subito, senza cedere il controllo: un comando concorrente lo vede gia'
    _publish(d)
    _power_sent = (any_on, datetime.now(timezone.utc))

    _send_seq += 1
    task.create(_send, _send_seq, d)
