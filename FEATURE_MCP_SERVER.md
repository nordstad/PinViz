# PinViz MCP Server Implementation Plan

**Goal**: Create an MCP server that generates PinViz wiring diagrams from natural language prompts.

**Timeline**: 4-5 weeks
**Scope**: 25-30 devices, JSON database, hybrid LLM parsing, URL-based device discovery

---

## Phase 1: Core MCP Server + Device Database ✅ COMPLETED

### MCP Server Foundation
- [x] Set up project structure: `src/pinviz_mcp/`
- [x] Install and configure `mcp` Python SDK (v1.22.0)
- [x] Create `server.py` with stdio transport
- [x] Implement tool: `generate_diagram` (Phase 1 placeholder)
- [x] Implement tool: `list_devices` (returns available devices)
- [x] Implement tool: `get_device_info` (returns device specs)
- [x] Implement tool: `search_devices_by_tags` (search by tags)
- [x] Implement tool: `get_database_summary` (database statistics)
- [x] Implement resource: `device_database` (exposes JSON catalog)
- [x] Implement resource: `device_schema` (exposes JSON schema)
- [x] Implement resource: `device_categories` (list categories)
- [x] Implement resource: `device_protocols` (list protocols)
- [x] Test MCP server basic communication

### JSON Device Database
- [x] Design JSON schema for device entries
- [x] Create `src/pinviz_mcp/devices/schema.json`
- [x] Create `src/pinviz_mcp/devices/database.json` with 25 devices
- [x] Add 5 display devices (SSD1306, SH1106, LCD 16x2, E-Paper, ST7735 TFT)
- [x] Add 10 sensor devices (BME280, DHT22, BH1750, DS18B20, PIR, HC-SR04, Photoresistor, MQ-2, MPU6050, TCS34725)
- [x] Add 4 HATs (Terminal Block, Sense HAT, Motor HAT, Servo HAT)
- [x] Add 1 breakout (4-Channel Relay Board)
- [x] Add 5 components/actuators (LED, RGB LED, Button, Relay Module, Buzzer)
- [x] Validate all 25 device entries against schema
- [x] Document device database schema in README

### Device Database Manager
- [x] Create `src/pinviz_mcp/device_manager.py`
- [x] Implement JSON database loading with validation
- [x] Implement fuzzy device name matching (SequenceMatcher with 0.6 threshold)
- [x] Implement device query by ID/name/category/protocol/voltage/tags
- [x] Implement device validation against schema
- [x] Write comprehensive unit tests (31 tests, 100% pass rate)
- [x] Integration ready for existing PinViz `DeviceRegistry`

---

## Phase 2: Natural Language Parsing + Pin Assignment (Weeks 2-3)

### Hybrid Prompt Parser
- [ ] Create `src/pinviz_mcp/parser.py`
- [ ] Implement regex patterns for common prompts
  - [ ] Pattern: "connect {device1} and {device2}"
  - [ ] Pattern: "wire {device} to my pi"
  - [ ] Pattern: "{device1}, {device2}, and {device3}"
- [ ] Implement Claude API integration for fallback
- [ ] Extract device list from prompt
- [ ] Extract board type (default: Raspberry Pi 5)
- [ ] Extract special requirements (pull-ups, shared buses)
- [ ] Write unit tests for parser
- [ ] Test with 20+ example prompts

### Intelligent Pin Assigner
- [ ] Create `src/pinviz_mcp/pin_assignment.py`
- [ ] Implement GPIO availability tracker
- [ ] Implement I2C bus sharing algorithm
- [ ] Implement SPI chip select allocation
- [ ] Implement power rail distribution (3.3V vs 5V)
- [ ] Implement constraint solver for pin conflicts
- [ ] Add conflict detection and resolution
- [ ] Handle edge cases (address conflicts, voltage mismatches)
- [ ] Write unit tests for pin assignment
- [ ] Test with complex multi-device scenarios

### Connection Generator
- [ ] Create `src/pinviz_mcp/connection_builder.py`
- [ ] Convert pin assignments to PinViz `Connection` objects
- [ ] Auto-insert pull-up resistors for I2C connections
- [ ] Auto-assign wire colors based on pin roles
- [ ] Generate complete `Diagram` object
- [ ] Support YAML output format
- [ ] Support direct SVG rendering
- [ ] Write unit tests for connection builder
- [ ] Integration test: prompt → Diagram → SVG

---

## Phase 3: URL-Based Device Documentation Parser (Weeks 3-4)

