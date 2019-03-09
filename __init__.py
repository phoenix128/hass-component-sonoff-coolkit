"""
Add suport for ITEAD devices like SONOFF without firmware flashing
"""
import logging
from collections import OrderedDict

from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery, config_validation
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['websockets', 'deepmerge', 'coolkit-client-phoenix']

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
    from coolkit_client import CoolkitSession
    from coolkit_client.device_control import CoolkitDeviceControl
    from coolkit_client.discover import CoolkitDevicesDiscovery

    res = await CoolkitSession.login(
        config.get(DOMAIN, {}).get(CONF_USERNAME, ''),
        config.get(DOMAIN, {}).get(CONF_PASSWORD, ''),
        config.get(DOMAIN, {}).get(CONF_REGION, '')
    )

    if not res:
        _LOGGER.error("Unable to login to coolikt server, please check your credentials")
        return False

    await CoolkitDevicesDiscovery.discover()
    CoolkitDeviceControl.start_daemon()

    for component in ['switch', 'sensor']:
        await discovery.async_load_platform(hass, component, DOMAIN, {}, config)

    return True
