import enum


class DeviceTechnologyType(str, enum.Enum):
    solar_pv = "solar_pv"
    wind_turbine = "wind_turbine"
    hydro = "hydro"
    battery_storage = "battery_storage"
    ev_charger = "ev_charger"
    chp = "chp"
    other = "other"
