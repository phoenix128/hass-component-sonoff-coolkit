"""Component switch"""
import asyncio

from ..log import Log
from typing import TYPE_CHECKING, Callable, Dict, Awaitable

if TYPE_CHECKING:
    from .device import CoolkitDevice


class CoolkitDeviceSwitch:
    _state_change_lock: asyncio.Lock = asyncio.Lock()
    _state: bool = False

    def __init__(self, device: 'CoolkitDevice', index: int):
        self._index = index
        self._device = device
        self._callbacks: Dict[str, Callable[['CoolkitDeviceSwitch', bool], Awaitable[None]]] = {}

    def get_state(self) -> bool:
        return self._state

    async def update_state(self, new_state: bool) -> None:
        if new_state != self._state:
            self._state = new_state
            for callback in self._callbacks.values():
                await callback(self, new_state)

    def add_state_callback(
            self,
            callback_name: str,
            callable: Callable[['CoolkitDeviceSwitch', bool], Awaitable[None]]
    ) -> None:
        self._callbacks[callback_name] = callable

    def remove_callback(self, callback_name: str) -> None:
        if callback_name in self._callbacks:
            del self._callbacks[callback_name]

    async def set_state(self, state: bool) -> None:
        # A lock is required to avoid state inconsistencies on multi outlet devices
        async with self._state_change_lock:
            if state != self.get_state():
                state_name = 'on' if state else 'off'

                if self._device.is_multi_switch_device:
                    new_params = {
                        'switches': self._device.params['switches']
                    }
                    new_params['switches'][self._index]['switch'] = state_name
                else:
                    new_params = {
                        'switch': state_name
                    }

                Log.info('Sending ' + str(self._device) + ' state[' + str(self._index) + '] = ' + state_name)

                if await self._device.client.send_switch_command(new_params):
                    await self.update_state(state)
