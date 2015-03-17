#!/usr/bin/python
# -*- coding: utf-8 -*-
# Developed in Python 2.7.5

'''
ISJ Coursework Project - Downloading and Comparing Movie Subtitles Automatically

@author: Jakub Vitasek
@date: 5/17/2014
@contact: xvitas02(at)stud.fit.vutbr.cz
@version: 1.0
@license: GPL
'''

from urllib2 import Request, URLError, urlopen
from bs4 import BeautifulSoup
import sys
from zipfile import *
import os
import argparse
import errno
import re
import math

# Function connecting to a server and returning the page
def openServerConnection(req):
	try:
		page = urlopen(req)
	except URLError, e:
		if hasattr(e, 'reason'):
			print 'The server cannot be reached.'
			print 'Reason: ', e.reason
			exit(1)
		elif hasattr(e, 'code'):
			print 'The server could not fulfill the request.'
			print 'Error code: ', e.code
			exit(1)
	return page

# Function to remove duplicates
def uniq(seq):
	seen = set()
	seen_add = seen.add
	return [ x for x in seq if x not in seen and not seen_add(x)]

# Function to check if a path exists and to create a path
def makeSurePathExists(path):
	try:
		os.makedirs(path)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise

# Function to get all download links for the available subs
def getDownloadLinks(langDict, movieUrl, langIndex):
	# Requesting the URL of the movie
	langFormatted = langDict[langIndex].replace(' ', '-')

	selectedLangUrl = movieUrl + '/' + langFormatted.lower()
	langReq = Request(selectedLangUrl)

	# Using the function above to connect to the server
	langPage = openServerConnection(langReq)

	# Reading the source code of the movie page
	langContent = langPage.read()
	soup = BeautifulSoup(langContent)

	# Getting all the urls
	langTags = soup.findAll('td', class_="a1")
	langTags = str(langTags)
	return re.findall('<a href="(.*)">', langTags)


# Function to download subs
def downloadSubs(langDict, langIndex, langUrls):
	# Changing CWD to better organize the files
	os.chdir(langDict[langIndex])
	# A variable to keep track of the unzipped files
	unzipped = 0

	# A loop to download every subtitle file and unzip it
	for i, url in enumerate(langUrls):
		finalSubPageUrl = 'http://subscene.com' + url
		finalSubPageReq = Request(finalSubPageUrl)

		# Using the function above to connect to the server
		finalSubPage = openServerConnection(finalSubPageReq)

		# Reading the source code of the final subtitle page
		finalSub = finalSubPage.read()
		soup = BeautifulSoup(finalSub)

		# Getting the download link
		downloadButTag = soup.findAll('a', id="downloadButton")
		downloadButTag = str(downloadButTag)
		downloadUrl = 'http://subscene.com' + str(re.findall('<a class=".*" href="(.*?)"', downloadButTag))
		# Getting rid of list leftovers (due to the string conversion)
		downloadUrl = re.sub(r'\[\'', '', downloadUrl)
		downloadUrl = re.sub(r'\'\]', '', downloadUrl)
		
		# The download process
		fileName = downloadUrl.split('/')[-1]
		u = urlopen(downloadUrl)
		f = open(fileName + '.zip', 'wb')
		meta = u.info()
		fileSize = int(meta.getheaders("Content-Length")[0])
		fileSizeDl = 0
		block_sz = 8192
		while True:
			buffer = u.read(block_sz)
			if not buffer:
				break

			fileSizeDl += len(buffer)
			f.write(buffer)
			status = r"%10d  [%3.2f%%]" % (fileSizeDl, fileSizeDl * 100. / fileSize)
			status = status + chr(8)*(len(status)+1)
			#print status,

		f.close()

		# Unzipping the downloaded file
		try:
			with ZipFile(fileName + '.zip') as zf:
				zf.extractall()
				unzipped += 1
		except(BadZipfile), e:
			pass

		# Removing unzipped .zip files
		os.remove(fileName + '.zip')

	# Changing the CWD back to the project folder
	os.chdir('../')
	# Returning the amount of unzipped files
	return unzipped

# The function to calculate the similarity in percents
def getSimilarity(val, val2):
	# If val is 100%
	if val > val2:
		percentage = ((val2*100)/val)
	# If val2 is 100%
	elif val2 > val:
		percentage = ((val*100)/val2)
	return percentage


###########################################
### 		HANDLING ARGUMENTS  		###
###########################################

# Initiating the parser
parser = argparse.ArgumentParser()
# Due to the way this project was implemented
# there cannot be more arguments that -m
parser.add_argument('-m', '--movie', help='title of the movie (enclose in quotes)')
args = parser.parse_args()


###########################################
### 		SELECTING THE MOVIE 		###
###########################################

print '--- MOVIE TITLE ---'

# If the movie name was passed through arguments
if args.movie:
	movieName = args.movie
	print 'Movie title passed through arguments: %s' % movieName
# Asking the user for the movie name
else:
	movieName = raw_input('Enter the name of the movie: ')

# Formatting the name for search query
movieName = movieName.replace(' ', '+')

# Requesting the URL (COULD BE A FUNCTION)
searchUrl = 'http://subscene.com/subtitles/title?q=' + movieName.lower()
searchReq = Request(searchUrl)

# Using the function above to connect to the server
searchPage = openServerConnection(searchReq)

# Reading the source code of the search results page
searchResults = searchPage.read()
soup = BeautifulSoup(searchResults)

