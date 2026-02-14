"""Options flow for Body Metrics."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import OptionsFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_PEOPLE,
    CONF_PERSON_AGE,
    CONF_PERSON_EXPECTED_IMPEDANCE,
    CONF_PERSON_EXPECTED_WEIGHT,
    CONF_PERSON_HEIGHT,
    CONF_PERSON_NAME,
    CONF_PERSON_SEX,
    CONF_PERSON_TOLERANCE,
    DEFAULT_TOLERANCE,
    SEX_FEMALE,
    SEX_MALE,
)


class BodyMetricsOptionsFlow(OptionsFlow):
    """Handle Body Metrics options."""

    def __init__(self, config_entry) -> None:
        self._people: list[dict[str, Any]] = list(
            config_entry.options.get(CONF_PEOPLE, [])
        )
        self._edit_index: int | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the options menu."""
        menu_options = ["add_person"]
        if self._people:
            menu_options.extend(["edit_person", "remove_person"])
        menu_options.append("done")

        return self.async_show_menu(step_id="init", menu_options=menu_options)

    async def async_step_add_person(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add a new person."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_PERSON_NAME].strip()
            if any(p[CONF_PERSON_NAME] == name for p in self._people):
                errors[CONF_PERSON_NAME] = "name_exists"
            else:
                user_input[CONF_PERSON_NAME] = name
                self._people.append(user_input)
                return await self.async_step_init()

        return self.async_show_form(
            step_id="add_person",
            data_schema=self._person_schema(),
            errors=errors,
        )

    async def async_step_edit_person(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a person to edit."""
        if not self._people:
            return await self.async_step_init()

        if user_input is not None:
            self._edit_index = int(user_input["person"])
            return await self.async_step_edit_person_form()

        return self.async_show_form(
            step_id="edit_person",
            data_schema=vol.Schema(
                {
                    vol.Required("person"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(
                                    value=str(i), label=p[CONF_PERSON_NAME]
                                )
                                for i, p in enumerate(self._people)
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_edit_person_form(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Edit a person's details."""
        errors: dict[str, str] = {}
        person = self._people[self._edit_index]

        if user_input is not None:
            name = user_input[CONF_PERSON_NAME].strip()
            conflict = any(
                p[CONF_PERSON_NAME] == name
                for i, p in enumerate(self._people)
                if i != self._edit_index
            )
            if conflict:
                errors[CONF_PERSON_NAME] = "name_exists"
            else:
                user_input[CONF_PERSON_NAME] = name
                self._people[self._edit_index] = user_input
                return await self.async_step_init()

        return self.async_show_form(
            step_id="edit_person_form",
            data_schema=self._person_schema(person),
            errors=errors,
        )

    async def async_step_remove_person(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a person to remove."""
        if not self._people:
            return await self.async_step_init()

        if user_input is not None:
            idx = int(user_input["person"])
            self._people.pop(idx)
            return await self.async_step_init()

        return self.async_show_form(
            step_id="remove_person",
            data_schema=vol.Schema(
                {
                    vol.Required("person"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(
                                    value=str(i), label=p[CONF_PERSON_NAME]
                                )
                                for i, p in enumerate(self._people)
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )

    async def async_step_done(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Finish options flow and save."""
        return self.async_create_entry(title="", data={CONF_PEOPLE: self._people})

    def _person_schema(
        self, defaults: dict[str, Any] | None = None
    ) -> vol.Schema:
        """Build the person form schema."""
        d = defaults or {}
        return vol.Schema(
            {
                vol.Required(
                    CONF_PERSON_NAME, default=d.get(CONF_PERSON_NAME, "")
                ): TextSelector(TextSelectorConfig()),
                vol.Required(
                    CONF_PERSON_HEIGHT, default=d.get(CONF_PERSON_HEIGHT, 170)
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=100,
                        max=250,
                        step=1,
                        unit_of_measurement="cm",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PERSON_AGE, default=d.get(CONF_PERSON_AGE, 30)
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=120,
                        step=1,
                        unit_of_measurement="years",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_PERSON_SEX, default=d.get(CONF_PERSON_SEX, SEX_MALE)
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=SEX_MALE, label="Male"),
                            SelectOptionDict(value=SEX_FEMALE, label="Female"),
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_PERSON_EXPECTED_WEIGHT,
                    default=d.get(CONF_PERSON_EXPECTED_WEIGHT, 70.0),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=20,
                        max=300,
                        step=0.1,
                        unit_of_measurement="kg",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_PERSON_EXPECTED_IMPEDANCE,
                    default=d.get(CONF_PERSON_EXPECTED_IMPEDANCE, 500),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=100,
                        max=1500,
                        step=1,
                        unit_of_measurement="\u03a9",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_PERSON_TOLERANCE,
                    default=d.get(CONF_PERSON_TOLERANCE, DEFAULT_TOLERANCE),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=50,
                        step=0.5,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )
