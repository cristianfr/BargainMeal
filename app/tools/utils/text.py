#Import positive words, negative words and stop_words
from words import *

'''
Text operations commonly used.
'''

def formatting(phrase):
	#Encoding tags from beautifulsoup into utf-8 text.
	return phrase.text.encode('utf-8')

def eliminate_stop_words(word_list):
	#Eliminate words not adding value.
	return [word_filter(word) for word in word_list if (word not in stop_words) and (len(word)>1) and (word_filter(word)!='the')]

def word_filter(word):
	#Standarize output for text analysis.
	aux = word.lower()
	of_chars = ['.',',',';',':','!','?']
	if (len(word)>1) and (aux[-1] in of_chars):
		return aux[:-1]
	else:
		return aux

def noEscapeChars(string):
	return string.replace('"','\\"').replace('\\','-').replace(',','').replace('&','').replace('.','').replace(' ','').replace("'",'').replace('/','')

def markerFormat(name,value,discount, tasty_items,revs):
	#Turn the marker information in to html labels.
	#Tasty items contains (item, number of times counted)
	#item = "menu item  $ Price"
	# Revs contains review, item refered.

	marker_head = "<big>"+name+"</big>"+"<br> <span class='deal'>Get a $"+str(value)+' value for $'+str(discount)+' </span>'
	m_label = marker_head +" <br><table class='menu_table'>"
	for items in tasty_items:
		(item,count_i) = items
		(menu_item,price) = item.split('$')
		m_label+= "<tr><td><span class='menu_item "+noEscapeChars(menu_item)+"'> "+menu_item +"</span></td><td><span class='price'> $"+price+'</span></td></tr>'
	m_label+= '</table>'
	m_revs = "<ul>"
	for rev in revs:
		(review, item) = rev
		(menu_item,price) = item.split('$')
		m_revs +="<li><span class='review "+noEscapeChars(menu_item) +"'>" +review + "</span><br>"
	m_revs+='</ul>'
	return (m_label, m_revs)
	

def main():
	#Test
	example1= 'args!'
	example2= {"text":"Ponzi's"}
	print 'word_filter :  '+example1+' '+word_filter(example1)
	print 'formatting :  '+example2+' '+formatting(example2)

if __name__=='__main__':
	main()