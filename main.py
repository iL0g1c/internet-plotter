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
    for idx, hop in enumerate(hopLocations):
        cityGroups[hop['label']].append((idx + 1, hop))
    avg_lat = sum([hop['lat'] for hop in hopLocations]) / len(hopLocations)
    avg_lon = sum([hop['lon'] for hop in hopLocations]) / len(hopLocations)
    tracerouteMap = folium.Map(location=[avg_lat, avg_lon], zoom_start=4)

    for city, hops in cityGroups.items():
        lat = hops[0][1]['lat']
        lon = hops[0][1]['lon']

        hopNumbers = [str(hop[0]) for hop in hops]
        ipAddresses = [hop[1]['ip'] for hop in hops]
        popupText = f"City: {city}<br>Hops: {hopNumbers[0]}-{hopNumbers[-1]}<br>IPs: {', '.join(ipAddresses)}"

        folium.Marker(
            location=[lat, lon],
            popup=popupText,
            tooltip=f"Hops {hopNumbers[0]}-{hopNumbers[-1]} in {city}",
            icon=folium.Icon(color="green", icon="info-sign")
        ).add_to(tracerouteMap)

    hopCoordinates = [[hop['lat'], hop['lon']] for hop in hopLocations]
    folium.PolyLine(hopCoordinates, color="blue", weight=2.5, opacity=1).add_to(tracerouteMap)
    tracerouteMap.save(outputFile)
    print(f"Map saved to {outputFile}")

def main():
    # get route
    target = "www.google.com"
    print(f"Tracing route to '{target}'...")
    result, _ = traceroute(target)
    print("Done.")

    # parse data
    print("Geolocating IP addresses...")
    hopLocations = []
    previousIP = None
    for snd, rcv in result:
        ip = rcv.src
        if ip == previousIP:
            continue
        previousIP = ip
        lat, lon, label = geolocateIP(ip) # get location for ip address

        if lat and lon:
            hopLocations.append({
                "ip": ip,
                "lat": lat,
                "lon": lon,
                "label": label
            })
    print("Done.")
    print(f"Found {len(hopLocations)} unique IP addresses.")
    print("Generating map...")
    generateHopMap(hopLocations, "traceroute_map.html")
    print("Done.")

if __name__ == "__main__":
    load_dotenv()
    IPINFO_TOKEN = os.getenv("IPINFO_TOKEN")
    main()