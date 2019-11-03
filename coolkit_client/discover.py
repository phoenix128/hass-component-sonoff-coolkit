import asyncio
import re
import socket
from threading import Thread
from typing import Optional

from aiohttp import ClientSession
from zeroconf import ServiceBrowser, Zeroconf

from .devices_repository import CoolkitDevicesRepository
from .device import CoolkitDevice
from .log import Log
from .session import CoolkitSession


class CoolkitDevicesDiscovery:
    @classmethod
    async def discover(cls, known_devices: dict) -> bool:
        devices_endpoint = CoolkitSession.get_api_endpoint_url('api/user/device')

        async with ClientSession(headers=CoolkitSession.get_auth_headers()) as session:
            async with session.get(devices_endpoint) as response:
                data = await response.json()

                if response.status != 200 or ('error' in data and data['error'] != 0):
                    Log.error('Error while trying to retrieve devices list: ' + str(data['error']))
                else:
                    for device_data in data:
                        if not CoolkitDevicesRepository.has_device(device_data['deviceid']):
                            device = CoolkitDevice(device_data)
                            CoolkitDevicesRepository.add_device(device)
                            Log.info('Found cloud device: ' + str(device) + ' -> ' + str(device.api_key))

        cls._map_known_devices(known_devices)
        cls._discover_lan()
        return True

    @classmethod
    def _map_known_devices(cls, known_devices: dict):
        for device_id in known_devices.keys():
            if not CoolkitDevicesRepository.has_device(device_id):
                device_data = {
                    'deviceid': device_id,
                    'devicekey': known_devices[device_id]['api_key'],
                    'brandName': known_devices[device_id]['brand_name'],
                    'name': known_devices[device_id]['name'],
                    'productModel': known_devices[device_id]['product_model'],
                    'online': 1,
                    'extra': {
                        'extra': {
                            'model': known_devices[device_id]['device_model']
                        }
                    },
                    'params': {}
                }

                switches_count = int(known_devices[device_id]['switches'])
                if switches_count == 1:
                    device_data['params']['switch'] = {'switch': 'off', 'outlet': 0}
                elif switches_count > 1:
                    device_data['params']['switches'] = []
                    for i in range(0, switches_count):
                        device_data['params']['switches'].append({'switch': 'off', 'outlet': i})

                device = CoolkitDevice(device_data)
                CoolkitDevicesRepository.add_device(device)

                Log.info('Added local device: ' + str(device) + ' -> ' + str(device.api_key))

    @classmethod
    def _discover_lan(cls) -> bool:
        cls.browser = ServiceBrowser(Zeroconf(), CoolkitDevice.SERVICE_TYPE, listener=cls)
        return True

    @classmethod
    async def _discover_in_background(cls) -> None:
        while True:
            await cls.discover({})
            await asyncio.sleep(60)

    @classmethod
    def _start_daemon(cls) -> None:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(cls._discover_in_background())

    @classmethod
    def start_daemon(cls) -> None:
        worker = Thread(target=cls._start_daemon)
        worker.setDaemon(True)
        worker.start()

    @classmethod
    def get_device_from_service_name(cls, name: str) -> Optional[CoolkitDevice]:
        m = re.search(r'^ewelink_(\w+)', name, re.IGNORECASE)
        if not m:
            return None

        device_id = m.group(1)
        return CoolkitDevicesRepository.get_device(device_id)

    @classmethod
    def add_service(cls, zeroconf: Zeroconf, type: str, name: str) -> None:
        """Add service from service browser"""
        if type != CoolkitDevice.SERVICE_TYPE:
            return

        info = zeroconf.get_service_info(type, name)
        if info is None:
            return

        device_ip = socket.inet_ntoa(info.addresses[0])
        device_port = info.port

        device = cls.get_device_from_service_name(name)

        if device is not None:
            Log.info('Found LAN device ' + str(device) + ' -> ' + str(device_ip))
            device.ip = device_ip
            device.port = device_port

        device.client.start_service_browser(zeroconf, name)
        device.client.update_service(zeroconf, type, name)

    @classmethod
    def remove_service(cls, zeroconf: Zeroconf, type: str, name: str) -> None:
        device = cls.get_device_from_service_name(name)

        if device is not None:
            Log.info('Removed LAN device ' + str(device))
            device.ip = None
            device.port = None
