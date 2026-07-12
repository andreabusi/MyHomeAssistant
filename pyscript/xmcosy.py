import base64
import struct

# --- CONFIGURA QUESTI DUE VALORI ---
DEVICE_ID = "bfc77ffe2caf9ac5a5dmnr"          # Tuya device id della lampada
DP51_SENSOR = "sensor.lampada_sala_localtuya_dp51"   # entita' sensor di Local Tuya che espone il DP 51
# ------------------------------------

DP_RAW = 51       # datapoint con lo stato dei due ring (base64)
DP_POWER = 20     # on/off generale


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
    # espone i campi decodificati come stati pyscript, letti dalle template light
    state.set("pyscript.xmcosy_rgb_on", "on" if d["rgb_on"] else "off")
    state.set("pyscript.xmcosy_white_on", "on" if d["white_on"] else "off")
    state.set("pyscript.xmcosy_hue", d["hue"])
    state.set("pyscript.xmcosy_sat", d["sat"])
    state.set("pyscript.xmcosy_rgb_bright", d["rgb_bright"])
    state.set("pyscript.xmcosy_white_bright", d["white_bright"])
    state.set("pyscript.xmcosy_white_temp", d["white_temp"])


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
        # fallback se non abbiamo ancora ricevuto un valore valido
        d = {"rgb_on": False, "white_on": False, "hue": 0, "sat": 1000,
             "rgb_bright": 1000, "white_bright": 1000, "white_temp": 0}

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
