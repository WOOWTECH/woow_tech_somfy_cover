"""Constants for the Somfy PoE Motor integration."""
from typing import Final

# Integration domain
DOMAIN: Final = "somfy_poe"

# Configuration keys
CONF_NAME: Final = "name"
CONF_HOST: Final = "host"
CONF_TARGET_ID: Final = "target_id"
CONF_KEY: Final = "key"
CONF_PORT: Final = "port"

# Defaults
DEFAULT_PORT: Final = 55055
DEFAULT_TIMEOUT: Final = 5.0
DEFAULT_NAME: Final = "Somfy Cover"

# Update intervals
UPDATE_INTERVAL_NORMAL: Final = 30  # seconds
UPDATE_INTERVAL_FAST: Final = 2  # seconds during movement

# API constants
API_PORT: Final = 55055
AES_BLOCK_SIZE: Final = 16
TARGET_ID_LENGTH: Final = 6
KEY_LENGTH: Final = 32

# API Methods
METHOD_PING: Final = "status.ping"
METHOD_STATUS_INFO: Final = "status.info"
METHOD_STATUS_POSITION: Final = "status.position"
METHOD_MOVE_UP: Final = "move.up"
METHOD_MOVE_DOWN: Final = "move.down"
METHOD_MOVE_STOP: Final = "move.stop"
METHOD_MOVE_TO: Final = "move.to"

# Error codes from API documentation
ERROR_DATA_OUT_OF_RANGE: Final = 1
ERROR_UNKNOWN_MESSAGE: Final = 16
ERROR_MESSAGE_LENGTH: Final = 17
ERROR_FEATURE_NOT_SUPPORTED: Final = 37
ERROR_DEVICE_LOCKED: Final = 32
ERROR_END_LIMITS_NOT_SET: Final = 34
ERROR_THERMAL_PROTECTION: Final = 48
ERROR_OBSTACLE_DETECTION: Final = 49
ERROR_TARGET_OUT_OF_RANGE: Final = 36
ERROR_IN_MOTION: Final = 38
ERROR_WRONG_POSITION: Final = 33
ERROR_NO_PRESET_POSITION: Final = 35
ERROR_END_LIMITS_SET: Final = 47
ERROR_LAST_PRESET_REACHED: Final = 40
ERROR_LOW_PRIORITY: Final = 42
ERROR_WINK_IN_PROGRESS: Final = 43
ERROR_DIAGNOSTIC_UNAVAILABLE: Final = 45
ERROR_INCORRECT_PARAMS: Final = 50
ERROR_UNKNOWN: Final = 254
ERROR_BUSY: Final = 255
