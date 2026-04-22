import json
from datetime import datetime
from app.db import get_conn, Database
from typing import Optional


class VehicleRepository:
    def save_or_update_vehicle(self, user_id: int, client_id: str, vehicle: dict):
        conn = get_conn()
        try:
            with conn.cursor() as cursor:
                sql_check = "SELECT id FROM tesla_vehicle WHERE vin = %s LIMIT 1"
                cursor.execute(sql_check, (vehicle.get("vin"),))
                exists = cursor.fetchone()

                raw_json = json.dumps(vehicle, ensure_ascii=False)

                if exists:
                    sql = """
                    UPDATE tesla_vehicle
                    SET user_id = %s,
                        vehicle_id = %s,
                        id_s = %s,
                        display_name = %s,
                        state = %s,
                        in_service = %s,
                        api_version = %s,
                        raw_json = %s,
                        is_active = 1,
                        last_synced_at = %s,
                        updated_at = NOW()
                    WHERE vin = %s
                    """
                    cursor.execute(sql, (
                        user_id,
                        vehicle.get("vehicle_id"),
                        vehicle.get("id_s"),
                        vehicle.get("display_name"),
                        vehicle.get("state"),
                        1 if vehicle.get("in_service") else 0 if vehicle.get("in_service") is not None else None,
                        vehicle.get("api_version"),
                        raw_json,
                        datetime.now(),
                        vehicle.get("vin"),
                    ))
                else:
                    sql = """
                    INSERT INTO tesla_vehicle
                    (user_id, client_id, vin, vehicle_id, id_s, display_name, state, in_service, api_version,
                     raw_json, is_active, last_synced_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
                    """
                    cursor.execute(sql, (
                        user_id,
                        client_id,
                        vehicle.get("vin"),
                        vehicle.get("vehicle_id"),
                        vehicle.get("id_s"),
                        vehicle.get("display_name"),
                        vehicle.get("state"),
                        1 if vehicle.get("in_service") else 0 if vehicle.get("in_service") is not None else None,
                        vehicle.get("api_version"),
                        raw_json,
                        datetime.now(),
                    ))
            conn.commit()
        finally:
            conn.close()

    def get_by_user_id(self, user_id: int) -> list[dict]:
        db = Database()
        return db.fetchall(
            "SELECT * FROM tesla_vehicle WHERE user_id = %s AND is_active = 1",
            (user_id,),
        )

    def get_first_by_user_id(self, user_id: int) -> Optional[dict]:
        db = Database()
        return db.fetchone(
            "SELECT * FROM tesla_vehicle WHERE user_id = %s AND is_active = 1 LIMIT 1",
            (user_id,),
        )

    def get_by_user_id_and_vin(self, user_id: int, vin: str) -> Optional[dict]:
        db = Database()
        return db.fetchone(
            "SELECT * FROM tesla_vehicle WHERE user_id = %s AND vin = %s AND is_active = 1 LIMIT 1",
            (user_id, vin),
        )

    def get_by_vin(self, vin: str) -> Optional[dict]:
        db = Database()
        return db.fetchone(
            "SELECT * FROM tesla_vehicle WHERE vin = %s AND is_active = 1 LIMIT 1",
            (vin,),
        )
