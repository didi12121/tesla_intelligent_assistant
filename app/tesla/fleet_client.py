from __future__ import annotations

import aiohttp

from tesla_fleet_api import TeslaFleetApi
from tesla_fleet_api.exceptions import VehicleOffline

from config import TESLA_REGION


class FleetClient:

    async def _create_api(self, access_token: str) -> TeslaFleetApi:
        """Create a TeslaFleetApi instance with EC private key for signed commands."""
        session = aiohttp.ClientSession()
        api = TeslaFleetApi(
            access_token=access_token,
            session=session,
            region="cn",
        )
        # Load EC private key for signed commands (use the key that was paired with the vehicle)
        await api.get_private_key("private-key.pem")
        return api

    async def list_vehicles(self, access_token: str):
        api = await self._create_api(access_token)
        try:
            result = await api.products()
            raw_items = result.get("response", []) if isinstance(result, dict) else []

            vehicles = []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue

                # products 接口里，车辆一般会带这些字段
                if item.get("vehicle_id") is not None or item.get("vin") or item.get("id_s"):
                    vehicles.append({
                        "id": item.get("id"),
                        "id_s": item.get("id_s"),
                        "vehicle_id": item.get("vehicle_id"),
                        "vin": item.get("vin"),
                        "display_name": item.get("display_name"),
                        "state": item.get("state"),
                        "in_service": item.get("in_service"),
                        "calendar_enabled": item.get("calendar_enabled"),
                        "api_version": item.get("api_version"),
                        "raw": item,
                    })

            return {
                "count": len(vehicles),
                "response": vehicles,
                "raw_response": result,
            }
        finally:
            await api.session.close()

    async def wake_up(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.wake_up()
        finally:
            await api.session.close()

    async def flash_lights(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.flash_lights()
        finally:
            await api.session.close()

    async def honk_horn(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.honk_horn()
        finally:
            await api.session.close()

    async def climate_start(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.auto_conditioning_start()
        finally:
            await api.session.close()

    async def climate_stop(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.auto_conditioning_stop()
        finally:
            await api.session.close()

    async def door_lock(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.door_lock()
        finally:
            await api.session.close()

    async def door_unlock(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.door_unlock()
        finally:
            await api.session.close()

    async def charge_start(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.charge_start()
        finally:
            await api.session.close()

    async def charge_stop(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.charge_stop()
        finally:
            await api.session.close()

    async def charge_port_open(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.charge_port_door_open()
        finally:
            await api.session.close()

    async def charge_port_close(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.charge_port_door_close()
        finally:
            await api.session.close()

    async def set_charge_limit(self, access_token: str, vin: str, percent: int):
        if percent < 50 or percent > 100:
            raise ValueError("charge limit percent must be between 50 and 100")
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.set_charge_limit(percent=percent)
        finally:
            await api.session.close()

    async def set_sentry_mode(self, access_token: str, vin: str, on: bool):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.set_sentry_mode(on=on)
        finally:
            await api.session.close()

    async def window_control(self, access_token: str, vin: str, command: str, window: str = "all"):
        if command not in ("vent", "close"):
            raise ValueError("window command must be 'vent' or 'close'")
        if window not in ("all", "front_left", "front_right", "rear_left", "rear_right"):
            raise ValueError("window must be one of: all, front_left, front_right, rear_left, rear_right")

        # Tesla Fleet API currently supports vent/close for windows, but not per-window targeting.
        if window != "all":
            return {
                "response": {
                    "result": False,
                    "reason": "individual_window_not_supported_by_fleet_api",
                },
                "requested_window": window,
                "supported_window_scope": "all",
            }

        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.window_control(command=command)
        finally:
            await api.session.close()

    async def fleet_status(self, access_token: str, vins: list[str]):
        api = await self._create_api(access_token)
        try:
            # fleet_status is a plain REST endpoint, no signing needed
            vehicle = api.vehicles.createFleet(vins[0])
            return await vehicle.fleet_status(vins)
        finally:
            await api.session.close()

    async def actuate_trunk(self, access_token: str, vin: str, which_trunk: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.actuate_trunk(which_trunk)
        finally:
            await api.session.close()

    async def navigate_to(self, access_token: str, vin: str, lat: float, lon: float, name: str):
        api = await self._create_api(access_token)
        try:
            vehicle = api.vehicles.createSigned(vin)
            return await vehicle.navigation_gps_destination_request(
                lat=lat, lon=lon, destination=name, order=0
            )
        finally:
            await api.session.close()

    async def vehicle_status(self, access_token: str, vin: str):
        api = await self._create_api(access_token)
        try:
            from tesla_fleet_api.const import VehicleDataEndpoint
            vehicle = api.vehicles.createFleet(vin)
            try:
                result = await vehicle.vehicle_data([
                    VehicleDataEndpoint.CHARGE_STATE,
                    VehicleDataEndpoint.CLIMATE_STATE,
                    VehicleDataEndpoint.VEHICLE_STATE,
                    VehicleDataEndpoint.CLOSURES_STATE,
                    VehicleDataEndpoint.DRIVE_STATE,
                    VehicleDataEndpoint.LOCATION_DATA,
                ])
            except VehicleOffline:
                return {
                    "state": "offline",
                    "charge": {},
                    "climate": {},
                    "location": {},
                    "vehicle_state": {},
                    "raw": {"error": "VehicleOffline"},
                    "message": "Vehicle is offline. Wake it up first and retry in 10-30 seconds.",
                }
            data = result.get("response", {})
            charge = data.get("charge_state", {})
            climate = data.get("climate_state", {})
            vehicle_state = data.get("vehicle_state", {})
            drive = data.get("drive_state", {})
            return {
                "state": data.get("state"),
                "charge": {
                    "battery_level": charge.get("battery_level"),
                    "battery_range": round(charge.get("battery_range", 0) * 1.60934, 1) if charge.get("battery_range") else None,
                    "charging_state": charge.get("charging_state"),
                    "charge_limit_soc": charge.get("charge_limit_soc"),
                },
                "climate": {
                    "inside_temp": climate.get("inside_temp"),
                    "outside_temp": climate.get("outside_temp"),
                    "driver_temp_setting": climate.get("driver_temp_setting"),
                    "is_climate_on": climate.get("is_climate_on"),
                },
                "location": {
                    "latitude": drive.get("latitude"),
                    "longitude": drive.get("longitude"),
                    "heading": drive.get("heading"),
                    "speed": drive.get("speed"),
                },
                "vehicle_state": {
                    "sentry_mode": vehicle_state.get("sentry_mode"),
                    "locked": vehicle_state.get("locked"),
                    "df": vehicle_state.get("df"),
                    "pf": vehicle_state.get("pf"),
                    "dr": vehicle_state.get("dr"),
                    "pr": vehicle_state.get("pr"),
                    "ft": vehicle_state.get("ft"),
                    "rt": vehicle_state.get("rt"),
                    "car_version": vehicle_state.get("car_version"),
                },
                "raw": data,
            }
        finally:
            await api.session.close()
