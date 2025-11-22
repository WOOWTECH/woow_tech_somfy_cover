# Documentation Index

**WoowTech Somfy Cover Integration for Home Assistant**

**Version**: 1.0.2
**Last Updated**: 2025-11-22

---

## Documentation Structure

This integration includes comprehensive documentation covering all aspects from basic configuration to advanced development.

---

## Quick Start

**For Users**: Start with [CONFIGURATION.md](CONFIGURATION.md)

**For Developers**: Start with [ARCHITECTURE.md](ARCHITECTURE.md) and [API_REFERENCE.md](API_REFERENCE.md)

**For Contributors**: Start with [DEVELOPMENT.md](DEVELOPMENT.md) and [TESTING.md](TESTING.md)

---

## Documentation Files

### User Documentation

#### [CONFIGURATION.md](CONFIGURATION.md)
Complete configuration guide for end users.

**Topics**:
- Prerequisites (hardware, network, credentials)
- Finding motor credentials (IP, target ID, encryption key)
- Config Flow (UI) setup step-by-step
- YAML configuration with examples
- Multiple motor setups
- Troubleshooting common issues
- Advanced configuration (automations, customization)

**Who needs this**: All users setting up the integration

---

### Technical Documentation

#### [ARCHITECTURE.md](ARCHITECTURE.md)
Complete system architecture and design documentation.

**Topics**:
- System overview and key features
- Layer architecture (HA → Client → Protocol → Encryption → Transport)
- Detailed data flow diagrams
- Component details (Config Flow, Coordinator, Cover Entity, API layers)
- Dual configuration support (Config Flow + YAML)
- Wake-up mechanism implementation
- Error handling hierarchy
- Performance characteristics
- Security considerations

**Who needs this**: Developers, advanced users, contributors

---

#### [API_REFERENCE.md](API_REFERENCE.md)
Complete API reference for the protocol layer.

**Topics**:
- SomfyClient API (high-level interface)
- Protocol layer (JSON-RPC)
- Encryption layer (AES-128-CBC)
- Transport layer (UDP socket management)
- Data models (DeviceInfo, PositionStatus, enums)
- Error codes (30+ motor error codes)
- Code examples and usage patterns
- Thread safety and performance tips

**Who needs this**: Developers using the API layer, integration developers

---

#### [TESTING.md](TESTING.md)
Comprehensive testing guide.

**Topics**:
- Testing levels (standalone, integration, end-to-end)
- Standalone test scripts in `/working_tests/`
- Integration testing with Home Assistant
- Manual testing procedures with checklists
- Automated testing (unit tests, CI/CD)
- Troubleshooting test failures
- Performance testing metrics
- Continuous testing recommendations

**Who needs this**: Developers, QA engineers, contributors

---

#### [DEVELOPMENT.md](DEVELOPMENT.md)
Development guide for contributors.

**Topics**:
- Development environment setup
- Code structure and module responsibilities
- Architecture deep dive
- Adding new features (commands, data fields, config options)
- Debugging tips and tools
- Common pitfalls and solutions
- Code style guidelines
- Testing during development
- Development workflow

**Who needs this**: Contributors, developers extending the integration

---

### Implementation Documentation

#### [IMPLEMENTATION_ANALYSIS.md](IMPLEMENTATION_ANALYSIS.md)
Historical document showing the analysis and testing process.

**Topics**:
- Device information and credentials
- Connection methods tested (UDP, TCP/TLS, CoAP, HTTPS)
- Test results from various approaches
- Working encryption method discovery (zero-padding)
- Socket configuration requirements
- Device information structure
- Code examples from testing

**Who needs this**: Historical reference, understanding implementation decisions

---

#### [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
Original implementation plan (now superseded by actual implementation).

**Topics**:
- File-by-file analysis
- Known issues and solutions
- Implementation steps (completed)
- Testing plan (completed)
- Success criteria (all met)

**Who needs this**: Historical reference

**Note**: This document reflects the planning phase. For actual implementation, see ARCHITECTURE.md and API_REFERENCE.md.

---

#### [WAKEUP_IMPLEMENTATION.md](WAKEUP_IMPLEMENTATION.md)
Detailed documentation of the motor wake-up mechanism.

**Topics**:
- Problem description (motor hibernation)
- Solution implemented (transparent wake-up)
- Implementation details in transport layer
- Test results and verification
- Benefits and production deployment

