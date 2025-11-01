"""The CFL P+R integration."""

from __future__ import annotations
from datetime import timedelta

from attr import dataclass
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_TOKEN
from .config_flow import CFLPRConfigEntry, CFLPRContext
from .model import PRItem
from .const import CONF_PRS
from .coordinators import CFLPRFastCoordinator, CFLPRSlowCoordinator
from cflpr.api import CFLPRAPI, CFLPRAPIAuthException

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

FAST_INTERVAL = 1
SLOW_INTERVAL = 30


async def async_setup_entry(hass: HomeAssistant, entry: CFLPRConfigEntry) -> bool:
    """Set up CFL P+R from a config entry."""

    def token_listener(token: str):
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_TOKEN: token}
        )

    async with CFLPRAPI(entry.data[CONF_TOKEN], token_listener) as api:
        try:
            await api.refresh_tokens()
        except CFLPRAPIAuthException:
            raise ConfigEntryAuthFailed(f"Credentials expired for CFL P+R")

    prs = list(PRItem(conf["id"], conf["name"]) for conf in entry.data[CONF_PRS])

    fast_coordinator = CFLPRFastCoordinator(
        hass,
        entry,
        prs,
        api,
        timedelta(minutes=FAST_INTERVAL),
        "CFL P+R fast interval coordinator",
    )
    slow_coordinator = CFLPRSlowCoordinator(
        hass,
        entry,
        prs,
        api,
        timedelta(minutes=SLOW_INTERVAL),
        "CFL P+R slow interval coordinator",
    )
    entry.runtime_data = CFLPRContext(api, prs, fast_coordinator, slow_coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: CFLPRConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
