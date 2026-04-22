from __future__ import annotations

from app.services.auth_service import AuthService
from app.tesla.fleet_client import FleetClient
from app.repositories.vehicle_repository import VehicleRepository

class VehicleService:
    def __init__(self):
        self.vehicle_repository = VehicleRepository()
        self.auth_service = AuthService()
        self.fleet_client = FleetClient()

    async def list_vehicles(self, user_id: int) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        result = await self.fleet_client.list_vehicles(access_token=access_token)

        vehicles = result.get("response", [])
        for vehicle in vehicles:
            self.vehicle_repository.save_or_update_vehicle(user_id, self.auth_service.client_id, vehicle)

        return result

    async def lock_doors(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.door_lock(access_token=access_token, vin=vin)

    async def unlock_doors(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.door_unlock(access_token=access_token, vin=vin)

    async def wake_up(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.wake_up(access_token=access_token, vin=vin)

    async def flash_lights(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.flash_lights(access_token=access_token, vin=vin)

    async def honk_horn(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.honk_horn(access_token=access_token, vin=vin)

    async def climate_start(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.climate_start(access_token=access_token, vin=vin)

    async def climate_stop(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.climate_stop(access_token=access_token, vin=vin)

    async def start_charging(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.charge_start(access_token=access_token, vin=vin)

    async def stop_charging(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.charge_stop(access_token=access_token, vin=vin)

    async def charge_port_open(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.charge_port_open(access_token=access_token, vin=vin)

    async def charge_port_close(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.charge_port_close(access_token=access_token, vin=vin)

    async def set_charge_limit(self, user_id: int, vin: str, percent: int) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.set_charge_limit(access_token=access_token, vin=vin, percent=percent)

    async def set_sentry_mode(self, user_id: int, vin: str, on: bool) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.set_sentry_mode(access_token=access_token, vin=vin, on=on)

    async def control_window(self, user_id: int, vin: str, command: str, window: str = "all") -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.window_control(
            access_token=access_token,
            vin=vin,
            command=command,
            window=window,
        )

    async def check_fleet_status(self, user_id: int, vins: list[str]) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.fleet_status(access_token=access_token, vins=vins)

    async def actuate_trunk(self, user_id: int, vin: str, which_trunk: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.actuate_trunk(access_token=access_token, vin=vin, which_trunk=which_trunk)

    async def navigate_to(self, user_id: int, vin: str, lat: float, lon: float, name: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.navigate_to(access_token=access_token, vin=vin, lat=lat, lon=lon, name=name)

    async def vehicle_status(self, user_id: int, vin: str) -> dict:
        access_token = self.auth_service.ensure_third_party_token(user_id)
        return await self.fleet_client.vehicle_status(access_token=access_token, vin=vin)
