import folium
from folium import plugins
import os
from dotenv import load_dotenv
import requests
from scapy.all import traceroute
from collections import defaultdict

def geolocateIP(ipAddress):
    url = f"https://ipinfo.io/{ipAddress}/json?token={IPINFO_TOKEN}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        loc = data.get("loc", None)
        if loc:
            lat, lon = map(float, loc.split(","))
            label = f"{data.get('city', 'Unknown city')}, {data.get('region', 'Unknown region')}, {data.get('country', 'Unknown country')}"
            return lat, lon, label
    return None, None, "Unknown location"

def generateHopMap(hopLocations, outputFile="test_route.html"):
    if not hopLocations:
        print("No hop locations to plot")
        return
    cityGroups = defaultdict(list)
    for hop in hopLocations:
        cityGroups[hop['label']].append(hop)

    avg_lat = sum([hop['lat'] for hop in hopLocations]) / len(hopLocations)
    avg_lon = sum([hop['lon'] for hop in hopLocations]) / len(hopLocations)
    tracerouteMap = folium.Map(location=[avg_lat, avg_lon], zoom_start=4)

    for city, hops in cityGroups.items():
        lat = hops[0]['lat']
        lon = hops[0]['lon']

        popupText = f"City: {city}<br>"
        popupText += "<br>".join([f"Hop {hop['hop_number']}: {hop['ip']}" for hop in hops])
        folium.Marker(
            location=[lat, lon],
            popup=popupText,
            tooltip=f"Hops {hops[0]['hop_number']} - {hops[-1]['hop_number']} in {city}",
            icon=folium.Icon(color="green", icon="info-sign")
        ).add_to(tracerouteMap)

    cityCoordinates = [(hops[0]['lat'], hops[0]['lon']) for hops in cityGroups.values()]
    folium.PolyLine(cityCoordinates, color="blue", weight=2.5, opacity=1).add_to(tracerouteMap)
    tracerouteMap.save(outputFile)
    print(f"Map saved to {outputFile}")

def main():
    # get route
    target = "www.chinadaily.com.cn"
    print(f"Tracing route to '{target}'...")
    result, _ = traceroute(target)
    print("Done.")

    # parse data
    print("Geolocating IP addresses...")
    hopLocations = []
    previousIP = None
    seenLocations = set()
    for hopNumber, (snd, rcv) in enumerate(result, start=1):
        ip = rcv.src
        lat, lon, label = geolocateIP(ip) # get location for ip address

        locationId = (ip, label)

        if ip == previousIP or locationId in seenLocations:
            continue

        previousIP = ip
        seenLocations.add(locationId)

        if lat and lon:
            hopLocations.append({
                "hop_number": hopNumber,
                "ip": ip,
                "lat": lat,
                "lon": lon,
                "label": label
            })
    print("Done.")
    print(f"Found {len(hopLocations)} unique IP addresses.")
    print(hopLocations)
    print("Generating map...")
    generateHopMap(hopLocations, "traceroute_map.html")
    print("Done.")

if __name__ == "__main__":
    load_dotenv()
    IPINFO_TOKEN = os.getenv("IPINFO_TOKEN")
    main()