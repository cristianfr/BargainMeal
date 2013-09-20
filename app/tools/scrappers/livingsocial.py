#Scrapper for livingsocial site
from bs4 import BeautifulSoup as BS
from urllib import urlopen
from ..utils.text import formatting

HOST = 'https://www.livingsocial.com'
URL = "https://www.livingsocial.com/cities/13-san-jose/food-deals"
LOCAL = "test_ls.html"
CITIES_URL="https://www.livingsocial.com/cities/13-san-jose/more_cities"

def dealExtractorURL(url):
	return dealExtractor(urlopen(url))

def dealExtractor(location):
	soup = BS(location)
	deals = soup.findAll(attrs={"class":"deal-bottom"})
	extracted = []
	for deal in deals:
		try:
			name = formatting( deal.h2 )
			title = formatting( deal.h3 )
			value = formatting( deal.find(attrs={"class":"deal-original"}) ).lstrip('$')
			discount = formatting( deal.find(attrs={"class":"deal-price"}) ).lstrip('$')
			url = deal.find(attrs={"itemprop":"url"})["href"].encode( 'utf-8')
			extracted.append( (name,title,value,discount,url,'livingsocial'))
		except AttributeError:
			continue
	return extracted

def dealStrip(url):
	soup = BS(urlopen(url))
	map_address = soup.find("span",attrs={"class":"directions"}).a['href']
	(lat,lng) = map_address[map_address.find('q=')+2:].split(',')
	phone = soup.find("span",attrs={"class":"phone"}).text
	phone = phone.replace('-','').replace('|','').replace(' ','')
	return (lat,lng, phone, "0")

def cityExtractor():
	soup = BS(urlopen(CITIES_URL))
	set_cities = soup.findAll("ul",attrs={"class":"unstyled cities"})
	links = []
	for cities in set_cities:
		links.extend(cities.findAll("a"))
	#Clean data
	ls_links = [(link.text.encode( 'utf-8'),(HOST+link['href']).encode( 'utf-8')) for link in links if link['href'][0]=='/']
	return ls_links

def main():
	#Offline test
	#deals = dealExtractor(open(LOCAL,'r'))
	deals = dealExtractorURL(URL)
	for deal in deals:
		print deal

if __name__=='__main__':
	main()