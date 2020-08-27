bay_area = ['Santa Clara', 'San Mateo', 'San Francisco', 'Marin', 'Sonoma', 
            'Napa', 'Solano', 'Contra Costa', 'Alameda']

sierras_and_cascades = ['Modoc','Lassen', 'Plumas', 'Sierra', 'Nevada', 'Placer', 'El Dorado', 
            'Amador', 'Alpine', 'Calaveras', 'Tuolumne', 'Mariposa', 'Mono', 'Inyo', 'Madera']

socal = ['Imperial', 'Kern', 'Los Angeles', 'Orange', 'Riverside', 'San Bernardino',
         'San Diego', 'Santa Barbara', 'San Luis Obispo', 'Ventura']

#def get_region(county):
#    if county in bay_area:
#        return "San Francisco Bay Area"
#    elif county in socal:
#        return "Southern California"
#    elif county in sierras:
#        return 'Sierra or Cascades'
#    else:
#        return 'Other'
    
def get_county_color(county):
    """
    Helper function to fix colors for a given region while plotting
    """
    if county in bay_area:
        return "teal"
    elif county in socal:
        return "orange"
    elif county in sierras_and_cascades:
        return 'pink'
    elif county == 'Multiple Counties':
        return 'maroon'
    else:
        return 'grey'
