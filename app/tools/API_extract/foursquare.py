#Get data from foursquare
from pprint import pprint
import requests

URL = 'https://api.foursquare.com/v2/'
S_URL = 'https:\\/\\/api.foursquare.com\\/v2\\/'
CLIENT_ID = 'GGXQB2N1DWH4MLUTV0HSNIR43DCIPUC30MGRQZ14DA0CBYFI'
CLIENT_SECRET = 'YRIETS4LT5PO2GFLYLN53KLISFAWNQOBM1UNJYENRIQXZ2EM'
auth = {'client_id':CLIENT_ID, 'client_secret':CLIENT_SECRET,'v':20130922}



def localInfo(local_id):
	#Get info for a particular place.
	r = requests.get(URL+'venues/' +str(local_id), params = auth)
	data = r.json()['response']['venue']
	name = data['name'].encode('utf-8')

	try:
		tips = [ t['text'].encode('utf-8') for t in data['tips']['groups'][0]['items'] ]
	except KeyError:
		tips = [""]

	r = requests.get(URL+'venues/' +local_id+'/menu', params = auth)
	menu = r.json()['response']
	mItems = process_menu(menu)
	return (name, tips, mItems)

def phoneMatch(lat,lng,phone,name):
	r_params = {'ll': str(lat)+","+str(lng),'radius':'20', 'intent':'browse'}
	r_params.update(auth)
	
	r = requests.get(URL+'venues/search', params = r_params)
	try:
		shops = r.json()['response']['venues']
	except KeyError:
		print 'oh oh'
		pprint(r.json())
		return ("no_id",name, str(phone), str(lat), str(lng))
	for shop in shops:
		try:
			fs_phone = shop['contact']['phone']
			if phone==fs_phone:
				print "match found - "+name
				return shop['id']
		except KeyError:
			continue
			print 'Key Error '+name
	print "no match - "+name+'-'+phone
	return ("no_id",name, str(phone), str(lat), str(lng))

def process_menu(menu):
	all_items = []
	try:
		for menus in menu['menu']['menus']['items'][0]['entries']['items']:
			for item in menus['entries']['items']:
				try:
					name = item['name'].encode('utf-8')
				except KeyError:
					print "KeyError"
					pprint(item)
					continue
				try:
					price = item['price'].encode('utf-8')
				except KeyError:
					price = -1
				try:
					desc = item['description'].encode('utf-8')
				except KeyError:
					desc = ""
				all_items.append( (name,desc,price) )						
		return all_items
	except KeyError:
		return ("","",0)
	except IndexError:
		return ("","",0)

def main():
	pass

if __name__=='__main__':
	main()