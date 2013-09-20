import json
import pickle
import nltk.classify.util
from ..utils.text import word_filter
from nltk.metrics import BigramAssocMeasures
from nltk.classify import NaiveBayesClassifier
from nltk.probability import FreqDist, ConditionalFreqDist

def yelp_feats(review):
	return dict([(word_filter(word),True) for word in nltk.word_tokenize(review)])

def yelp_feats_filter(review,filterwords):
	return dict([(word_filter(word),True) for word in nltk.word_tokenize(review) if word in filterwords])

def train_on_yelp(featx):
	path = 'tools/validation_datasets/yelp_academic_dataset_review.json'
	yreviews = [json.loads(line) for line in open(path)]
	negreviews = [review['text'] for review in yreviews if review['stars']<=3]
	posreviews = [review['text'] for review in yreviews if review['stars']>4]

	negfeats = [(featx(review),'neg') for review in negreviews]
	posfeats = [(featx(review),'pos') for review in posreviews]

	return (posfeats, negfeats)

def train_on_yelp_2(featx,filterwords):
	path = 'yelp_academic_dataset_review.json'
	yreviews = [json.loads(line) for line in open(path)]
	negreviews = [review['text'] for review in yreviews if review['stars']<=3]
	posreviews = [review['text'] for review in yreviews if review['stars']>4]

	negfeats = [(featx(review,filterwords),'neg') for review in negreviews]
	posfeats = [(featx(review,filterwords),'pos') for review in posreviews]

	return (posfeats, negfeats)

def create_classifier(posfeats,negfeats):
	negcutoff = len(negfeats)*9/10
	poscutoff = len(posfeats)*9/10
	 
	trainfeats = negfeats[:negcutoff] + posfeats[:poscutoff]
	testfeats = negfeats[negcutoff:] + posfeats[poscutoff:]
	print 'train on %d instances, test on %d instances' % (len(trainfeats), len(testfeats))
	 
	classifier = NaiveBayesClassifier.train(trainfeats)
	print 'accuracy:', nltk.classify.util.accuracy(classifier, testfeats)
	classifier.show_most_informative_features()

	return classifier

def NaiveBayes():
	#(posfeats, negfeats ) =train_on_movies()
	print "determining the words associated with reviews."
	(posfeats, negfeats ) =train_on_yelp(yelp_feats)
	print "Done"
	#classifier = create_classifier(posfeats, negfeats)
	#Determine all the positive words
	pos_words = []
	for feat in posfeats:
		pos_words.extend(feat[0].keys())
	#Determine all the negative words
	neg_words = []
	for feat in negfeats:
		neg_words.extend(feat[0].keys())
	word_fd = FreqDist()
	label_word_fd = ConditionalFreqDist()
	print str(len(pos_words))+ ': positive words'
	print str(len(neg_words))+ ': negative words'
	for word in pos_words:
	    word_fd.inc(word.lower())
	    label_word_fd['pos'].inc(word.lower())
 
	for word in neg_words:
	    word_fd.inc(word.lower())
	    label_word_fd['neg'].inc(word.lower())

	pos_word_count = label_word_fd['pos'].N()
	neg_word_count = label_word_fd['neg'].N()
	total_word_count = pos_word_count + neg_word_count

	word_scores = {}
	print 'Calculating scores'
	for word, freq in word_fd.iteritems():
	    pos_score = BigramAssocMeasures.chi_sq(label_word_fd['pos'][word],
	        (freq, pos_word_count), total_word_count)
	    neg_score = BigramAssocMeasures.chi_sq(label_word_fd['neg'][word],
	        (freq, neg_word_count), total_word_count)
	    word_scores[word] = pos_score + neg_score
	 
	best = sorted(word_scores.iteritems(), key=lambda (w,s): s, reverse=True)[:10000]
	bestwords = set([w for w, s in best])
	print 'Final Classifier '
	(new_pos, new_neg) = train_on_yelp_2(yelp_feats_filter,bestwords)
	pos_words = []
	for feat in posfeats:
		pos_words.extend(feat[0].keys())
	#Determine all the negative words
	neg_words = []
	for feat in negfeats:
		neg_words.extend(feat[0].keys())
	print str(len(pos_words))+ ': positive words'
	print str(len(neg_words))+ ': negative words'
	classifier = create_classifier(new_pos, new_neg)
	f = open('my_classifier.pickle', 'wb')
	pickle.dump(classifier, f)
	f.close()
