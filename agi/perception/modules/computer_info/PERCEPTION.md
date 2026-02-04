
---
name: computer_info
description: Provides detailed local environment information.
category: system
sub_category: specs
---

# Computer Info Perception

**Type**: Passive/On-Demand Sensor
**Description**: Provides comprehensive local environment data including hardware, network, battery, WiFi, disk, and weather.

## Signals
- `system`: platform, release, version, architecture, processor, hostname, cpu_count, uptime
- `network`: local_ip, public_ip, location (city, region, country, lat, lon)
- `battery`: percentage, state (charging/discharging)
- `wifi`: ssid, signal_rssi, connected
- `disk`: total_gb, used_gb, free_gb, percent_used
- `apps`: list of installed applications (macOS)
- `weather`: current temperature, weather code (if location available)
- `time`: timestamp, time_readable, timezone
