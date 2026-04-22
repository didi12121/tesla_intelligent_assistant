from __future__ import annotations

import json
from typing import AsyncIterator

from openai import AsyncOpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from app.services.map_service import MapService
from app.services.vehicle_service import VehicleService
from app.repositories.vehicle_repository import VehicleRepository

SYSTEM_PROMPT = """你是 Tesla 车辆智能助手。你可以帮助用户查看车辆状态、控制车辆（锁车、解锁、开关后备箱等）、搜索附近店铺并导航。

当前用户的车辆 VIN: {vin}
当前车辆状态:
{vehicle_status}
{user_location_info}

你可以使用以下工具来操作车辆和搜索附近地点，请根据用户意图调用合适的工具。

**重要：请始终使用中文回答用户。**"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_vehicle_status",
            "description": "获取车辆当前状态，包括续航、位置、温度、哨兵模式等",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lock_doors",
            "description": "锁上车门",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unlock_doors",
            "description": "解锁车门",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wake_up_vehicle",
            "description": "唤醒车辆",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "flash_lights",
            "description": "闪灯",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "honk_horn",
            "description": "鸣笛",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "climate_start",
            "description": "开启空调",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "climate_stop",
            "description": "关闭空调",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "start_charging",
            "description": "开始车辆充电",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_charging",
            "description": "停止车辆充电",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "charge_port_open",
            "description": "打开充电口盖",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "charge_port_close",
            "description": "关闭充电口盖",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_charge_limit",
            "description": "设置充电上限百分比（50-100）",
            "parameters": {
                "type": "object",
                "properties": {
                    "percent": {
                        "type": "integer",
                        "minimum": 50,
                        "maximum": 100,
                        "description": "充电上限百分比",
                    }
                },
                "required": ["percent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_sentry_mode",
            "description": "设置哨兵模式",
            "parameters": {
                "type": "object",
                "properties": {
                    "on": {
                        "type": "boolean",
                        "description": "true=开启, false=关闭",
                    }
                },
                "required": ["on"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "control_window",
            "description": "控制车窗。action 支持 vent/close；window 支持 all/front_left/front_right/rear_left/rear_right",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["vent", "close"],
                        "description": "vent=开窗通风, close=关窗",
                    },
                    "window": {
                        "type": "string",
                        "enum": ["all", "front_left", "front_right", "rear_left", "rear_right"],
                        "description": "要控制的车窗位置",
                    }
                },
                "required": ["action", "window"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "actuate_trunk",
            "description": "打开或关闭后备箱（toggle 操作）",
            "parameters": {
                "type": "object",
                "properties": {
                    "which_trunk": {
                        "type": "string",
                        "enum": ["rear", "front"],
                        "description": "rear=后尾箱, front=前备箱",
                    }
                },
                "required": ["which_trunk"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_nearby",
            "description": "搜索车辆当前位置附近的地点，比如餐厅、充电桩、停车场、加油站、商场等。不传坐标时自动使用车辆当前位置。",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词，比如'充电桩'、'停车场'、'星巴克'、'餐厅'等",
                    },
                    "radius": {
                        "type": "integer",
                        "description": "搜索半径（米），默认 3000，最大 50000",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "搜索中心经度",
                    },
                    "latitude": {
                        "type": "number",
                        "description": "搜索中心纬度",
                    },
                },
                "required": ["keyword", "longitude", "latitude"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "geocode",
            "description": "将经纬度转换为详细地址（逆地理编码）",
            "parameters": {
                "type": "object",
                "properties": {
                    "longitude": {"type": "number", "description": "经度"},
                    "latitude": {"type": "number", "description": "纬度"},
                },
                "required": ["longitude", "latitude"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "navigate_to",
            "description": "设置车辆导航目的地，将指定地点发送到车机导航",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "目的地纬度"},
                    "longitude": {"type": "number", "description": "目的地经度"},
                    "name": {"type": "string", "description": "目的地名称，如'星巴克xxx店'"},
                },
                "required": ["latitude", "longitude", "name"],
            },
        },
    },
]


class AgentService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
        self.vehicle_service = VehicleService()
        self.vehicle_repo = VehicleRepository()
        self.map_service = MapService()

    async def _execute_tool(self, user_id: int, name: str, arguments: dict, user_location: dict | None = None) -> str:
        try:
            if name == "search_nearby":
                lng = arguments.get("longitude")
                lat = arguments.get("latitude")
                # 如果没传坐标，用车辆当前位置
                if lng is None or lat is None:
                    vin = await self._get_vin(user_id)
                    status = await self.vehicle_service.vehicle_status(user_id, vin)
                    loc = (status.get("location") or {})
                    lng = loc.get("longitude")
                    lat = loc.get("latitude")
                if lng is None or lat is None:
                    return json.dumps({"error": "无法获取车辆位置"})
                results = self.map_service.search_nearby(
                    longitude=lng,
                    latitude=lat,
                    keyword=arguments.get("keyword", ""),
                    radius=arguments.get("radius", 3000),
                )
                return json.dumps(results, ensure_ascii=False)

            elif name == "geocode":
                result = self.map_service.regeocode(
                    longitude=arguments["longitude"],
                    latitude=arguments["latitude"],
                )
                return json.dumps(result, ensure_ascii=False)

            # 以下是车辆操作
            vin = await self._get_vin(user_id)
            if name == "get_vehicle_status":
                result = await self.vehicle_service.vehicle_status(user_id, vin)
                return json.dumps(result, ensure_ascii=False)

            elif name == "lock_doors":
                result = await self.vehicle_service.lock_doors(user_id, vin)
            elif name == "unlock_doors":
                result = await self.vehicle_service.unlock_doors(user_id, vin)
            elif name == "wake_up_vehicle":
                result = await self.vehicle_service.wake_up(user_id, vin)
            elif name == "flash_lights":
                result = await self.vehicle_service.flash_lights(user_id, vin)
            elif name == "honk_horn":
                result = await self.vehicle_service.honk_horn(user_id, vin)
            elif name == "climate_start":
                result = await self.vehicle_service.climate_start(user_id, vin)
            elif name == "climate_stop":
                result = await self.vehicle_service.climate_stop(user_id, vin)
            elif name == "start_charging":
                result = await self.vehicle_service.start_charging(user_id, vin)
            elif name == "stop_charging":
                result = await self.vehicle_service.stop_charging(user_id, vin)
            elif name == "charge_port_open":
                result = await self.vehicle_service.charge_port_open(user_id, vin)
            elif name == "charge_port_close":
                result = await self.vehicle_service.charge_port_close(user_id, vin)
            elif name == "set_charge_limit":
                result = await self.vehicle_service.set_charge_limit(
                    user_id, vin, percent=int(arguments.get("percent", 80))
                )
            elif name == "set_sentry_mode":
                result = await self.vehicle_service.set_sentry_mode(
                    user_id, vin, on=bool(arguments.get("on", True))
                )
            elif name == "control_window":
                result = await self.vehicle_service.control_window(
                    user_id,
                    vin,
                    command=arguments.get("action", "vent"),
                    window=arguments.get("window", "all"),
                )
            elif name == "actuate_trunk":
                result = await self.vehicle_service.actuate_trunk(
                    user_id, vin, arguments.get("which_trunk", "rear")
                )
            elif name == "navigate_to":
                result = await self.vehicle_service.navigate_to(
                    user_id, vin,
                    lat=arguments["latitude"],
                    lon=arguments["longitude"],
                    name=arguments["name"],
                )
            else:
                return json.dumps({"error": f"Unknown tool: {name}"})
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def _get_vin(self, user_id: int) -> str:
        vehicle = self.vehicle_repo.get_first_by_user_id(user_id)
        if vehicle:
            return vehicle["vin"]
        result = await self.vehicle_service.list_vehicles(user_id)
        vehicles = result.get("response", [])
        if not vehicles:
            raise Exception("未找到车辆")
        return vehicles[0]["vin"]

    async def chat_stream(
        self, messages: list[dict], vin: str, vehicle_status: dict, user_id: int,
        user_location: dict | None = None, chat_repo=None
    ) -> AsyncIterator[str]:
        """SSE 流式聊天，支持 tool calling 循环。"""
        user_location_info = ""
        if user_location:
            user_location_info = f"用户当前定位: 经度 {user_location['longitude']}, 纬度 {user_location['latitude']}"

        # 保存用户最后一条消息
        if messages and messages[-1].get("role") == "user" and chat_repo:
            chat_repo.save_message(user_id, "user", messages[-1]["content"])

        system_msg = SYSTEM_PROMPT.format(
            vin=vin,
            vehicle_status=json.dumps(vehicle_status, ensure_ascii=False, indent=2),
            user_location_info=user_location_info,
        )

        full_messages = [{"role": "system", "content": system_msg}] + messages

        while True:
            stream = await self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=full_messages,
                tools=TOOLS,
                stream=True,
            )

            assistant_content = ""
            tool_calls = {}

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                # 文本内容
                if delta.content:
                    assistant_content += delta.content
                    yield f"data: {json.dumps({'type': 'content', 'content': delta.content})}\n\n"

                # Tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls:
                            tool_calls[idx] = {
                                "id": tc.id or "",
                                "name": "",
                                "arguments": "",
                            }
                        if tc.function:
                            if tc.function.name:
                                tool_calls[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls[idx]["arguments"] += tc.function.arguments

            # 没有 tool calls，结束
            if not tool_calls:
                # 保存助手回复
                if assistant_content and chat_repo:
                    chat_repo.save_message(user_id, "assistant", assistant_content)
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            # 把 assistant 回复加入消息历史
            assistant_msg = {"role": "assistant", "content": assistant_content or None}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for tc in tool_calls.values()
                ]
            full_messages.append(assistant_msg)

            # 执行 tool calls
            for tc in tool_calls.values():
                yield f"data: {json.dumps({'type': 'tool_call', 'name': tc['name']})}\n\n"
                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                result = await self._execute_tool(user_id, tc["name"], args, user_location)
                full_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": result,
                    }
                )
