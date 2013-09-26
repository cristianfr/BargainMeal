#!Heuristic For Matching Dishes to Reviews
from ..utils.text import eliminate_stop_words
from nltk import word_tokenize, pos_tag
from operator import itemgetter

def queryMenu(Rid,cur):
	cur.execute('SELECT itemId, itemName, itemDesc FROM Menus WHERE restaurantId = %s', Rid)
	mItems = cur.fetchall()
	return mItems

def queryReviews(Rid, cur):
	cur.execute('SELECT reviewId, review FROM Reviews WHERE restaurantId = %s', Rid)
	return cur.fetchall()

def score(review,mItem):
	(iId, iName, iDesc) = mItem
	sideA = eliminate_stop_words( word_tokenize(review[1]) )
	nameTok = eliminate_stop_words( word_tokenize( iName ))
	descTok = eliminate_stop_words( word_tokenize( iDesc ))
	i_pnouns = [word[0] for word in pos_tag( iName ) if word[1]=='NNP' ]
	rev= review[1].lower()
	nameInReview = (rev.find(iName.lower().strip())>0)*1
	#print ' '.join(nameTok)+' '.join(descTok)+' '.join(i_pnouns)
	return 5*nameInReview+1.5*intersect(sideA,nameTok)+intersect(sideA,descTok)+2*intersect(sideA,i_pnouns)

def intersect(bag1, bag2):
	return len(bag1) - len([word for word in bag1 if word not in bag2])

def itemAssign(Rid, cur):
	mItems = queryMenu(Rid, cur)
	reviews = queryReviews(Rid, cur)
	assignations = []
	for review in reviews:
		scores = []
		for item in mItems:
			iScore = score( review, item) 
			scores.append( (item, iScore) )
		try:
			iRefered = max(scores, key = itemgetter(1))
			if (iRefered[1]>1):
				assignations.append( ( iRefered[0][0],review[0] ) )
			#assignations.append( (review[1], iRefered[0][1], iRefered[0][2], str(iRefered[1]) ) )
		except ValueError:
			continue
	return assignations


