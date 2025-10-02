"""Coordinator for Hengda Property integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
import aiohttp
import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    CONF_UNION_ID,
    CONF_AUTHORIZATION,
    CONF_YEAR,
    API_PAID_BILL,
    API_PRE_CHARGE,
    API_BILL_FROM_ERP,
    DEFAULT_HEADERS,
    CHARGE_ITEMS,
    PUBLIC_CHARGE_ITEMS
)

_LOGGER = logging.getLogger(__name__)

class HengdaPropertyCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Hengda Property data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        
        self.entry = entry
        self.union_id = entry.data[CONF_UNION_ID]
        self.authorization = entry.data[CONF_AUTHORIZATION]
        self.year = entry.data.get(CONF_YEAR, datetime.now().year)
        
        # 记录更新时间
        self.last_update_time = None

    async def _async_update_data(self):
        """Update data via API."""
        try:
            # 记录更新时间
            self.last_update_time = datetime.now()
            
            # 获取三种类型的数据
            paid_data = await self._fetch_paid_bills()
            prepaid_data = await self._fetch_prepaid_charges()
            pending_data = await self._fetch_pending_bills()
            
            # 计算合计数据
            total_data = self._calculate_total_data(paid_data, prepaid_data, pending_data)
            
            return {
                "paid": paid_data,
                "prepaid": prepaid_data,
                "pending": pending_data,
                "total": total_data,
                "last_update": self.last_update_time.isoformat()
            }
            
        except Exception as err:
            raise UpdateFailed(f"更新数据时出错: {err}")

    async def _fetch_paid_bills(self):
        """获取已交物业费数据"""
        try:
            headers = {
                **DEFAULT_HEADERS,
                "authorization": self.authorization,
                "token": self.authorization
            }
            
            # 使用配置的年份
            start_date = f"{self.year}-01-01"
            end_date = f"{self.year}-12-31"
            
            payload = {
                "courtUuid": "fjpthdyjbd20191025750269b2bunscp",
                "userErpId": "1156528",
                "startDate": start_date,
                "endDate": end_date
            }
            
            url = f"{API_PAID_BILL}?unionId={self.union_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        _LOGGER.warning("获取已交物业费API失败: %s", response.status)
                        return self._create_default_paid_data()
                    
                    data = await response.json()
                    return self._process_paid_data(data)
        except Exception as err:
            _LOGGER.error("获取已交物业费数据时出错: %s", err)
            return self._create_default_paid_data()

    async def _fetch_prepaid_charges(self):
        """获取预交物业费数据"""
        try:
            headers = {
                **DEFAULT_HEADERS,
                "authorization": self.authorization,
                "token": self.authorization
            }
            
            # 获取住宅预交费
            house_payload = {
                "courtUuid": "fjpthdyjbd20191025750269b2bunscp",
                "houseUuID": "1217951",
                "houseErpId": "1217951"
            }
            
            house_url = f"{API_PRE_CHARGE}?unionId={self.union_id}"
            
            async with aiohttp.ClientSession() as session:
                # 住宅预交费
                async with session.post(house_url, json=house_payload, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        _LOGGER.warning("获取住宅预交费API失败: %s", response.status)
                        house_data = None
                    else:
                        house_data = await response.json()
                
                # 车位预交费
                parking_payload = {
                    "courtUuid": "fjpthdyjbd20191025750269b2bunscp",
                    "houseUuID": "1569520",
                    "houseErpId": "1569520"
                }
                
                async with session.post(house_url, json=parking_payload, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        _LOGGER.warning("获取车位预交费API失败: %s", response.status)
                        parking_data = None
                    else:
                        parking_data = await response.json()
            
            return self._process_prepaid_data(house_data, parking_data)
        except Exception as err:
            _LOGGER.error("获取预交物业费数据时出错: %s", err)
            return self._create_default_prepaid_data()

    async def _fetch_pending_bills(self):
        """获取待交物业费数据"""
        try:
            headers = {
                **DEFAULT_HEADERS,
                "authorization": self.authorization,
                "token": self.authorization
            }
            
            # 使用配置的年份
            start_time = f"{self.year}-01-01T00:00:00"
            end_time = f"{self.year}-12-31T23:59:00"
            
            payload = {
                "id": "1456921",
                "idType": 2,
                "isAll": 1,
                "startTime": start_time,
                "endTime": end_time,
                "courtUuid": "fjpthdyjbd20191025750269b2bunscp",
                "houseUuid": "fa7db2f5f48d4f7c91463bc2e9837408",
                "houseErpIdList": ["1217951", "1569520"]
            }
            
            url = f"{API_BILL_FROM_ERP}?unionId={self.union_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    if response.status != 200:
                        _LOGGER.warning("获取待交物业费API失败: %s", response.status)
                        return self._create_default_pending_data()
                    
                    data = await response.json()
                    return self._process_pending_data(data)
        except Exception as err:
            _LOGGER.error("获取待交物业费数据时出错: %s", err)
            return self._create_default_pending_data()

    def _calculate_total_data(self, paid_data, prepaid_data, pending_data):
        """计算合计数据"""
        # 预交费用合计
        prepaid_total = sum(
            float(item_data.get("balance", 0)) 
            for item_data in prepaid_data.values()
        )
        
        # 已交月公摊费合计（只包括公摊相关费用）
        paid_public_total = sum(
            float(paid_data.get(item_key, {}).get("amount", 0))
            for item_key in PUBLIC_CHARGE_ITEMS
        )
        
        # 待交费用合计
        pending_total = sum(
            float(item_data.get("amount", 0)) 
            for item_data in pending_data.values()
        )
        
        return {
            "prepaid_total": prepaid_total,
            "paid_public_total": paid_public_total,
            "pending_total": pending_total
        }

    def _create_default_paid_data(self):
        """创建默认的已交费用数据"""
        return {
            "water_fee": self._format_paid_item({}),
            "ladder_light": self._format_paid_item({}),
            "public_electricity": self._format_paid_item({}),
            "elevator_electricity": self._format_paid_item({}),
            "pump_electricity": self._format_paid_item({}),
            "property_fee": self._format_paid_item({}),
            "parking_fee": self._format_paid_item({})
        }

    def _create_default_prepaid_data(self):
        """创建默认的预交费用数据"""
        return {
            "water_fee": self._format_prepaid_item({}),
            "ladder_light": self._format_prepaid_item({}),
            "public_electricity": self._format_prepaid_item({}),
            "elevator_electricity": self._format_prepaid_item({}),
            "pump_electricity": self._format_prepaid_item({}),
            "property_fee": self._format_prepaid_item({}),
            "parking_fee": self._format_prepaid_item({})
        }

    def _create_default_pending_data(self):
        """创建默认的待交费用数据"""
        return {
            "water_fee": self._format_pending_item({}),
            "ladder_light": self._format_pending_item({}),
            "public_electricity": self._format_pending_item({}),
            "elevator_electricity": self._format_pending_item({}),
            "pump_electricity": self._format_pending_item({}),
            "property_fee": self._format_pending_item({}),
            "parking_fee": self._format_pending_item({})
        }

    def _process_paid_data(self, data):
        """处理已交费用数据 - 按照原始流程逻辑处理最近一个月的数据"""
        result = self._create_default_paid_data()
        
        if data and data.get("data"):
            # 按费用类型分组
            grouped_data = {}
            for item in data["data"]:
                charge_type = item.get("chargeItemName", "")
                item_key = self._get_charge_item_key(charge_type)
                if item_key:
                    if item_key not in grouped_data:
                        grouped_data[item_key] = []
                    grouped_data[item_key].append(item)
            
            # 对每个费用类型，处理数据
            for item_key, items in grouped_data.items():
                # 按照原始流程逻辑：获取最近一个月的数据并求和
                latest_month_data = self._get_latest_month_summed_data(items)
                if latest_month_data:
                    result[item_key] = self._format_paid_item(latest_month_data)
        
        return result

    def _get_charge_item_key(self, charge_type):
        """根据费用类型名称获取对应的键"""
        if "公摊水费" in charge_type:
            return "water_fee"
        elif "梯灯公摊电费" in charge_type:
            return "ladder_light"
        elif "公共区域公摊电费" in charge_type:
            return "public_electricity"
        elif "电梯公摊电费" in charge_type:
            return "elevator_electricity"
        elif "水泵公摊电费" in charge_type:
            return "pump_electricity"
        elif "住宅物业服务费" in charge_type:
            return "property_fee"
        elif "车位服务费" in charge_type:
            return "parking_fee"
        return None

    def _get_latest_month_summed_data(self, items):
        """获取最近一个月的数据并求和 - 按照原始流程逻辑"""
        if not items:
            return None
            
        # 首先按日期排序，找到最近的日期
        # 使用日期字符串进行排序，处理各种日期格式
        def get_date_key(item):
            bill_date = item.get("billDate", "")
            # 处理不同的日期格式
            if "-" in bill_date:  # 格式如 "20251001-20251031"
                # 取开始日期部分
                date_part = bill_date.split("-")[0]
                return int(date_part) if date_part.isdigit() else 0
            else:  # 格式如 "202509" 或其他
                return int(bill_date) if bill_date.isdigit() else 0
        
        sorted_items = sorted(items, key=get_date_key, reverse=True)
        
        if not sorted_items:
            return None
            
        # 获取最近一个月的日期
        latest_date_key = get_date_key(sorted_items[0])
        if latest_date_key == 0:
            return sorted_items[0]
            
        # 找到相同日期的所有项目
        same_date_items = [item for item in sorted_items 
                          if get_date_key(item) == latest_date_key]
        
        if not same_date_items:
            return sorted_items[0]
            
        # 如果同一个月有多个项目，求和金额
        total_amount = sum(float(item.get("billAmount", 0)) for item in same_date_items)
        
        # 创建合并后的数据项，使用第一个项目的信息，但金额为总和
        merged_item = same_date_items[0].copy()
        merged_item["billAmount"] = total_amount
        
        # 提取年份和月份
        bill_date = merged_item.get("billDate", "")
        if "-" in bill_date:  # 格式如 "20251001-20251031"
            date_part = bill_date.split("-")[0]
            if len(date_part) >= 6:
                merged_item["billYear"] = date_part[:4]
                merged_item["billMonth"] = date_part[4:6]
        elif len(bill_date) >= 6:  # 格式如 "202509"
            merged_item["billYear"] = bill_date[:4]
            merged_item["billMonth"] = bill_date[4:6]
        
        return merged_item

    def _format_paid_item(self, item):
        """格式化已交费用项"""
        return {
            "amount": float(item.get("billAmount", 0)),
            "year": item.get("billYear", ""),
            "month": item.get("billMonth", ""),
            "date": item.get("billDate", ""),
            "charge_date": item.get("shouldChargeDate", ""),
            "status": item.get("chargeStatus", "未知")
        }

    def _process_prepaid_data(self, house_data, parking_data):
        """处理预交费用数据"""
        result = self._create_default_prepaid_data()
        
        # 处理住宅预交费
        if house_data and house_data.get("data", {}).get("preChargeList"):
            for item in house_data["data"]["preChargeList"]:
                charge_type = item.get("chargeItemName", "")
                if "梯灯公摊电费" in charge_type:
                    result["ladder_light"] = self._format_prepaid_item(item)
                elif "电梯公摊电费" in charge_type:
                    result["elevator_electricity"] = self._format_prepaid_item(item)
                elif "公共区域公摊电费" in charge_type:
                    result["public_electricity"] = self._format_prepaid_item(item)
                elif "公摊水费" in charge_type:
                    result["water_fee"] = self._format_prepaid_item(item)
                elif "水泵公摊电费" in charge_type:
                    result["pump_electricity"] = self._format_prepaid_item(item)
                elif "住宅物业服务费" in charge_type:
                    result["property_fee"] = self._format_prepaid_item(item)
        
        # 处理车位预交费
        if (parking_data and parking_data.get("data", {}).get("preChargeList") and 
            len(parking_data["data"]["preChargeList"]) >= 3):
            parking_item = parking_data["data"]["preChargeList"][2]  # 第三个是车位费
            result["parking_fee"] = self._format_prepaid_item(parking_item)
            
        return result

    def _format_prepaid_item(self, item):
        """格式化预交费用项"""
        return {
            "balance": float(item.get("balance", 0)),
            "customer": item.get("customerName", "未知"),
            "house": item.get("houseName", "未知"),
            "charge_item": item.get("chargeItemName", "未知项目"),
            "sub_charge_item": item.get("subChargeItemName", ""),
            "frozen_amount": float(item.get("frozenHanSum", 0))
        }

    def _process_pending_data(self, data):
        """处理待交费用数据"""
        result = self._create_default_pending_data()
        
        if data and data.get("data", {}).get("erpBillList"):
            for item in data["data"]["erpBillList"]:
                charge_type = item.get("chargeItemName", "")
                if "住宅物业服务费" in charge_type:
                    result["property_fee"] = self._format_pending_item(item)
                elif "水泵公摊电费" in charge_type:
                    result["pump_electricity"] = self._format_pending_item(item)
                elif "区域公摊电费" in charge_type:
                    result["public_electricity"] = self._format_pending_item(item)
                elif "公摊水费" in charge_type:
                    result["water_fee"] = self._format_pending_item(item)
                elif "电梯公摊电费" in charge_type:
                    result["elevator_electricity"] = self._format_pending_item(item)
                elif "梯灯公摊电费" in charge_type:
                    result["ladder_light"] = self._format_pending_item(item)
        return result

    def _format_pending_item(self, item):
        """格式化待交费用项"""
        return {
            "amount": float(item.get("billAmount", 0)),
            "customer": item.get("customerName", "未知"),
            "charge_item": item.get("chargeItemName", "未知项目"),
            "date": item.get("billDate", ""),
            "charge_date": item.get("shouldChargeDate", ""),
            "last_reading": item.get("lastReadDegree", ""),
            "current_reading": item.get("currentReadDegree", "")
        }