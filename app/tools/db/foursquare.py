from ..API_extract import foursquare as fs
from util import hasher
'''
Foursquare related tables. Tasty dishes, local info, etc.
TastyDishes originally was created for storing the best dishes
of each restaurant. However, later on with the objective of improving
accuracy a new table was created to contain the whole menu.

-- To do --
Given the update one can add the itemId to the fs_foods.
Add a key for review. ReviewId

-- Ultimate to do -- 
Get the keys from a hash function.
'''

def create_foursquare(cur):
	#Create all the relevant foursquare tables.
	cur.execute('DROP TABLE IF EXISTS Restaurants')
	cur.execute("CREATE TABLE Restaurants( \
			idCoupon INT, \
			restaurantId VARCHAR(255) CHARACTER SET utf8,\
			name VARCHAR(255) CHARACTER SET utf8,\
			lat FLOAT,\
			lng FLOAT,\
			rating INT, \
			PRIMARY KEY(restaurantId))")
	cur.execute('DROP TABLE IF EXISTS Reviews')
	cur.execute("CREATE TABLE Reviews( \
			reviewId INT, \
			restaurantId VARCHAR(255) CHARACTER SET utf8, \
			review TEXT CHARACTER SET utf8,\
			mItem VARCHAR(255) CHARACTER SET utf8\
			)")
	cur.execute('DROP TABLE IF EXISTS Tasties')
	cur.execute("CREATE TABLE Tasties( \
			itemId INT,\
			restaurantId VARCHAR(255) CHARACTER SET utf8, \
			mItem VARCHAR(255) CHARACTER SET utf8)")
	cur.execute('DROP TABLE IF EXISTS Menus')
	cur.execute('CREATE TABLE Menus( \
			itemId INT , \
			restaurantId VARCHAR(255) CHARACTER SET utf8, \
			itemName VARCHAR(255) CHARACTER SET utf8, \
			itemPrice FLOAT, \
			itemDesc TEXT, \
			PRIMARY KEY(itemId) )')

	
def populate_foursquare(cur):
	cur.execute("SELECT Coupons.id,name,title,value,discount,url,lat,lng,phone,yelp_r \
		FROM Coupons JOIN Additional ON Coupons.id=Additional.id")
	coupons = cur.fetchall()
	errors = ""
	places, reviews, dishes, mItems =  [],[],[], []
	for coupon in coupons:
		( ids, name, title, value, discount, url, lat, lng, phone, yelp_r) = coupon
		foursquare_id = fs.phone_match( lat, lng, phone, name)
		if foursquare_id[0] == "no_id":
			errors += ','.join(foursquare_id) +'\n'
			continue
		( tasty_items, revs, m_items ) = fs.getTastyM( foursquare_id )		
		for item in m_items:
			itemKey = hasher( item ) #mysql INT limit
			(iName, iDesc, iPrice) = item
			mItems.append( [( itemKey, foursquare_id , iName, iPrice, iDesc)])
		dishes.extend( [ ( hasher(dish) , foursquare_id, dish ) for dish in tasty_items ] )
		reviews.extend( [ ( hasher(review[0]), foursquare_id, review[0], review[1] ) for review in revs ] )
		places.append( ( ids, foursquare_id, name, lat, lng, yelp_r ) )
		with open('populate_foursquare.log','w') as outfile:
			outfile.write(errors)

	cur.executemany('INSERT INTO Menus\
		(itemId, restaurantId, itemName, itemPrice, itemDesc) \
		VALUES (%s,%s,%s,%s,%s)',mItems)

	cur.executemany( "INSERT INTO Tasties(itemId, restaurantId, mItem) \
		VALUES (%s,%s,%s)", dishes )
	cur.executemany( "INSERT INTO Reviews(reviewId, restaurantId, review, mItem) \
		VALUES (%s,%s,%s,%s)", reviews )
	cur.executemany( "INSERT INTO Restaurants(idCoupon, restaurantId, name, lat, lng, rating)\
															 VALUES (%s,%s,%s,%s,%s,%s)",places)
def createRequestsFile(cur):
	cur.execute("SELECT Coupons.id,name,title,value,discount,url,lat,lng,phone,yelp_r \
		FROM Coupons JOIN Additional ON Coupons.id=Additional.id")
	coupons = cur.fetchall()
	line = ""
	for coupon in coupons:
		( ids, name, title, value, discount, url, lat, lng, phone, yelp_r) = coupon
		line += fs.phoneRequest(lat,lng,phone,name)+'\n'
	with open('PhoneRequests.txt', 'w') as outfile:
		outfile.write(line)


