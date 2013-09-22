#Get data from foursquare
import nltk
import pickle
import requests
import operator
from ..text_classifiers.multinomialBayes import featx
from ..utils.text import eliminate_stop_words,find_max_similarity,similarity

URL = 'https://api.foursquare.com/v2/'
CLIENT_ID = 'CB2ROLMTNIOWPZUK5FJBT1NISJDYXAZMWNXQIFZIGYDIHHEH'
CLIENT_SECRET = '4RFUXZKCFZBCQQLZUM522PKCW4MHWHI1PUU25U2UNWBH0IKR'
auth = {'client_id':CLIENT_ID, 'client_secret':CLIENT_SECRET}



def local_info(local_id):
	#Get info for a particular place.
	r = requests.get(URL+'venues/' +local_id, params = auth)
	data = r.json()['response']['venue']
	name = data['name'].encode('utf-8')

	try:
		tips = [ t['text'].encode('utf-8') for t in data['tips']['groups'][0]['items'] ]
	except KeyError:
		tips = [""]
	try:
		rating = data['rating']
	except KeyError:
		rating = "-1"
	try:
		status = data['hours']['status'].encode('utf-8')
	except KeyError:
		status = "Unknown"

	#Get menu
	r = requests.get(URL+'venues/' +local_id+'/menu', params = auth)
	menu = r.json()['response']
	return (name, rating, status, tips, menu)

def phone_match(lat,lng,phone,name):
	r_params = {'ll': str(lat)+","+str(lng),'radius':'10'}
	r_params.update(auth)
	r = requests.get(URL+'venues/search', params = r_params)
	shops = r.json()['response']['groups'][0]['items']
	for shop in shops:
		try:
			fs_phone = shop['contact']['phone']
			if phone==fs_phone:
				print "match found"
				return shop['id'].encode('utf-8')
		except KeyError:
			continue
	print "no match"
	return "no_id"

def venue_match(info):
	#Take a (latlng, name) and return a foursquare id
	(latlng, name) = info
	name_bag = eliminate_stop_words(nltk.word_tokenize(name))
	q_param = ""
	for word in name_bag:
		q_param+= word+"%20"
	r_params = {'ll': latlng,'radius':'100000','query':q_param.rstrip()}
	r_params.update(auth)
	r = requests.get(URL+'venues/search', params = r_params)
	shops = r.json()['response']['groups'][0]['items']
	(data_id, score) = find_max_similarity(name_bag, shops)
	return (data_id, score)

def getTastyM(local_id):
	with open('tools/text_classifiers/mbclassif.pickle','r') as infile:
		classif = pickle.load( infile )
	(name, rating, status, reviews, menu) = local_info(local_id)
	classified_rev = [ ( review , classif.classify( featx( review ) ) ) for review in reviews]
	pos_reviews = [ review.replace('"','\\"') for (review,score) in classified_rev if score=='pos']
	m_items = process_menu(menu)
	toreturn = []
	r_reviews = []
	for review in pos_reviews:
		(menu_item,found) = match_item3(review,m_items)
		if found:
			toreturn.append( menu_item )
			r_reviews.append( (review, menu_item) )
	return (toreturn ,r_reviews )

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
					desc = item['description'].encode('utf-8')
					price = item['price'].encode('utf-8')
				except KeyError:
					print "KeyError: "+item
					continue
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