### Documentation Fetcher
- [ ] Create `src/pinviz_mcp/doc_parser.py`
- [ ] Implement URL content fetcher (handle HTML/PDF)
- [ ] Implement Claude API datasheet extraction
  - [ ] Extract pin definitions (name, role, position)
  - [ ] Extract I2C address (if applicable)
  - [ ] Extract communication protocol
  - [ ] Extract voltage requirements
- [ ] Validate extracted specs against schema
- [ ] Generate temporary device entry
- [ ] Write unit tests for doc parser
- [ ] Test with 10+ real device datasheets

### Interactive Device Registration
- [ ] Implement fallback: prompt user for missing specs
- [ ] Create interactive CLI form for device entry
  - [ ] Prompt for pin names and roles
  - [ ] Prompt for communication protocol
  - [ ] Prompt for I2C address (if applicable)
  - [ ] Prompt for voltage requirements
- [ ] Validate user-provided data
- [ ] Save new device to `user_devices.json`
- [ ] Test interactive flow with unknown device

### Device Database Growth System
- [ ] Create `src/pinviz_mcp/devices/user_devices.json`
- [ ] Implement user device loading alongside main database
- [ ] Implement device validation workflow
- [ ] Create migration script: user → main database
- [ ] Document community contribution process
- [ ] Test device persistence across sessions

---

## Phase 4: Testing, Refinement, Device Library (Weeks 4-5)

### Comprehensive Test Suite
- [ ] Write unit tests for all modules (target: 80% coverage)
- [ ] Write integration tests: prompt → SVG generation
- [ ] Create test fixtures for 10-15 real-world scenarios
  - [ ] Single device connection
  - [ ] Two I2C devices (bus sharing)
  - [ ] Mixed protocols (I2C + SPI)
  - [ ] HAT with multiple devices
  - [ ] Complex scenario (5+ connections)
- [ ] Run pytest and verify coverage
- [ ] Fix any failing tests

### Device Database Completion
- [ ] Verify all 25-30 devices have complete specs
- [ ] Cross-reference device specs with 3+ datasheets
- [ ] Test each device entry with real connection scenarios
- [ ] Add device images/thumbnails (optional)
- [ ] Document each device category in README

### Documentation + Examples
- [ ] Write MCP server installation guide
- [ ] Write MCP server usage guide
- [ ] Create 10+ example prompts with expected outputs
- [ ] Document device database structure
- [ ] Write device contribution guide
- [ ] Update main PinViz README with MCP server info
- [ ] Create troubleshooting guide

### Final Polish
- [ ] Run ruff linting on all new code
- [ ] Run ruff formatting on all new code
- [ ] Review code for security issues
- [ ] Performance testing (prompt → SVG generation time)
- [ ] Error message improvements (user-friendly)
- [ ] CLI help text and documentation strings

---

## Project Structure

```
src/pinviz_mcp/
├── __init__.py
├── server.py                 # MCP server entry point
├── parser.py                 # Natural language → structured data
├── pin_assignment.py         # Intelligent pin allocation algorithm
├── connection_builder.py     # Generate PinViz Connection objects
├── device_manager.py         # Query/load JSON device database
├── doc_parser.py             # URL-based device discovery
└── devices/
    ├── database.json         # Main 25-30 device catalog
    ├── user_devices.json     # User-contributed devices
    └── schema.json           # JSON schema for validation
```

---

## Success Criteria

- [ ] Generate accurate diagrams from natural language prompts
- [ ] Handle 80%+ of common device connection scenarios
- [ ] URL-based device addition works for Adafruit/SparkFun/Waveshare
- [ ] Database covers 25-30 popular devices
- [ ] MCP server integrates cleanly with PinViz architecture
- [ ] Test coverage >80%
- [ ] Documentation complete

---

## Key Technical Decisions

1. **JSON over SQL**: Easy version control, human-readable, no server dependency
2. **Hybrid LLM**: Regex for 80% (fast, cheap), Claude API for 20% (complex cases)
3. **URL Parsing**: Unique feature - Claude extracts specs from datasheets
4. **Stdio Transport**: Standard MCP communication pattern

---

## Risk Mitigation

- **Claude API cost**: Cache parsed devices, minimize token usage
- **Pin conflicts**: Conservative algorithm, clear error messages
- **Database maintenance**: Community workflow, validation automation

---

## Notes

- Do not commit this file to git
- Check off tasks as completed
- Update timeline estimates as needed
- Add notes/blockers in this section
