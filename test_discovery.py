#!/usr/bin/env python3
"""
Test script to discover Bellphonics services on the local network.
Usage: python test_discovery.py
"""

from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import time


class BellphonicsListener(ServiceListener):
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} updated")

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        print(f"Service {name} removed")

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            print(f"\n✅ Found Bellphonics service!")
            print(f"   Name: {name}")
            print(f"   Address: {'.'.join(map(str, info.addresses[0]))}")
            print(f"   Port: {info.port}")
            print(f"   Server: {info.server}")
            if info.properties:
                print(f"   Properties:")
                for key, value in info.properties.items():
                    print(f"      {key.decode('utf-8')}: {value.decode('utf-8')}")
            print(f"   URL: http://{'.'.join(map(str, info.addresses[0]))}:{info.port}/speak")
        else:
            print(f"Service {name} found but couldn't get info")


if __name__ == "__main__":
    print("🔍 Searching for Bellphonics services on the local network...")
    print("Press Ctrl+C to stop\n")
    
    zeroconf = Zeroconf()
    listener = BellphonicsListener()
    browser = ServiceBrowser(zeroconf, "_bellphonics._tcp.local.", listener)
    
    try:
        time.sleep(10)  # Search for 10 seconds
        print("\n⏱️  Search complete")
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    finally:
        zeroconf.close()
