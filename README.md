# Body Metrics

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://www.home-assistant.io)

Home Assistant custom integration for smart body scales. Identifies household members by weight/impedance matching and calculates body composition metrics using BIA (Bioelectrical Impedance Analysis) formulas.

## Features

- **Per-person tracking** — each person gets their own device with 8 sensors
- **Body composition** — weight, BMI, body fat %, muscle mass, water %, bone mass
- **Smart matching** — weighted score algorithm assigns readings to the right person
- **EMA smoothing** — exponential moving average filters out noisy readings
- **Menu-based setup** — add, edit, remove people through the UI
- **HACS-ready** — install as a custom repository

## Sensors

| Sensor | Unit | Description |
|--------|------|-------------|
| Weight | kg | Smoothed weight reading |
| Impedance | Ω | Smoothed impedance reading |
| BMI | kg/m² | Body Mass Index |
| Body fat | % | Body fat percentage (requires impedance) |
| Muscle mass | kg | Skeletal muscle mass (requires impedance) |
| Water | % | Body water percentage (requires impedance) |
| Bone mass | kg | Bone mineral mass (requires impedance) |
| Confidence | % | How closely the reading matched this person |

## Installation

### HACS (recommended)

1. Open HACS → Integrations → three-dot menu → **Custom repositories**
2. Add this repository URL, category: **Integration**
3. Install **Body Metrics**
4. Restart Home Assistant

### Manual

Copy `custom_components/body_metrics/` to your `config/custom_components/` directory and restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration → Body Metrics**
2. Select your weight sensor (and optionally impedance sensor)
3. Open integration options to add people with their expected weight, height, age, and sex

## Requirements

- Home Assistant 2024.1.0 or newer
- A body scale that exposes weight (and optionally impedance) as HA sensor entities

## License

[MIT](LICENSE)
