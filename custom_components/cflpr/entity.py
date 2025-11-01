from dataclasses import dataclass
from abc import abstractmethod
from homeassistant.helpers.entity import Entity, EntityDescription
from typing import TypeVar, Generic
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from homeassistant.core import callback
from .model import PRItem
from .const import DOMAIN, MANUFACTURER


@dataclass(kw_only=True)
class CFLPREntityDescription(EntityDescription):
    """"""


T = TypeVar("T")


class CFLPREntity(Generic[T], CoordinatorEntity[T], Entity):
    entity_description: CFLPREntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: T,
        description: CFLPREntityDescription,
        pr: PRItem,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        self.entity_description: CFLPREntityDescription = description
        self._attr_translation_key = description.key
        self._attr_unique_id = pr.id

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, pr.id)},
            manufacturer=MANUFACTURER,
            model=pr.name,
            name=f"{MANUFACTURER} {pr.name}",
        )

        self._coordinator = coordinator
        self._pr = pr

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_state(self._coordinator)
        super()._handle_coordinator_update()

    @abstractmethod
    def _update_state(self, coordinator: T) -> None:
        """Update the state of the entity."""
        raise NotImplementedError
