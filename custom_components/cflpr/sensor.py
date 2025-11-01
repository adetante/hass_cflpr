from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.const import PERCENTAGE

from .config_flow import CFLPRConfigEntry
from .coordinators import CFLPRFastCoordinator, FastCoordinatorData
from .entity import CFLPREntity, CFLPREntityDescription


_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class CFLPRSensorDescription(SensorEntityDescription, CFLPREntityDescription):
    """"""


_DESCRIPTIONS: tuple[CFLPRSensorDescription, ...] = (
    CFLPRSensorDescription(
        key="filling_rate",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        native_unit_of_measurement=PERCENTAGE,
    ),
)


class CFLPRSensorEntity(CFLPREntity[CFLPRFastCoordinator], SensorEntity):
    def _update_state(self, coordinator: CFLPRFastCoordinator) -> None:
        data: FastCoordinatorData = coordinator.data
        native_value = None
        extra_states = None

        if self._pr.id in data.availability:
            native_value = int(data.availability[self._pr.id].fill_rate)
            extra_states = {
                "free_spaces": data.availability[self._pr.id].free_spaces,
                "free_electric_spaces": data.availability[
                    self._pr.id
                ].free_electric_spaces,
                "free_pmr_spaces": data.availability[self._pr.id].free_pmr_spaces,
            }

        self._attr_native_value = native_value
        self._attr_extra_state_attributes = extra_states


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CFLPRConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    entities: list[CFLPRSensorEntity] = []
    fast_coordinator = entry.runtime_data.fast_coordinator
    for pr in entry.runtime_data.selected_pr:
        for description in _DESCRIPTIONS:
            entities.append(CFLPRSensorEntity(fast_coordinator, description, pr))
    async_add_entities(entities)
