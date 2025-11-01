"""Config flow for the CFL P+R integration."""

from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass
import logging
from typing import Any

from .model import PRItem
import voluptuous as vol

from aiohttp.client_exceptions import ClientResponseError
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    SOURCE_REAUTH,
)
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL, CONF_TOKEN, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .coordinators import CFLPRFastCoordinator, CFLPRSlowCoordinator
from .const import DOMAIN, CONF_PRS
from cflpr.api import CFLPRAPI
from cflpr.models import PR


@dataclass
class CFLPRContext:
    api: CFLPRAPI
    selected_pr: list[PRItem]
    fast_coordinator: CFLPRFastCoordinator
    slow_coordinator: CFLPRSlowCoordinator


type CFLPRConfigEntry = ConfigEntry[CFLPRContext]


_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_auth(data: dict[str, Any]) -> str:
    refresh_token = None

    def token_listener(token: str):
        refresh_token = token

    async with CFLPRAPI(None, token_listener) as api:
        await api.authenticate(data[CONF_EMAIL], data[CONF_PASSWORD])

    return str(refresh_token)


class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CFL P+R."""

    VERSION = 1

    def __init__(self) -> None:
        super().__init__()
        self._all_prs: list[PR] = []
        self._config_data: dict[str, str] = {}
        self._user_email: str

    async def async_step_reauth(self, _: Mapping[str, Any]) -> ConfigFlowResult:
        """Perform reauth upon an API authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                description_placeholders={CONF_NAME: self._get_reauth_entry().title},
            )
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                refresh_token = await validate_auth(user_input)
            except ClientResponseError as e:
                if e.status == 401:
                    errors["base"] = "invalid_auth"
                else:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if self.source == SOURCE_REAUTH:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(),
                        data_updates={CONF_TOKEN: refresh_token},
                        reload_even_if_entry_is_unchanged=False,
                    )
                self._user_email = user_input[CONF_EMAIL]
                self._config_data[CONF_TOKEN] = refresh_token
                self._all_prs = await CFLPRAPI(refresh_token).get_all_pr()
                _LOGGER.debug(self._all_prs)
                return await self.async_step_prs()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_prs(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            prs = [
                {"id": pr.id, "name": pr.name}
                for pr in self._all_prs
                if (pr.id in user_input["prs"])
            ]
            self._config_data[CONF_PRS] = prs
            await self.async_set_unique_id(self._user_email)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="CFL P+R", data=self._config_data)

        schema = vol.Schema(
            {
                vol.Required(CONF_PRS): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(
                                value=pr.id,
                                label=pr.name,
                            )
                            for pr in self._all_prs
                        ],
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                    )
                ),
            },
        )

        return self.async_show_form(step_id="prs", data_schema=schema, errors=errors)
