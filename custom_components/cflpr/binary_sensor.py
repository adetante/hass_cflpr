from dataclasses import dataclass
import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from .config_flow import CFLPRConfigEntry
from .coordinators import CFLPRSlowCoordinator
from .entity import CFLPREntity, CFLPREntityDescription


_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class CFLPRBinarySensorDescription(
    BinarySensorEntityDescription, CFLPREntityDescription
):
    """"""


_DESCRIPTIONS: tuple[CFLPRBinarySensorDescription, ...] = (
    CFLPRBinarySensorDescription(
        key="subscription_availability",
    ),
)


class CFLPRBinarySensorEntity(CFLPREntity[CFLPRSlowCoordinator], BinarySensorEntity):
    def _update_state(self, coordinator: CFLPRSlowCoordinator) -> None:
        is_on = None

        if self._pr.id in data.slot_available:
            is_on = data.slot_available[self._pr.id]

        self._attr_is_on = is_on


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CFLPRConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    entities: list[CFLPRBinarySensorEntity] = []
    slow_coordinator = entry.runtime_data.slow_coordinator
    for pr in entry.runtime_data.selected_pr:
        for description in _DESCRIPTIONS:
            entities.append(CFLPRBinarySensorEntity(slow_coordinator, description, pr))
    async_add_entities(entities)
