#Get data from foursquare
import nltk
import pickle
import requests
import operator
from pprint import pprint
from ..text_classifiers.multinomialBayes import featx
from ..utils.text import eliminate_stop_words,find_max_similarity,similarity

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
	shops = r.json()['response']['venues']
	for shop in shops:
		try:
			fs_phone = shop['contact']['phone']
			if phone==fs_phone:
				print "match found - "+name
				return shop['id']
		except KeyError:
			continue
	print "no match - "+name+'-'+phone
	return ("no_id",name, str(phone), str(lat), str(lng))

def phoneRequest(lat,lng,phone,name):
	r_params = {'ll': str(lat)+","+str(lng),'radius':'10', 'intent':'browse'}
	r_params.update(auth)
	toreturn = URL+'venues/search?'
	for word in r_params.keys():
		toreturn += word+'='+str(r_params[word]).replace(' ','')+'&'
	return toreturn[:-1]

def venue_match(info):
	#Take a (latlng, name) and return a foursquare id
	(latlng, name) = info
	name_bag = eliminate_stop_words(nltk.word_tokenize(name))
	q_param = ""
	for word in name_bag:
		q_param+= word+"%20"
	r_params = {'ll': latlng,'radius':'1000','query':q_param.rstrip()}
	r_params.update(auth)
	r = requests.get(URL+'venues/search', params = r_params, timeout=6)
	shops = r.json()['response']['groups'][0]['items']
	(data_id, score) = find_max_similarity(name_bag, shops)
	return (data_id, score)

def getTastyM(local_id):
	print 'loading Classifier'
	with open('tools/text_classifiers/mbclassif.pickle','r') as infile:
		classif = pickle.load( infile )
	(name, reviews, m_items) = localInfo(local_id)
	classified_rev = [ ( review , classif.classify( featx( review ) ) ) for review in reviews]
	pos_reviews = [ review.replace('"','\\"') for (review,score) in classified_rev if score=='pos']
	toreturn = []
	r_reviews = []
	for review in pos_reviews:
		(menu_item,found) = match_item3(review,m_items)
		if found:
			toreturn.append( menu_item )
			r_reviews.append( (review, menu_item) )
	return (toreturn ,r_reviews, m_items )

def match_item(review, menu_items):
	text_w = eliminate_stop_words(nltk.word_tokenize(review))
	item_scores = []
	for item in menu_items:
		try:
			(name,desc,price) = item
		except ValueError:
			return (" "," ")
		text_m = eliminate_stop_words(nltk.word_tokenize(name)+nltk.word_tokenize(desc))
		score = similarity(text_w, text_m)
		item_scores.extend( [(name+' $'+str(price) ,score)] )
	item_refered = max(item_scores, key = operator.itemgetter(1))
	return (item_refered[0],item_refered[1]>1)

def match_item2(review,menu_items):
	text_r = eliminate_stop_words( nltk.word_tokenize(review) )
	r_nouns = [word[0] for word in nltk.pos_tag( text_r ) if word[1]=='NN' ]
	r_pnouns = [word[0] for word in nltk.pos_tag( text_r ) if word[1]=='NNP' ]
	item_scores = []
	for item in menu_items:
		try:
			(name,desc,price) = item
		except ValueError:
			return (" "," ")
		text_m = eliminate_stop_words(nltk.word_tokenize(name)+nltk.word_tokenize(desc))
		score = weightedSim( text_m , r_nouns, r_pnouns)
		item_scores.extend( [(name+' $'+str(price) ,score)] )
	item_refered = max(item_scores, key = operator.itemgetter(1))
	return (item_refered[0],item_refered[1]>0)

def match_item3(review,menu_items):
	text_w = eliminate_stop_words( nltk.word_tokenize(review) )
	item_scores = []
	r_nouns = [word[0] for word in nltk.pos_tag( text_w ) if word[1]=='NN' ]
	r_pnouns = [word[0] for word in nltk.pos_tag( text_w ) if word[1]=='NNP' ]
	for item in menu_items:
		try:
			(name,desc,price) = item
		except ValueError:
			return (" ",False)
		text_name = eliminate_stop_words(nltk.word_tokenize(name))
		text_desc = eliminate_stop_words(nltk.word_tokenize(desc))
		score = 2* similarity(text_w, text_name) + similarity(text_w,text_desc) + \
		2*weightedSim(text_name,r_nouns,r_pnouns) + weightedSim(text_desc,r_nouns,r_pnouns)
		item_scores.extend( [(name+' $'+str(price) ,score)] )
	item_refered = max(item_scores, key = operator.itemgetter(1))
	return (item_refered[0],item_refered[1]>3)

def weightedSim(bag_1, nouns, propern):
	#Check the words and score for nouns and proper nouns
	noNouns = len(nouns) - len([noun for noun in nouns if noun not in bag_1])
	noPnouns = len(propern) - len([pnoun for pnoun in propern if pnoun not in bag_1])
	return noNouns + 2*noPnouns

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