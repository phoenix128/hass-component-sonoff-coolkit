from collections import OrderedDict

from .coolkit_client.device import CoolkitDeviceSwitch
from .coolkit_client import CoolkitDevicesRepository
from homeassistant.components.switch import SwitchDevice, DOMAIN
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .coolkit_client import CoolkitDevice


async def async_setup_platform(
        hass: HomeAssistant,
        config: OrderedDict,
        async_add_entities,
        discovery_info=None
):
    ha_entities = []

    devices = CoolkitDevicesRepository.get_devices()
    for device in devices.values():
        for i in range(0, len(device.switches)):
            ha_entities.append(SonoffSwitch(device, i))

    async_add_entities(ha_entities, update_before_add=False)


class SonoffSwitch(SwitchDevice):
    _state = True

    def __init__(self, device: 'CoolkitDevice', index: int):
        self._index = index
        self._device = device
        self._switch: CoolkitDeviceSwitch = self._device.switches[self._index]
        self._switch.add_state_callback(
            callback_name='hass',
            callable=self._on_state_change
        )

    async def _on_state_change(
            self,
            switch: CoolkitDeviceSwitch,
            new_state: bool
    ) -> None:
        self._state = new_state
        await self.async_update_ha_state()

    @property
    def entity_id(self) -> str:
        if len(self._device.switches) > 1:
            return DOMAIN + '.sonoff_' + self._device.device_id + '_' + str(self._index + 1)
        else:
            return DOMAIN + '.sonoff_' + self._device.device_id

    @property
    def available(self) -> bool:
        return self._device.is_online

    @property
    def name(self) -> str:
        if len(self._device.switches) > 1:
            return self._device.name + ' ' + str(self._index + 1)
        else:
            return self._device.name

    @property
    def should_poll(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self._switch.get_state()

    @property
    def state(self) -> str:
        """Return the state."""
        return STATE_ON if self.is_on else STATE_OFF

    async def async_turn_on(self, **kwargs) -> None:
        await self._switch.set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._switch.set_state(False)






