"""
Add suport for ITEAD devices like SONOFF without firmware flashing
"""
import asyncio
import logging
from collections import OrderedDict

from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery, config_validation
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

#'coolkit-client-phoenix-ng>=1.0.0'
REQUIREMENTS = ['websockets', 'pycryptodome', 'zeroconf']

DOMAIN = 'sonoff'
CONF_REGION = 'region'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): config_validation.string,
        vol.Required(CONF_PASSWORD): config_validation.string,
        vol.Optional(CONF_REGION, default='eu'): config_validation.string,
    }, extra=vol.ALLOW_EXTRA),
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: OrderedDict):
    from .coolkit_client import CoolkitSession
    from .coolkit_client.discover import CoolkitDevicesDiscovery

    known_devices = config.get('sonoff', {}).get('known_devices')
    if known_devices is None:
        known_devices = {}

    res = await CoolkitSession.login(
        config.get(DOMAIN, {}).get(CONF_USERNAME, ''),
        config.get(DOMAIN, {}).get(CONF_PASSWORD, ''),
        config.get(DOMAIN, {}).get(CONF_REGION, '')
    )

    if not res:
        _LOGGER.error("Unable to login to coolikt server, please check your credentials.")

    await CoolkitDevicesDiscovery.discover(known_devices)
    await asyncio.sleep(2)

    for component in ['switch', 'sensor']:
        await discovery.async_load_platform(hass, component, DOMAIN, {}, config)

    return True
