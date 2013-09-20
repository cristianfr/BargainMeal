# Extract deals from groupon

import json
import requests


URL = 'https://api.groupon.com/v2/'
API_KEY = {'client_id': '9ca0316d69a65c5bc11c86d49ede8df71eed5784'}


def DealsRequest(r_params):
	#add key to parameters
	r_params.update(API_KEY)
	return requests.get(URL+'deals.json',params =r_params)

def getDeals(location):
	#Connect to googlemaps to identify latitude and longitude of a location string.
	r_params = {'address': location, 'sensor':'true'}
	try:
		g = requests.get('http://maps.googleapis.com/maps/api/geocode/json', params = r_params )
		latlng = g.json()['results'][0]['geometry']['location']
	except IndexError:
		#occurs when I excede google maps calls. Default: San Francisco, CA
		latlng = {'lat': 37.7749295, 'lng':-122.4194155}
	latlng.update({'radius':'50'})
	r = DealsRequest( latlng )
	deals = r.json()['deals']
	return (deals, str(latlng['lat'])+','+str(latlng['lng']) )

def filterFoods(deals):
	food_deals = [deal for deal in deals if (len( set(['foodie','simple-pleasures']) & set([t['id'] for t in deal['dealTypes'] ]) ) >0)  ]
	simple_deal = []
	index = 0
	for deal in food_deals:
		index += 1
		ids = str(index)
		name = deal['merchant']['name']
		title = deal['title']
		value = deal['options'][0]['value']['amount']/100
		discount = value - deal['options'][0]['discount']['amount']/100
		url = deal['dealUrl']		
		simple_deal.append((ids,name,title,value,discount, url,'groupon') )
	return simple_deal

def main():
	# Deals for San Francisco.
	deals = getDeals('San Francisco, CA')
	# Filter the deals that are related to the keywords : foodie or simple-pleasures
	simple_deal = filterFoods(deals)
	with open('food_groupon.json','w') as outfile:
		json.dump(simple_deal, outfile)

if __name__ == '__main__':
	main()