import base64
import struct

# --- CONFIGURA QUESTI VALORI ---
DEVICE_ID = "bfc77ffe2caf9ac5a5dmnr"          # Tuya device id della lampada
DP51_SENSOR = "sensor.lampada_sala_localtuya_dp51"   # entita' sensor di Local Tuya che espone il DP 51
POWER_SWITCH = "switch.lampada_sala_localtuya_power"  # entita' switch di Local Tuya che espone il DP 20
# ------------------------------------

DP_RAW = 51       # datapoint con lo stato dei due ring (base64)
DP_POWER = 20     # on/off generale

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


# l'ultimo stato noto deve sopravvivere ai riavvii: e' il fallback quando DP51 non e' leggibile
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


def _last_known():
    # ricostruisce lo stato dagli ultimi valori pubblicati
    d = {}
    for key, entity in STATES.items():
        try:
            v = state.get(entity)
            d[key] = (v == "on") if isinstance(DEFAULTS[key], bool) else int(v)
        except Exception:
            d[key] = DEFAULTS[key]
    # a lampada spenta nessun ring e' acceso, qualunque cosa dica l'ultimo stato
    if state.get(POWER_SWITCH) == "off":
        d["rgb_on"] = False
        d["white_on"] = False
    return d


@state_trigger(DP51_SENSOR)
def xmcosy_on_dp51_change(value=None):
    if value in (None, "unknown", "unavailable", ""):
        return
    try:
        _publish(_decode(value))
    except Exception as e:
        log.warning(f"xmcosy: decode DP51 fallita ({value!r}): {e}")


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
    cur = state.get(DP51_SENSOR)
    try:
        d = _decode(cur)
    except Exception:
        # dopo una riconnessione LocalTuya non rilegge il DP51, che resta unavailable fino al
        # prossimo comando: si riparte dall'ultimo stato noto invece che da valori fissi
        log.warning(f"xmcosy_set: DP51 non leggibile ({cur!r}), uso l'ultimo stato noto")
        d = _last_known()

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

    new = _encode(d)
    localtuya.set_dp(device_id=DEVICE_ID, dp=DP_RAW, value=new)

    # gestione on/off generale: spento solo se entrambi i ring sono spenti
    any_on = d["rgb_on"] or d["white_on"]
    localtuya.set_dp(device_id=DEVICE_ID, dp=DP_POWER, value=any_on)

    # aggiorna subito gli stati (senza aspettare il push)
    _publish(d)
