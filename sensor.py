from collections import OrderedDict

from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant

SONOFF_SENSORS_MAP = {
    'power': {'eid': 'power', 'uom': 'W', 'icon': 'mdi:flash-outline'},
    'current': {'eid': 'current', 'uom': 'A', 'icon': 'mdi:current-ac'},
    'voltage': {'eid': 'voltage', 'uom': 'V', 'icon': 'mdi:power-plug'},
    'currentHumidity': {'eid': 'humidity', 'uom': '%', 'icon': 'mdi:water-percent'},
    'currentTemperature': {'eid': 'temperature', 'uom': TEMP_CELSIUS, 'icon': 'mdi:thermometer'},
}


async def async_setup_platform(
        hass: HomeAssistant,
        config: OrderedDict,
        async_add_entities,
        discovery_info=None
):
    return True
