#!/usr/bin/env python3

import pandas as pd
import json
import re

def check_gps_coordinates():
    """Check GPS coordinates available in the data"""
    
    print("🗺️ GPS COORDINATES ANALYSIS")
    print("=" * 50)
    
    apps = ['BPS', 'Lineup', 'bspace', 'btech', 'etam']
    
    for app in apps:
        print(f"\n📍 GPS Analysis for {app.upper()}:")
        print("-" * 35)
        
        try:
            # Load sample data
            df = pd.read_csv(f'data_app_posthog_{app}.csv', nrows=1000, on_bad_lines='skip')
            print(f"✅ Loaded {len(df)} sample rows")
            
            gps_fields = ['$geoip_latitude', '$geoip_longitude', '$geoip_city_name', 
                         '$geoip_country_name', '$geoip_subdivision_1_name']
            
            coordinate_data = []
            locations = {}
            
            for i, prop_str in enumerate(df['properties'].head(200)):
                if pd.notna(prop_str) and prop_str != '':
                    try:
                        props = json.loads(prop_str)
                        
                        # Extract from $set nested object if present
                        if '$set' in props and isinstance(props['$set'], dict):
                            gps_data = props['$set']
                        else:
                            gps_data = props
                        
                        lat = gps_data.get('$geoip_latitude')
                        lon = gps_data.get('$geoip_longitude')
                        city = gps_data.get('$geoip_city_name')
                        country = gps_data.get('$geoip_country_name')
                        region = gps_data.get('$geoip_subdivision_1_name')
                        
                        if lat is not None and lon is not None:
                            coordinate_data.append({
                                'lat': lat,
                                'lon': lon,
                                'city': city,
                                'country': country,
                                'region': region
                            })
                            
                            # Track unique locations
                            location_key = f"{city}, {region}, {country}"
                            if location_key not in locations:
                                locations[location_key] = {
                                    'lat': lat, 'lon': lon, 'count': 0
                                }
                            locations[location_key]['count'] += 1
                    
                    except json.JSONDecodeError:
                        # Try regex extraction for malformed JSON
                        lat_match = re.search(r'"\\$geoip_latitude":\s*([+-]?\d*\.?\d+)', prop_str)
                        lon_match = re.search(r'"\\$geoip_longitude":\s*([+-]?\d*\.?\d+)', prop_str)
                        country_match = re.search(r'"\\$geoip_country_name":\s*"([^"]*)"', prop_str)
                        
                        if lat_match and lon_match:
                            coordinate_data.append({
                                'lat': float(lat_match.group(1)),
                                'lon': float(lon_match.group(1)),
                                'country': country_match.group(1) if country_match else None
                            })
            
            print(f"  📊 GPS coordinates found: {len(coordinate_data)}/200 ({len(coordinate_data)/2:.1f}%)")
            
            if coordinate_data:
                # Show coordinate ranges
                lats = [d['lat'] for d in coordinate_data if d['lat'] is not None]
                lons = [d['lon'] for d in coordinate_data if d['lon'] is not None]
                countries = [d['country'] for d in coordinate_data if d['country'] is not None]
                
                if lats and lons:
                    print(f"  🌐 Latitude range: {min(lats):.3f} to {max(lats):.3f}")
                    print(f"  🌐 Longitude range: {min(lons):.3f} to {max(lons):.3f}")
                    
                    # Check if data is in Indonesia (rough bounds)
                    indonesia_coords = any(-11 <= lat <= 6 and 95 <= lon <= 141 for lat, lon in zip(lats, lons))
                    print(f"  🇮🇩 Contains Indonesia coordinates: {'Yes' if indonesia_coords else 'No'}")
                
                if countries:
                    unique_countries = list(set(countries))
                    print(f"  🏳️ Countries found: {unique_countries[:5]}")
                
                # Show top locations
                if locations:
                    top_locations = sorted(locations.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
                    print(f"  📍 Top locations:")
                    for location, data in top_locations:
                        print(f"    • {location}: {data['count']} occurrences")
            else:
                print(f"  ❌ No GPS coordinates found")
                
        except Exception as e:
            print(f"❌ Error analyzing {app}: {e}")

if __name__ == "__main__":
    check_gps_coordinates()