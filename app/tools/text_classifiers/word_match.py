#Collect the reviews and do analysis on them
import nltk
from ..utils.text import *
from ..API_extract import foursquare as fs

def score_reviews(reviews):
	scores = []
	for review in reviews:
		review_token = eliminate_stop_words(nltk.word_tokenize(review))
		pos_score = similarity(positive_words,review_token)
		neg_score = similarity(negative_words,review_token)
		try:
			score = pos_score*1.0/(pos_score + neg_score)-neg_score*1.0/(pos_score + neg_score)
		except ZeroDivisionError:
			score = 0
		scores.extend( [ (review , score ) ] )
	return scores

def get_tasty(local_id):
	local = fs.local_info(local_id)
	reviews = local[3]
	menu = local[4]
	r_scores = score_reviews(reviews)
	m_items = fs.process_menu(menu)
	toreturn = []
	r_reviews = []
	for review in r_scores:
		(text, s) = review
		text_w = eliminate_stop_words(nltk.word_tokenize(text))
		item_scores = []
		for item in m_items:
			try:
				(name,desc,price) = item
			except ValueError:
				return ([(" $ "," ")],[(" "," $ ")])
			text_m = eliminate_stop_words(nltk.word_tokenize(name)+nltk.word_tokenize(desc))
			score = similarity(text_w, text_m)
			item_scores.extend( [( name+' $'+str(price) ,score)] )
		item_refered = max(item_scores, key = operator.itemgetter(1))
		if item_refered[1]>1 and s>0:
			toreturn.append( item_refered[0] )
			r_reviews.append( (text, item_refered) )
	counter = dict([(item, 0) for item in toreturn])
	for item in toreturn:
		counter[item] += 1
	counted_items = [ (item, counter[item]) for item in toreturn]
	print counted_items
	return (counted_items ,r_reviews )

def main():
	#A simpler method
	#NaiveBayes()
	#Case study: 
	local_id ='4ab1cc3ef964a520986a20e3'
	print get_Tasty(local_id)
	


if __name__=='__main__':
	main()	