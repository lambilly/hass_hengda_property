"""Config flow for Hengda Property."""
from __future__ import annotations

import voluptuous as vol
from datetime import datetime
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_UNION_ID,
    CONF_AUTHORIZATION,
    CONF_YEAR,
)

class HengdaPropertyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hengda Property."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # 验证输入
            if not user_input[CONF_UNION_ID] or not user_input[CONF_AUTHORIZATION]:
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(
                    title="恒大物业",
                    data=user_input,
                )

        # 获取当前年份作为默认值
        current_year = datetime.now().year
        
        data_schema = vol.Schema({
            vol.Required(CONF_UNION_ID): str,
            vol.Required(CONF_AUTHORIZATION): str,
            vol.Required(CONF_YEAR, default=current_year): vol.All(vol.Coerce(int), vol.Range(min=2020, max=2030)),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "union_id": "Union ID",
                "authorization": "Authorization Token",
                "year": "数据年份"
            }
        )