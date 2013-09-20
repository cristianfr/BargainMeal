import json
import numpy as np
import pickle
from ..utils.text import word_filter,eliminate_stop_words
from nltk import word_tokenize
from nltk.probability import FreqDist
from nltk.classify import SklearnClassifier
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

pipeline = Pipeline([('tfidf', TfidfTransformer()),
                     ('chi2', SelectKBest(chi2, k=2000)),
                     ('nb', MultinomialNB())])
classif = SklearnClassifier(pipeline)

def featx(text):
	bag = [word_filter(word) for word in word_tokenize(text)]
	return FreqDist(eliminate_stop_words(bag))

def yelp_data(featx,size):
	path = 'tools/validation_datasets/yelp_academic_dataset_review.json'
	yreviews = [json.loads(line) for line in open(path)]
	negreviews = [review['text'] for review in yreviews[:size] if review['stars']<=3]#3
	posreviews = [review['text'] for review in yreviews[:size] if review['stars']==5]#5
	print str(len(negreviews))+ ' '+ str(len(posreviews))
	negfeats = [(featx(review),'neg') for review in negreviews]
	posfeats = [(featx(review),'pos') for review in posreviews]
	pickle.dump(posfeats, open('tools/text_classifiers/pos_train.pickle','w'))
	pickle.dump(negfeats, open('tools/text_classifiers/neg_train.pickle','w'))
	return (posfeats, negfeats)

def validate(size,classif):
	path = 'tools/validation_datasets/yelp_academic_dataset_review.json'
	yreviews = [json.loads(line) for line in open(path)]
	negreviews = [featx(review['text']) for review in yreviews[-size:] if review['stars']<=3]#3
	posreviews = [featx(review['text']) for review in yreviews[-size:] if review['stars']==5]#5
	print 'validating with the last '+str(size)
	l_pos = np.array(classif.batch_classify(posreviews))
	l_neg = np.array(classif.batch_classify(negreviews))
	print "Confusion matrix:\n%d\t%d\n%d\t%d" % (
          (l_pos == 'pos').sum(), (l_pos == 'neg').sum(),
          (l_neg == 'pos').sum(), (l_neg == 'neg').sum())

def save_classifier( train_data ):
	(pos,neg)= train_data
	classif.train(pos+neg)
	with open('tools/text_classifiers/mbclassif.pickle','w') as outfile:
		pickle.dump(classif, outfile)

def main():
	with open('mbclassif.pickle','r') as infile:
		classif = pickle.load(infile)
	validate(1000,classif)

if __name__=='__main__':
	main()