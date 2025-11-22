# Changelog

All notable changes to the WoowTech Somfy Cover integration will be documented in this file.

## [1.0.1] - 2025-11-22

### Added
- YAML configuration support via `configuration.yaml`
- `async_setup()` function in `__init__.py` for YAML discovery
- `async_setup_platform()` function in `cover.py` for YAML platform setup
- `PLATFORM_SCHEMA` validation for YAML configuration
- `SomfyYAMLCover` class for YAML-configured entities
- Example YAML configuration file (`example_configuration.yaml`)
- Comprehensive documentation for YAML configuration in README.md

### Changed
- Version bumped to 1.0.1 in `manifest.json`
- README.md updated with YAML configuration examples and instructions
- Version badge updated to 1.0.1

### Technical Details
- YAML and Config Flow configurations can coexist
- Each YAML cover creates its own coordinator and client instance
- YAML covers use unique_id format: `yaml_<target_id>_<sanitized_name>`
- Config Flow covers use unique_id format: `<entry_id>_cover`
- No conflicts between YAML and Config Flow entities

### Backward Compatibility
- Fully backward compatible with v1.0.0
- Existing Config Flow entries continue to work unchanged
- No breaking changes

## [1.0.0] - 2025-11-22

### Initial Release
- Config Flow UI setup support
- Encrypted UDP communication with AES-128-CBC
- Full position control (open, close, stop, set position)
- Automatic motor wake-up mechanism
- Real-time position polling with adaptive intervals
- Comprehensive error handling and logging
- Docker/macOS support
- Device registry integration
- DataUpdateCoordinator pattern for efficient state management