**Who needs this**: Developers interested in wake-up logic, troubleshooting wake-up issues

---

### Changelog and Version History

#### [CHANGELOG.md](../custom_components/woow_tech_somfy_cover/CHANGELOG.md)
Complete version history with all changes.

**Versions**:
- **v1.0.2** (2025-11-22): YAML parsing improvements (unquoted hex values)
- **v1.0.1** (2025-11-22): YAML configuration support
- **v1.0.0** (2025-11-22): Initial release

**Who needs this**: All users, for understanding version differences and upgrade paths

---

## Documentation by Use Case

### I want to install and use the integration

**Read**:
1. [CONFIGURATION.md](CONFIGURATION.md) - Complete setup guide
2. [CHANGELOG.md](../custom_components/woow_tech_somfy_cover/CHANGELOG.md) - Current version features
3. [README.md](../custom_components/woow_tech_somfy_cover/README.md) - Quick start

**Troubleshooting**:
- [CONFIGURATION.md#troubleshooting](CONFIGURATION.md#troubleshooting) - Common issues

---

### I want to understand how it works

**Read**:
1. [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. [API_REFERENCE.md](API_REFERENCE.md) - Protocol details
3. [WAKEUP_IMPLEMENTATION.md](WAKEUP_IMPLEMENTATION.md) - Wake-up mechanism

---

### I want to contribute code

**Read**:
1. [DEVELOPMENT.md](DEVELOPMENT.md) - Development setup and workflow
2. [ARCHITECTURE.md](ARCHITECTURE.md) - Understanding the codebase
3. [TESTING.md](TESTING.md) - How to test changes
4. [API_REFERENCE.md](API_REFERENCE.md) - API details

**Also Check**:
- [CODE_REVIEW_FIXES.md](../CODE_REVIEW_FIXES.md) - Lessons learned from code review

---

### I want to add a new feature

**Read**:
1. [DEVELOPMENT.md#adding-new-features](DEVELOPMENT.md#adding-new-features) - How to add commands, data fields, config options
2. [ARCHITECTURE.md#component-details](ARCHITECTURE.md#component-details) - Where each component fits
3. [TESTING.md](TESTING.md) - How to test new features

---

### I want to test the integration

**Read**:
1. [TESTING.md](TESTING.md) - Complete testing guide
2. [DEVELOPMENT.md#testing-during-development](DEVELOPMENT.md#testing-during-development) - Quick test loop

**Run Tests**:
```bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests/
python3 test_decrypt_responses.py  # Standalone API test
python3 test_wakeup_mechanism.py   # Wake-up mechanism test
```

---

### I'm troubleshooting an issue

**Read**:
1. [CONFIGURATION.md#troubleshooting](CONFIGURATION.md#troubleshooting) - User issues
2. [TESTING.md#troubleshooting-tests](TESTING.md#troubleshooting-tests) - Test failures
3. [DEVELOPMENT.md#debugging-tips](DEVELOPMENT.md#debugging-tips) - Development debugging

**Enable Debug Logging**:
```yaml
logger:
  logs:
    custom_components.woow_tech_somfy_cover: debug
```

---

### I'm curious about implementation history

**Read**:
1. [IMPLEMENTATION_ANALYSIS.md](IMPLEMENTATION_ANALYSIS.md) - Testing journey
2. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Original planning
3. [CHANGELOG.md](../custom_components/woow_tech_somfy_cover/CHANGELOG.md) - What changed when

---

## Documentation Maintenance

### When to Update Documentation

**Code Changes**:
- New features → Update ARCHITECTURE.md, API_REFERENCE.md, DEVELOPMENT.md
- Bug fixes → Update CHANGELOG.md
- Configuration changes → Update CONFIGURATION.md
- New tests → Update TESTING.md

**Version Releases**:
- Update CHANGELOG.md with version details
- Update version numbers in all documentation headers
- Review all docs for accuracy

**Issues Reported**:
- Add to troubleshooting sections
- Create examples if needed
- Update FAQ (if we create one)

---

## Contributing to Documentation

### Documentation Standards

1. **Clear and Concise**: Write for your audience
2. **Code Examples**: Include working examples
3. **Actual Implementation**: Document reality, not plans
4. **Up-to-date**: Keep in sync with code
5. **Cross-references**: Link related sections

### Documentation Review Checklist

- [ ] Accurate to actual implementation
- [ ] Clear for intended audience
- [ ] Code examples work
- [ ] Cross-references correct
- [ ] Version numbers updated
- [ ] No outdated information
- [ ] Grammar and spelling checked

---

## Quick Reference

### File Paths

**Integration Code**:
```
/Users/alanlin/Documents/woowtech_somfy_new/
├── custom_components/woow_tech_somfy_cover/  # Integration code
│   ├── __init__.py                            # Entry point
│   ├── cover.py                               # Cover platform
│   ├── coordinator.py                         # Data coordinator
│   ├── config_flow.py                         # UI configuration
│   ├── const.py                               # Constants
│   ├── errors.py                              # Error definitions
│   ├── api/                                   # API layer
│   │   ├── client.py                          # High-level client
│   │   ├── protocol.py                        # JSON-RPC protocol
│   │   ├── transport.py                       # UDP transport
│   │   ├── encryption.py                      # AES encryption
│   │   └── models.py                          # Data models
│   ├── CHANGELOG.md                           # Version history
│   └── README.md                              # Integration README
├── docs/                                      # Documentation
│   ├── ARCHITECTURE.md                        # Architecture
│   ├── API_REFERENCE.md                       # API docs
│   ├── CONFIGURATION.md                       # User guide
│   ├── TESTING.md                             # Testing guide
│   ├── DEVELOPMENT.md                         # Dev guide
│   ├── IMPLEMENTATION_ANALYSIS.md             # Historical
│   ├── IMPLEMENTATION_PLAN.md                 # Historical
│   ├── WAKEUP_IMPLEMENTATION.md               # Wake-up docs
│   └── DOCUMENTATION_INDEX.md                 # This file
└── working_tests/                             # Test scripts
    ├── test_decrypt_responses.py              # Main test
    ├── test_wakeup_mechanism.py               # Wake-up test
    ├── test_01_udp_ping_encrypted.py          # UDP test
    └── test_ha_integration_debug.py           # HA integration test
```

---

### Key Concepts

| Concept | Description | Document |
|---------|-------------|----------|
| **Config Flow** | UI-based setup | CONFIGURATION.md |
| **YAML Config** | File-based setup | CONFIGURATION.md |
| **Coordinator** | Polling and state management | ARCHITECTURE.md |
| **Wake-up** | Motor hibernation handling | WAKEUP_IMPLEMENTATION.md |
| **Zero-padding** | Encryption padding method | API_REFERENCE.md |
| **Adaptive Polling** | 2s moving, 30s stopped | ARCHITECTURE.md |
| **Position Inversion** | Somfy 0=open ↔ HA 0=closed | ARCHITECTURE.md |
| **Target ID** | Last 6 chars of MAC | CONFIGURATION.md |

---

### Common Tasks

| Task | Command/Steps | Document |
|------|---------------|----------|
| **Install Integration** | Copy to custom_components/ | CONFIGURATION.md |
| **Add Motor (UI)** | Settings → Add Integration | CONFIGURATION.md |
| **Add Motor (YAML)** | Edit configuration.yaml | CONFIGURATION.md |
| **Enable Debug Logs** | Add logger config | CONFIGURATION.md, TESTING.md |
| **Test Standalone** | Run test scripts in working_tests/ | TESTING.md |
| **Test in HA** | Add integration, test controls | TESTING.md |
| **Debug Issue** | Check logs, run tests | DEVELOPMENT.md |
| **Add Feature** | Follow dev workflow | DEVELOPMENT.md |

---

## Documentation Versions

| Documentation Version | Integration Version | Date | Notes |
|----------------------|---------------------|------|-------|
| 1.0.2 | 1.0.2 | 2025-11-22 | Comprehensive docs created |
| 1.0.1 | 1.0.1 | 2025-11-22 | YAML config added |
| 1.0.0 | 1.0.0 | 2025-11-22 | Initial release |

---

## Feedback

Found documentation issues?

- Unclear sections
- Missing information
- Outdated content
- Broken links
- Typos or errors

Please report via GitHub issues or submit a pull request with corrections.

---

**Last Updated**: 2025-11-22
**Documentation Version**: 1.0.2
**Integration Version**: 1.0.2
