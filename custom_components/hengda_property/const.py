"""Constants for Hengda Property integration."""

DOMAIN = "hengda_property"
DEFAULT_NAME = "恒大物业"
DEFAULT_SCAN_INTERVAL = 86400  # 24小时更新一次

CONF_UNION_ID = "union_id"
CONF_AUTHORIZATION = "authorization"
CONF_YEAR = "year"  # 新增年份配置

# API URLs
API_PAID_BILL = "https://h5.hengdayun.com/api/payment/queryPaidBillRecord"
API_PRE_CHARGE = "https://h5.hengdayun.com/api/payment/mapPreCharge" 
API_BILL_FROM_ERP = "https://h5.hengdayun.com/api/payment/mapBillFromErp"

# Headers
DEFAULT_HEADERS = {
    "traceid": "340001171841441898602020000001A14E4F39246B95562768AD0CC9C79D57",
    "fronttype": "egc-mobile-ui"
}

# 费用类型
CHARGE_TYPES = {
    "paid": "已交物业费",
    "prepaid": "预交物业费", 
    "pending": "待交物业费"
}

# 具体费用项目
CHARGE_ITEMS = {
    "water_fee": "公摊水费",
    "ladder_light": "梯灯电费",
    "public_electricity": "公摊电费",
    "elevator_electricity": "电梯电费",
    "pump_electricity": "水泵电费",
    "property_fee": "住宅物业费",
    "parking_fee": "车位服务费"
}

# 公摊费用项目（用于月公摊费计算）
PUBLIC_CHARGE_ITEMS = [
    "water_fee",        # 公摊水费
    "ladder_light",     # 梯灯电费  
    "public_electricity", # 公摊电费
    "elevator_electricity", # 电梯电费
    "pump_electricity"  # 水泵电费

]
