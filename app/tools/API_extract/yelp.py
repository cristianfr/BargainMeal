from ..db import common as db
import requests

'''
Yelp related functions.
'''

HOST = 'http://api.yelp.com/phone_search'
KEY='vKdquZAPRDlSVXve3vZTBA'
auth = { 'ywsid': KEY }

def getRating(phone):
	#Query yelp API for ratings.
	r_params= {'phone':phone}
	r_params.update(auth)
	r = requests.get(HOST, params= r_params)
	rating = r.json()['businesses'][0]['avg_rating']
	return rating

def addRatings():
	#Add the ratings to the database.
	con = db.connect_db()
	cur = con.cursor()
	cur.execute("SELECT id, phone FROM additional WHERE yelp_r=0 ")
	coupons = cur.fetchall()
	for coupon in coupons:
		(the_id, phone) = coupon
		rating = getRating(phone)
		cur.execute("UPDATE additional SET yelp_r = %s WHERE phone = %s"% (rating, phone))
	con.commit()
	cur.close()
	con.close()

def main():
	addRatings()

if __name__=='__main__':
	main()
