"""Sensor platform for Hengda Property."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
    CHARGE_TYPES,
    CHARGE_ITEMS,
    PUBLIC_CHARGE_ITEMS
)
from .coordinator import HengdaPropertyCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Hengda Property sensor platform."""
    
    coordinator: HengdaPropertyCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = []
    
    # 为每种费用类型和设备创建传感器
    for charge_type_key, charge_type_name in CHARGE_TYPES.items():
        # 添加常规费用传感器
        for item_key, item_name in CHARGE_ITEMS.items():
            sensors.append(
                HengdaPropertySensor(coordinator, charge_type_key, charge_type_name, item_key, item_name)
            )
        
        # 添加更新时间传感器
        sensors.append(
            HengdaPropertyUpdateTimeSensor(coordinator, charge_type_key, charge_type_name)
        )
        
        # 添加合计传感器
        if charge_type_key == "prepaid":
            sensors.append(
                HengdaPropertyTotalSensor(coordinator, charge_type_key, charge_type_name, "prepaid_total", "预交费用合计")
            )
        elif charge_type_key == "paid":
            sensors.append(
                HengdaPropertyTotalSensor(coordinator, charge_type_key, charge_type_name, "paid_public_total", "月公摊费")
            )
        elif charge_type_key == "pending":
            sensors.append(
                HengdaPropertyTotalSensor(coordinator, charge_type_key, charge_type_name, "pending_total", "待交费用合计")
            )
    
    async_add_entities(sensors, True)


class HengdaPropertySensor(SensorEntity):
    """Representation of a Hengda Property Sensor."""

    def __init__(
        self, 
        coordinator: HengdaPropertyCoordinator, 
        charge_type: str,
        charge_type_name: str,
        item_key: str,
        item_name: str
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._charge_type = charge_type
        self._charge_type_name = charge_type_name
        self._item_key = item_key
        self._item_name = item_name
        
        # 优化实体名称：直接使用费用项目名称，不使用连接符
        self._attr_name = f"{item_name}"
        self._attr_unique_id = f"{DOMAIN}_{charge_type}_{item_key}"
        
        # 设置设备信息
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{DOMAIN}_{charge_type}")},
            name=charge_type_name,
            manufacturer="恒大物业",
            model=charge_type_name,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return 0
            
        data = self.coordinator.data.get(self._charge_type, {})
        item_data = data.get(self._item_key, {})
        
        if self._charge_type == "paid":
            return item_data.get("amount", 0)
        elif self._charge_type == "prepaid":
            return item_data.get("balance", 0)
        elif self._charge_type == "pending":
            return item_data.get("amount", 0)
        
        return 0

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "元"

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return {}
            
        data = self.coordinator.data.get(self._charge_type, {})
        item_data = data.get(self._item_key, {})
        
        if not item_data:
            return {}
            
        if self._charge_type == "paid":
            return {
                "费用类型": "已交费用",
                "年份": item_data.get("year", ""),
                "月份": item_data.get("month", ""),
                "账单日期": item_data.get("date", ""),
                "应缴日期": item_data.get("charge_date", ""),
                "缴费状态": item_data.get("status", "未知")
            }
        elif self._charge_type == "prepaid":
            return {
                "费用类型": "预交费用",
                "客户姓名": item_data.get("customer", "未知"),
                "房产名称": item_data.get("house", "未知"),
                "费用项目": item_data.get("charge_item", "未知项目"),
                "子费用项": item_data.get("sub_charge_item", ""),
                "冻结金额": item_data.get("frozen_amount", 0)
            }
        elif self._charge_type == "pending":
            return {
                "费用类型": "待交费用",
                "客户姓名": item_data.get("customer", "未知"),
                "费用项目": item_data.get("charge_item", "未知项目"),
                "账单日期": item_data.get("date", ""),
                "应缴日期": item_data.get("charge_date", ""),
                "上次读数": item_data.get("last_reading", ""),
                "当前读数": item_data.get("current_reading", "")
            }
        
        return {}

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )


class HengdaPropertyUpdateTimeSensor(SensorEntity):
    """Representation of a Hengda Property Update Time Sensor."""

    def __init__(
        self, 
        coordinator: HengdaPropertyCoordinator, 
        charge_type: str,
        charge_type_name: str
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._charge_type = charge_type
        self._charge_type_name = charge_type_name
        
        self._attr_name = f"更新时间"
        self._attr_unique_id = f"{DOMAIN}_{charge_type}_update_time"
        
        # 设置设备信息
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{DOMAIN}_{charge_type}")},
            name=charge_type_name,
            manufacturer="恒大物业",
            model=charge_type_name,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        # 从coordinator的数据中获取最后更新时间
        last_update_str = self.coordinator.data.get("last_update")
        if last_update_str:
            try:
                # 将ISO格式的时间字符串转换为可读格式
                dt = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                # 如果解析失败，返回原始字符串
                return last_update_str
        
        return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return None

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        # 添加下次预计更新时间
        next_update = None
        last_update_str = self.coordinator.data.get("last_update") if self.coordinator.data else None
        
        if last_update_str:
            try:
                last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                # 使用coordinator的更新间隔来计算下次更新时间
                update_interval = self.coordinator.update_interval
                if update_interval:
                    next_update = last_update + update_interval
                    next_update = next_update.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
            
        return {
            "费用类型": self._charge_type_name,
            "数据年份": self.coordinator.year,
            "下次更新": next_update,
            "更新间隔": str(self.coordinator.update_interval) if self.coordinator.update_interval else "未设置"
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )


class HengdaPropertyTotalSensor(SensorEntity):
    """Representation of a Hengda Property Total Sensor."""

    def __init__(
        self, 
        coordinator: HengdaPropertyCoordinator, 
        charge_type: str,
        charge_type_name: str,
        total_type: str,
        total_name: str
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._charge_type = charge_type
        self._charge_type_name = charge_type_name
        self._total_type = total_type
        self._total_name = total_name
        
        self._attr_name = f"{total_name}"
        self._attr_unique_id = f"{DOMAIN}_{charge_type}_{total_type}"
        
        # 设置设备信息
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{DOMAIN}_{charge_type}")},
            name=charge_type_name,
            manufacturer="恒大物业",
            model=charge_type_name,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return 0
            
        total_data = self.coordinator.data.get("total", {})
        return total_data.get(self._total_type, 0)

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return "元"

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return {}
            
        attributes = {
            "费用类型": self._charge_type_name,
            "年份": self.coordinator.year  # 将"数据年份"改为"年份"
        }
        
        # 为月公摊费添加明细和月份信息
        if self._total_type == "paid_public_total":
            paid_data = self.coordinator.data.get("paid", {})
            
            # 从公摊电费获取月份信息
            public_electricity_data = paid_data.get("public_electricity", {})
            month = public_electricity_data.get("month", "")
            if month:
                attributes["月份"] = month  # 添加月份属性
            
            for item_key in PUBLIC_CHARGE_ITEMS:
                item_name = {
                    "water_fee": "公摊水费",
                    "ladder_light": "梯灯电费",
                    "public_electricity": "公摊电费",
                    "elevator_electricity": "电梯电费",
                    "pump_electricity": "水泵电费"
                }.get(item_key, item_key)
                attributes[item_name] = paid_data.get(item_key, {}).get("amount", 0)
        
        return attributes

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )