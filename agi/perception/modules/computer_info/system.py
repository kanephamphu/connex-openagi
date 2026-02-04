
import os
import shutil
import socket
import platform
import time
import requests
import json
import subprocess
from typing import Any, Dict, List, Optional
from agi.perception.base import PerceptionModule, PerceptionMetadata

class ComputerInfoPerception(PerceptionModule):
    """
    Perceives detailed local computer information:
    - Available applications
    - Hardware (CPU, Arch, OS)
    - Time and Uptime
    - Network (IP, Location, Weather)
    """
    
    @property
    def metadata(self) -> PerceptionMetadata:
        return PerceptionMetadata(
            name="computer_info",
            description="Provides detailed local environment information: installed apps, hardware specs, uptime, battery status, WiFi details (SSID/Signal), disk usage, current time, IP address, geographical location, and local weather.",
            version="1.0.0"
        )

    def __init__(self, config):
        super().__init__(config)
        self.cached_geo = {}
        self.last_geo_check = 0
        self.geo_cache_ttl = 3600 # 1 hour

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def perceive(self, query: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Gathers a comprehensive snapshot of computer state.
        """
        data = {
            "timestamp": time.time(),
            "time_readable": time.ctime(),
            "timezone": time.tzname,
            "system": self._get_system_info(),
            "network": await self._get_network_info(),
            "battery": self._get_battery_info(),
            "wifi": self._get_wifi_info(),
            "disk": self._get_disk_info(),
            "apps": self._get_installed_apps() if query != "fast" else "Skipped"
        }
        
        # Merge weather into network/geo context if available
        if data["network"].get("location"):
            weather = await self._get_weather(data["network"]["location"])
            data["weather"] = weather
            
        return data

    def _get_system_info(self) -> Dict[str, Any]:
        uptime_str = "Unknown"
        try:
            if platform.system() == "Darwin":
                # Get boot time via sysctl
                out = subprocess.check_output(["sysctl", "-n", "kern.boottime"]).decode().split()[3].replace(",", "")
                boot_time = int(out)
                uptime_seconds = int(time.time()) - boot_time
                hours, remainder = divmod(uptime_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime_str = f"{hours}h {minutes}m"
        except:
            pass

        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "cpu_count": os.cpu_count(),
            "uptime": uptime_str
        }

    def _get_battery_info(self) -> Dict[str, Any]:
        try:
            if platform.system() == "Darwin":
                output = subprocess.check_output(["pmset", "-g", "batt"]).decode()
                import re
                percent = re.search(r"(\d+)%", output)
                state = re.search(r";\s+([^;]+);", output)
                return {
                    "percentage": int(percent.group(1)) if percent else None,
                    "state": state.group(1) if state else "unknown",
                    "raw": output.strip().split("\n")[-1]
                }
        except:
            pass
        return {"error": "Not available"}

    def _get_wifi_info(self) -> Dict[str, Any]:
        try:
            if platform.system() == "Darwin":
                # macOS internal airport tool
                cmd = ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"]
                output = subprocess.check_output(cmd).decode()
                import re
                ssid = re.search(r" SSID: (.+)", output)
                rssi = re.search(r" agrCtlRSSI: (-\d+)", output)
                return {
                    "ssid": ssid.group(1).strip() if ssid else "None",
                    "signal_rssi": int(rssi.group(1)) if rssi else None,
                    "connected": ssid is not None
                }
        except:
            pass
        return {"connected": False}

    def _get_disk_info(self) -> Dict[str, Any]:
        try:
            usage = shutil.disk_usage("/")
            return {
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "percent_used": round((usage.used / usage.total) * 100, 1)
            }
        except:
            return {}

    async def _get_network_info(self) -> Dict[str, Any]:
        info = {
            "local_ip": socket.gethostbyname(socket.gethostname()),
            "public_ip": "Unknown",
            "location": None
        }
        
        now = time.time()
        if now - self.last_geo_check < self.geo_cache_ttl and self.cached_geo:
            return self.cached_geo

        try:
            # Get public IP and Geo info
            resp = requests.get("https://ipapi.co/json/", timeout=3)
            if resp.status_code == 200:
                geo_data = resp.json()
                info["public_ip"] = geo_data.get("ip")
                info["location"] = {
                    "city": geo_data.get("city"),
                    "region": geo_data.get("region"),
                    "country": geo_data.get("country_name"),
                    "latitude": geo_data.get("latitude"),
                    "longitude": geo_data.get("longitude")
                }
                self.cached_geo = info
                self.last_geo_check = now
        except:
            pass
            
        return info

    async def _get_weather(self, loc: Dict[str, Any]) -> Dict[str, Any]:
        lat = loc.get("latitude")
        lon = loc.get("longitude")
        if not lat or not lon:
            return {}
            
        try:
             w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
             resp = requests.get(w_url, timeout=3)
             if resp.status_code == 200:
                 return resp.json().get("current_weather", {})
        except:
            pass
        return {}

    def _get_installed_apps(self) -> List[str]:
        apps = []
        if platform.system() == "Darwin": # macOS
            try:
                # Scan /Applications
                items = os.listdir("/Applications")
                apps = [item.replace(".app", "") for item in items if item.endswith(".app")]
            except:
                pass
        elif platform.system() == "Windows":
            # Very simplified for Windows
            apps = ["Registry scan required"]
        else:
            # Linux: look for common bin paths or flatpaks
            apps = ["/usr/bin scan required"]
            
        return sorted(apps)[:50] # Limit to top 50 for context size
