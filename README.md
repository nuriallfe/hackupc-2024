# hackupc-2024


import math

def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers. Use 3956 for miles
    r = 6371

    # Calculate the result
    return c * r

# Example usage
latitude1 = 52.2296756
longitude1 = 21.0122287
latitude2 = 41.8919300
longitude2 = 12.5113300

distance = haversine_distance(latitude1, longitude1, latitude2, longitude2)
print(f"The distance between the two points is {distance:.2f} kilometers.")
