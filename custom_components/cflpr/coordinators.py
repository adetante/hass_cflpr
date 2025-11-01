from dataclasses import dataclass
from .config_flow import PRItem
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
import logging
from datetime import timedelta
from .model import PRAvailability

from cflpr.api import CFLPRAPI

_LOGGER = logging.getLogger(__name__)


@dataclass
class FastCoordinatorData:
    availability: dict[str, int]


@dataclass
class SlowCoordinatorData:
    slot_available: dict[str, bool]


class CFLPRFastCoordinator(DataUpdateCoordinator[FastCoordinatorData]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry,
        prs: list[PRItem],
        api: CFLPRAPI,
        update_interval: timedelta,
        name: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=name,
            update_interval=update_interval,
        )
        self._api = api
        self._prs = prs

    async def _async_update_data(self) -> FastCoordinatorData:
        data = {}
        for pr in self._prs:
            pr_availability = await self._api.get_pr(pr.id)
            data[pr.id] = PRAvailability(
                pr_availability.occupiedTotalSpaces / pr_availability.totalSpaces * 100,
                pr_availability.totalSpaces - pr_availability.occupiedTotalSpaces,
                pr_availability.totalElectricalSpaces
                - pr_availability.occupiedElectricalSpaces,
                pr_availability.totalPmrSpaces - pr_availability.occupiedPmrSpaces,
            )
        return FastCoordinatorData(data)


class CFLPRSlowCoordinator(DataUpdateCoordinator[SlowCoordinatorData]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry,
        prs: list[PRItem],
        api: CFLPRAPI,
        update_interval: timedelta,
        name: str,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=name,
            update_interval=update_interval,
        )
        self._api = api
        self._prs = prs

    async def _async_update_data(self) -> SlowCoordinatorData:
        data = {}
        for pr in self._prs:
            nb_slots = await self._api.get_subscription_available_spots(pr.id)
            data[pr.id] = nb_slots > 0
        return SlowCoordinatorData(data)
