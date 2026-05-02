"""Store constants."""

VERSION = "1.1.4"
DOMAIN = "zoned_heating"
NAME = "Zoned Heating"
DATA = "data"
UPDATE_LISTENER = "update_listener"

CONF_CONTROLLER = "controller"
CONF_ZONES = "zones"
CONF_MAX_SETPOINT = "max_setpoint"
CONF_CONTROLLER_DELAY_TIME = "controller_delay_time"
CONF_USE_FIXED_CONTROLLER_RESTORATION_SETTING = "use_fixed_controller_restoration_setting"
CONF_FIXED_CONTROLLER_RESTORATION_MODE = "fixed_controller_restoration_mode"
CONF_FIXED_CONTROLLER_RESTORATION_SETPOINT = "fixed_controller_restoration_setpoint"

DEFAULT_MAX_SETPOINT = 21
DEFAULT_CONTROLLER_DELAY_TIME = 10
DEFAULT_HYSTERESIS = 1
DEFAULT_USE_FIXED_CONTROLLER_RESTORATION_SETTING = False
CONF_HYSTERESIS = "hysteresis"

ATTR_OVERRIDE_ACTIVE = "override_active"
ATTR_TEMPERATURE_INCREASE = "temperature_increase"
ATTR_STORED_CONTROLLER_STATE = "stored_controller_state"
ATTR_STORED_CONTROLLER_SETPOINT = "stored_controller_setpoint"