# Getting all the possible matches
allMovieTitlesTag = soup.findAll('div', class_="title")
allMovieTitlesTag = str(allMovieTitlesTag)
allTitles = re.findall('<.*>(.*)</a>', allMovieTitlesTag)
allUrls = re.findall('<a href="(.*)">.*</a>', allMovieTitlesTag)

# If no movies match the search query
if(len(allTitles) == 0):
	print 'No movie found!'
	exit(0)

# Removing duplicates
titles = uniq(allTitles)
urls = uniq(allUrls)

# Listing all movies found in the search query
print '\n--- POSSIBLE MATCHES ---'
for i, title in enumerate(titles):
	print '[' + str(i) + ']' + ' = ' + title

# Letting the user decide which movie to choose
print '\n--- PICK YOUR MOVIE ---'
movieIndex = int(raw_input('Enter the [INDEX] of your movie: '))

# Validating for the bounds of the index
if movieIndex > (len(titles)-1):
	print 'The index is out of bounds!'
	exit(1)

print 'You picked: %s' % titles[movieIndex]


###########################################
###		   GETTING THE LANGUAGE			###
###########################################

# Getting the selected movie's URL from the urls list
selectedMovieUrl = urls[movieIndex]

# Requesting the URL of the movie
movieUrl = 'http://subscene.com' + selectedMovieUrl
movieReq = Request(movieUrl)

# Using the function above to connect to the server
moviePage = openServerConnection(movieReq)

# Reading the source code of the movie page
movieContent = moviePage.read()
soup = BeautifulSoup(movieContent)

# Getting all the possible matches
allLangs = [s.get_text().strip() for s in soup.find_all('span', class_=True)]

# Getting rid of redundant data
del allLangs[0]
del allLangs[0]
del allLangs[0]
del allLangs[0]
del allLangs[-1]

# Getting rid of duplicates
languages = uniq(allLangs)

# Creating a dictionary of languages
langDict = {}
for i, language in enumerate(languages):
	langDict[i] = language

# Listing all available languages
print '\n--- AVAILABLE LANGUAGES ---'
for i, language in enumerate(languages):
	print '[' + str(i) + ']' + ' = ' + language

# Letting the user decide which first language to pick
print '\n--- PICK YOUR FIRST LANGUAGE ---'
firstLangIndex = int(raw_input('Enter the [INDEX] of your first language: '))
print 'First language: %s' % langDict[firstLangIndex]

# Letting the user decide which second language to pick
print '\n--- PICK YOUR SECOND LANGUAGE ---'
secondLangIndex = int(raw_input('Enter the [INDEX] of your second language: '))
print 'Second language: %s' % langDict[secondLangIndex]

# Creating the folder for the first lang subs
makeSurePathExists(langDict[firstLangIndex])
# Creating the folder for the second lang subs
makeSurePathExists(langDict[secondLangIndex])

print '\n--- FOLDERS CREATED ---'
print '[ ' + langDict[firstLangIndex] + ' ]'
print '[ ' + langDict[secondLangIndex] + ' ]'


###########################################
### 	   GETTING THE SUB LINKS		###
###########################################

# Using a function specified above to get the download links
firstLangUrls = getDownloadLinks(langDict, movieUrl, firstLangIndex)
secondLangUrls = getDownloadLinks(langDict, movieUrl, secondLangIndex)


###########################################
### 		 DOWNLOADING SUBS	 		###
###########################################

print '\n--- DOWNLOADING... (takes a while) ---'

# The return value is the amount of unzipped files
unzippedFirst = downloadSubs(langDict, firstLangIndex, firstLangUrls)
unzippedSecond = downloadSubs(langDict, secondLangIndex, secondLangUrls)

print '\n--- FINISHED ---'

# Printing out the amount of unzipped files respectively to each language
print '[' + str(unzippedFirst) + '] ' + langDict[firstLangIndex]
print '[' + str(unzippedSecond) + '] ' + langDict[secondLangIndex]


###########################################
###    COMPARING SUBS BASED ON SIZE 	###
###########################################

# Getting the filenames of all the subs downloaded
fileNameListFirst = os.listdir(langDict[firstLangIndex])
fileNameListSecond = os.listdir(langDict[secondLangIndex])

# Key -> filename, Value -> filesize
nameAndSize1 = {}
nameAndSize2 = {}

# Filling up the directories specified above
for name in fileNameListFirst:
	nameAndSize1[name] = os.path.getsize(langDict[firstLangIndex] + '/' + name)
for name in fileNameListSecond:
	nameAndSize2[name] = os.path.getsize(langDict[secondLangIndex] + '/' +name)

# Finding the closest match in filesize between the two languages
size1 = 0
size2 = 0
distance = 0
for key in nameAndSize1:
	value = nameAndSize1[key]
	# The minimum is being set to the maximum integer value
	minimum = sys.maxint
	closest_key = None
	# for every file we calculate difference in their sizes,
	# if difference is smaller than our minimum put that
	# value in minimum and save corresponding key
	for key2 in nameAndSize2:
		value2 = nameAndSize2[key2]
		# Getting the abs. value of the difference of the two values
		distance = abs(value-value2)
		if distance < minimum:
			minimum = distance
			# Taking notes of the final sizes to calculate
			# the similarity
			size1 = nameAndSize1[key]
			size2 = nameAndSize2[key2]
			closest_key = key
			closest_key2 = key2

if distance == 0:
	sizeSimilarity = 100
else:
	sizeSimilarity = getSimilarity(size1, size2)

print '\n--- THE BEST FILESIZE MATCH ---'

print '%s: %s\n%s: %s\nSimilarity: [%s%%]' % (langDict[firstLangIndex], closest_key, langDict[secondLangIndex], closest_key2, str(sizeSimilarity))
