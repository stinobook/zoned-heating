"""Config flow for the Zoned Heating component."""
import secrets
import logging
import voluptuous as vol
from copy import deepcopy

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import (
    ATTR_MIN_TEMP,
    ATTR_MAX_TEMP
)
from homeassistant.components.climate.const import HVACMode
from homeassistant.const import Platform
from homeassistant.const import ATTR_TEMPERATURE
from . import const

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=const.DOMAIN):
    """Config flow for Zoned Heating."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""

        _LOGGER.debug("async_step_user")

        # Only a single instance of the integration
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        id = secrets.token_hex(6)

        await self.async_set_unique_id(id)
        self._abort_if_unique_id_configured(updates=user_input)

        return self.async_create_entry(title=const.NAME, data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Zoned Heating."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""

        self.options = deepcopy(dict(config_entry.options))
        self.controller = None
        self.zones = None
        self.max_setpoint = None
        self.controller_delay_time = None
        self.use_fixed_idle_controller_state = None
        self.fixed_idle_controller_mode = None
        self.fixed_idle_controller_temperature = None

    async def async_step_init(self, user_input=None):
        """Handle options flow."""

        if user_input is not None:
            self.controller = user_input.get(const.CONF_CONTROLLER)
            if not self.controller.startswith(Platform.CLIMATE):
                self.use_fixed_idle_controller_state = False
                self.fixed_idle_controller_mode = None
                self.fixed_idle_controller_temperature = None
                return await self.async_step_zones()
            return await self.async_step_controller_idle_state()

        all_climates = [
            climate
            for climate in self.hass.states.async_entity_ids("climate")
        ]
        all_switches = [
            switch
            for switch in self.hass.states.async_entity_ids("switch")
        ]
        controller_options = sorted(all_climates) + sorted(all_switches)

        default = self.options.get(const.CONF_CONTROLLER)
        if default not in controller_options:
            default = None

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_CONTROLLER,
                        default=default
                    ): vol.In(controller_options)
                }
            )
        )

    async def async_step_controller_idle_state(self, user_input=None):
        """Handle controller idle state strategy option."""

        if user_input is not None:
            self.use_fixed_idle_controller_state = user_input.get(
                const.CONF_USE_FIXED_IDLE_CONTROLLER_STATE
            )
            if not self.controller.startswith(Platform.CLIMATE):
                self.use_fixed_idle_controller_state = False
            if self.use_fixed_idle_controller_state and self.controller.startswith(Platform.CLIMATE):
                return await self.async_step_fixed_idle_controller_state()

            self.fixed_idle_controller_mode = None
            self.fixed_idle_controller_temperature = None
            return await self.async_step_zones()

        default = self.options.get(
            const.CONF_USE_FIXED_IDLE_CONTROLLER_STATE,
            const.DEFAULT_USE_FIXED_IDLE_CONTROLLER_STATE,
        )
        if not self.controller.startswith(Platform.CLIMATE):
            default = False

        schema = {
            vol.Required(
                const.CONF_USE_FIXED_IDLE_CONTROLLER_STATE,
                default=default,
            ): bool
        }

        return self.async_show_form(
            step_id="controller_idle_state",
            data_schema=vol.Schema(schema),
        )

    async def async_step_fixed_idle_controller_state(self, user_input=None):
        """Handle fixed controller idle mode and temperature options."""

        controller_state = self.hass.states.get(self.controller)
        if controller_state is None:
            return await self.async_step_zones()

        min_temp = 0
        max_temp = 100
        if self.controller.startswith(Platform.CLIMATE):
            min_temp_attr = controller_state.attributes.get(ATTR_MIN_TEMP)
            max_temp_attr = controller_state.attributes.get(ATTR_MAX_TEMP)
            if isinstance(min_temp_attr, (int, float)):
                min_temp = round(min_temp_attr)
            if isinstance(max_temp_attr, (int, float)):
                max_temp = round(max_temp_attr)

        supported_modes = controller_state.attributes.get("hvac_modes", [])
        mode_options = [
            mode
            for mode in supported_modes
            if mode != HVACMode.OFF
        ]
        if not mode_options:
            mode_options = [controller_state.state]

        if user_input is not None:
            self.fixed_idle_controller_mode = user_input.get(
                const.CONF_FIXED_IDLE_CONTROLLER_MODE
            )
            self.fixed_idle_controller_temperature = user_input.get(
                const.CONF_FIXED_IDLE_CONTROLLER_TEMPERATURE
            )
            return await self.async_step_zones()

        default_mode = self.options.get(const.CONF_FIXED_IDLE_CONTROLLER_MODE)
        if default_mode not in mode_options:
            default_mode = controller_state.state if controller_state.state in mode_options else mode_options[0]

        default_temperature = self.options.get(const.CONF_FIXED_IDLE_CONTROLLER_TEMPERATURE)
        if default_temperature is None:
            default_temperature = controller_state.attributes.get(ATTR_TEMPERATURE)
        if default_temperature is None or default_temperature < min_temp or default_temperature > max_temp:
            default_temperature = min_temp

        return self.async_show_form(
            step_id="fixed_idle_controller_state",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_FIXED_IDLE_CONTROLLER_MODE,
                        default=default_mode,
                    ): vol.In(mode_options),
                    vol.Required(
                        const.CONF_FIXED_IDLE_CONTROLLER_TEMPERATURE,
                        default=default_temperature,
                    ): vol.All(
                        vol.Coerce(float),
                        vol.Range(min=min_temp, max=max_temp),
                    ),
                }
            ),
        )

    async def async_step_zones(self, user_input=None):
        """Handle options flow."""

        if user_input is not None:
            self.zones = user_input.get(const.CONF_ZONES)
            return await self.async_step_max_setpoint()

        zone_options = [
            climate
            for climate in self.hass.states.async_entity_ids("climate")
            if climate != self.controller
        ]

        default = [
            climate
            for climate in self.options.get(const.CONF_ZONES, [])
            if climate in zone_options
        ]

        return self.async_show_form(
            step_id=const.CONF_ZONES,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_ZONES,
                        default=default
                    ): vol.All(
                        cv.multi_select(sorted(zone_options)),
                        vol.Length(min=1),
                    ),
                }
            )
        )

    async def async_step_max_setpoint(self, user_input=None):
        """Handle options flow."""

        if user_input is not None:
            self.max_setpoint = user_input.get(const.CONF_MAX_SETPOINT)
            return await self.async_step_hysteresis()

        controller_state = self.hass.states.get(self.controller)
        min_temp = 0
        max_temp = 100
        if self.controller and self.controller.startswith(Platform.CLIMATE) and controller_state:
            min_temp_attr = controller_state.attributes.get(ATTR_MIN_TEMP)
            max_temp_attr = controller_state.attributes.get(ATTR_MAX_TEMP)
            if isinstance(min_temp_attr, (int, float)):
                min_temp = round(min_temp_attr)
            if isinstance(max_temp_attr, (int, float)):
                max_temp = round(max_temp_attr)

        default = self.options.get(const.CONF_MAX_SETPOINT)
        if not default or default < min_temp or default > max_temp:
            default = const.DEFAULT_MAX_SETPOINT

        return self.async_show_form(
            step_id=const.CONF_MAX_SETPOINT,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_MAX_SETPOINT,
                        default=default
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=min_temp, max=max_temp)
                    )
                }
            )
        )

    async def async_step_hysteresis(self, user_input=None):
        """Handle hysteresis option during the options flow."""

        if user_input is not None:
            self.hysteresis = user_input.get(const.CONF_HYSTERESIS)
            return await self.async_step_controller_delay_time()

        default = self.options.get(const.CONF_HYSTERESIS, const.DEFAULT_HYSTERESIS)

        return self.async_show_form(
            step_id=const.CONF_HYSTERESIS,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_HYSTERESIS,
                        default=default
                    ): vol.All(
                        vol.Coerce(float),
                        vol.Range(min=0, max=10)
                    )
                }
            )
        )

    async def async_step_controller_delay_time(self, user_input=None):
        """Handle options flow."""

        if user_input is not None:
            self.controller_delay_time = user_input.get(const.CONF_CONTROLLER_DELAY_TIME)

            return self.async_create_entry(title="", data={
                const.CONF_ZONES: self.zones,
                const.CONF_CONTROLLER: self.controller,
                const.CONF_MAX_SETPOINT: self.max_setpoint,
                const.CONF_CONTROLLER_DELAY_TIME: self.controller_delay_time,
                const.CONF_HYSTERESIS: getattr(self, "hysteresis", const.DEFAULT_HYSTERESIS),
                const.CONF_USE_FIXED_IDLE_CONTROLLER_STATE: (
                    self.use_fixed_idle_controller_state
                    if self.use_fixed_idle_controller_state is not None
                    else self.options.get(
                        const.CONF_USE_FIXED_IDLE_CONTROLLER_STATE,
                        const.DEFAULT_USE_FIXED_IDLE_CONTROLLER_STATE,
                    )
                ),
                const.CONF_FIXED_IDLE_CONTROLLER_MODE: self.fixed_idle_controller_mode,
                const.CONF_FIXED_IDLE_CONTROLLER_TEMPERATURE: self.fixed_idle_controller_temperature,
            })

        default = self.options.get(const.CONF_CONTROLLER_DELAY_TIME)
        if not default:
            default = const.DEFAULT_CONTROLLER_DELAY_TIME

        return self.async_show_form(
            step_id=const.CONF_CONTROLLER_DELAY_TIME,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        const.CONF_CONTROLLER_DELAY_TIME,
                        default=default
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=10, max=300)
                    )
                }
            )
        )
