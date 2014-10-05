#!/usr/bin/env python
# encoding: utf-8

"""


##################
#  ontodocs
# 
##################


"""





from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.html import strip_tags, escape
from django.contrib import messages

from StringIO import StringIO
import urllib2
import os

from ontoview.models import *
from settings import STATIC_URL

# ps: this uses the local installation
from ontospy_local.ontospy import *

from django.core.cache import cache


# calc abs paths for the **models** folder, assuming it's in the static dir of the ontoview app
thisFilePath = os.path.dirname(os.path.realpath(__file__)).rsplit('/', 1)[0] 
LOCAL_ONTOLOGIES_FOLDER = os.path.join(thisFilePath, 'ontodocs/static/ontodocs/ontologies/')




def get_current_ontology(request, url, startpage=False):
	"""
	If testing in local, loads the ontology file from the local folder.
	Otherwise it just expects a standard rdf-returning URI.
	"""	   
	
	if url.startswith("file://localhost/"):

		# then it's a local file
		realpath = os.path.join(LOCAL_ONTOLOGIES_FOLDER, url.replace("file://localhost/", ""))	 
		# onto = getCached_Onto(request, realpath) 
		onto = Ontology(realpath)

		# hide the physical location set by OntoSpy (so to hide server path infos in display & url parameters)
		onto.ontologyMaskedLocation = url

		# override physical location set by OntosPy (so to allow source download via Django static handler)
		prefix = 'https://' if request.is_secure() else 'http://'
		if STATIC_URL.startswith("http"):
			onto.ontologyPhysicalLocation = STATIC_URL + 'ontoview/models/' + url.replace("file://localhost/", "")
		else:
			onto.ontologyPhysicalLocation = prefix + request.get_host() + STATIC_URL + 'ontoview/models/' + url.replace("file://localhost/", "")
		return onto
	
	else: 
	
		if url.startswith("http://"):
			pass
		else:
			url = "http://" + url
	
		onto = Ontology(url)
		onto.ontologyMaskedLocation = url # what is this for?
	
		# in theory the onto has loaded succesfully - so we save it 
		# (ps: only if the request comes from the startpage!)
		if startpage:
			updateHistory(onto)
	
		return onto
			


# def load_webOnto(ontoInstanceURI):
# 	"""
# 	Similar as getCached_Onto, but removed all caching to make things simple
# 	"""
# 	# get Source file
# 	req = urllib2.Request(ontoInstanceURI)
# 	req.add_header('Accept', 'application/rdf+xml,text/rdf+n3;q=0.9,application/xhtml+xml;q=0.5, */*;q=0.1')
#
# 	res = urllib2.urlopen(req)
#
# 	onto = Ontology(StringIO(res.read()))
# 	res.close()
# 	return onto
#



def get_files():
	mypath = LOCAL_ONTOLOGIES_FOLDER
	onlyfiles = [ "file://localhost/" + f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath,f)) and not f.startswith(".") ]
	return onlyfiles



# October 5, 2014: DEPRECATED 
# in single-html-page version of tool we dont do any caching
def getCached_Onto(request, ontoInstanceURI):
	""" 
	Uses the session/cache backend to avoid reloading an ontology every time
	
	Note that each time we're loading the ontology using an http request - and passing the file directly to rdflib.parse()
	"""
	ONTOVIEW_CACHE = cache.get(ontoInstanceURI)
		
	if not ONTOVIEW_CACHE:		
		printDebug("**NO CACHE** Could not find a cached version of %s..... now retrieving and caching...." % ontoInstanceURI)
		
		# get Source file 
		req = urllib2.Request(ontoInstanceURI)
		req.add_header('Accept', 'application/rdf+xml,text/rdf+n3;q=0.9,application/xhtml+xml;q=0.5, */*;q=0.1')
		
		
		res = urllib2.urlopen(req)
			
		ONTOVIEW_CACHE = res.read()
		cache.set(ontoInstanceURI, ONTOVIEW_CACHE, 300)	 # note: in seconds		
		onto = Ontology(StringIO(ONTOVIEW_CACHE))
		
		
		res.close()
		
	else:
		printDebug("**YES CACHE** Found a cached version of <%s>! " % ontoInstanceURI)
		onto = Ontology(StringIO(ONTOVIEW_CACHE))
	
	return onto






def bootstrapDesc(onto):
	"""
	Extract whatever could be used as a description for the ontology
	"""
	DCTERMS = Namespace('http://purl.org/dc/terms/')		
	DC = Namespace('http://purl.org/dc/elements/1.1/')

	RDFSlabel = "\n".join([x for x in onto.rdfGraph.objects(onto.ontologyURI, RDFS.label)])
	RDFScomment = "\n".join([x for x in onto.rdfGraph.objects(onto.ontologyURI, RDFS.comment)])

	DCdescription = "\n".join([x for x in onto.rdfGraph.objects(onto.ontologyURI, DC.description)])
	DCtitle = "\n".join([x for x in onto.rdfGraph.objects(onto.ontologyURI, DC.description)])
	DCTERMSdescription = "\n".join([x for x in onto.rdfGraph.objects(onto.ontologyURI, DCTERMS.description)])
	DCTERMStitle = "\n".join([x for x in onto.rdfGraph.objects(onto.ontologyURI, DCTERMS.description)])
	
	return	" ".join([DCtitle, DCdescription, DCTERMStitle, DCTERMSdescription, RDFSlabel, RDFScomment])	




def updateHistory(onto):
	""" update the history table once a URI is succesfully loaded into an ontology """
	if onto.ontologyPhysicalLocation:
		try:
			# if the URI already exists, just save so to increase the count
			h = HistoryEntry.objects.get(uri=onto.ontologyPhysicalLocation.strip())
			h.save()
		except:
			# create a new history entry
			h = HistoryEntry(uri=onto.ontologyPhysicalLocation.strip(), description=bootstrapDesc(onto))
			h.save()
	else:
		printDebug("updateHistory: failed as onto.ontologyPhysicalLocation is missing")	



def encodeuri(u):
	"""
	hashes are interpreted differently in urls and ontology uris, so we mask them when passed as args 
	"""
	return u.replace("#", "*hash*")	 # &#x23; in html TODO
def decodeuri(u):
	""" 
	"""
	return u.replace("*hash*", "#")	 


# note: duplicate of templatetagg so to avoid circular imports
def truncchar_inverse(value, arg):
	if len(value) < arg:
		return value
	else:
		x = len(value) - arg
		return '...' + value[x:] 



		

def getDefaultContext(onto):
	"""
	Refactoring stuff that we always want in context
	"""
		
	context = {	  
				'ontoFile' : onto.ontologyMaskedLocation or onto.ontologyPhysicalLocation,
				'ontoFileNoMask' : onto.ontologyPhysicalLocation ,
				'ontoPrettyUri' : onto.ontologyPrettyURI ,
				'namespaces' : onto.ontologyNamespaces ,
				}				
				
	return context







def printDebug(s):
	try:
		print s
	except: 
		pass







##################
#  
#  TREE DISPLAY FUNCTIONS
#
##################



def formatHTML_ClassTreeTable(onto, treedict = None, element = 0):
	""" outputs an html tree representation based on the dictionary we get from the Inspector
	object....

	EG: 
	<table class=h>
	
		<tr>
		  <td class="tc" colspan=4><a href="../DataType">DataType</a>
		  </td>
		</tr>
		<tr>
		  <td class="tc" colspan=4><a href="../DataType">DataType</a>
		  </td>
		</tr>
	
		<tr>
		  <td class="space"></td>
		  <td class="bar"></td>
		  <td class="space"></td>

		  <td>
			<table class=h>
			   <tr><td class="tc" colspan=4><a href="../Boolean">Boolean</a>
					</td>
			   </tr>
			   <tr><td class="tc" colspan=4><a href="../Boolean">Boolean</a>
					</td>
			   </tr>
		   </table>
		  </td>
	  
	  
		 </tr>
	 </table>

	
	Note: The top level owl:Thing never appears as a link.
	
	"""
	ontoFile = onto.ontologyMaskedLocation or onto.ontologyPhysicalLocation
	if not treedict:
		treedict = onto.ontologyClassTree
	stringa = """<table class="h">"""
	for x in treedict[element]:
		if uri2niceString(x, onto.ontologyNamespaces) == "owl:Thing":
			stringa += """<tr>
							<td class="tc" colspan=4><a>%s</a></td>
						  </tr>""" % (truncchar_inverse(uri2niceString(x, onto.ontologyNamespaces), 50))			  
		else:
			stringa += """<tr>
							<td class="tc" colspan=4><a title=\"%s\" class=\"treelinks\" href=\"#%s\">%s</a></td>
						  </tr>""" % (str(x), uri2niceString(x, onto.ontologyNamespaces), truncchar_inverse(uri2niceString(x, onto.ontologyNamespaces), 50))
			
		if treedict.get(x, None):
			stringa += """ <tr>
							<td class="space"></td>
							<td class="bar"></td>
							<td class="space"></td>
							<td>%s</td>
							</tr>""" % formatHTML_ClassTreeTable(onto, treedict, x)
					  
		# stringa += formatHTML_ClassTree(onto, treedict, x)
		# stringa += "</li>"
	stringa += "</table>"
	return stringa
	
	
	




def formatHTML_PropTreeTable(onto, classPredicate, treedict = None, element = 0):
	""" outputs an html tree representation based on the dictionary we get from the Inspector
	object....
	-see above for an example-
	
	if not treedict:
		if classPredicate == "owl.objprop":
			treedict = onto.ontologyObjPropertyTree
		else:
			treedict = onto.ontologyDataPropertyTree
	stringa = "<ul>"
	for x in treedict[element]:
		stringa += "<li><a title=\"%s\" class=\"treelinks propcolor\" href=\"?model=%s&resource=%s\">%s</a>" % (str(x), 
			ontoFile, encodeuri(x) , uri2niceString(x, onto.ontologyNamespaces))
		stringa += formatHTML_PropTree(onto, classPredicate, treedict, x)
		stringa += "</li>"
	stringa += "</ul>"
	return stringa
	
	
	
	"""
	ontoFile = onto.ontologyMaskedLocation or onto.ontologyPhysicalLocation
	if not treedict:
		if classPredicate == "owl.objprop":
			treedict = onto.ontologyObjPropertyTree
		else:
			treedict = onto.ontologyDataPropertyTree

	stringa = """<table class="h propcolor">"""
	for x in treedict[element]:
		stringa += """<tr>
						<td class="tc" colspan=4><a title=\"%s\" class=\"treelinks\" href=\"#%s\">%s</a></td>
					  </tr>""" % (str(x), uri2niceString(x, onto.ontologyNamespaces) , truncchar_inverse(uri2niceString(x, onto.ontologyNamespaces), 50))
			
		if treedict.get(x, None):
			stringa += """ <tr>
							<td class="space"></td>
							<td class="bar"></td>
							<td class="space"></td>
							<td>%s</td>
							</tr>""" % formatHTML_PropTreeTable(onto, classPredicate, treedict, x)
					  
		# stringa += formatHTML_ClassTree(onto, treedict, x)
		# stringa += "</li>"
	stringa += "</table>"
	return stringa
	
	
	
	
#	
#	
# ============= 
# old tree formatting algorithms: work but deprecated 
# ===========	
# 
# 

	

def formatHTML_ClassTree(onto, treedict = None, element = 0):
	""" outputs an html tree representation based on the dictionary we get from the Inspector
	object....

	EG: 
	<ul id="example" class="filetree">
		<li><a class="folder">Folder 2</a>
			<ul>
				<li><a class="folder">Subfolder 2.1</a>
					<ul>
						<li><a class="file">File 2.1.1</a></li>
						<li><a class="file">File 2.1.2</a></li>
					</ul>
				</li>
				<li><a class="file">File 2.2</a></li>
			</ul>
		</li>
		<li class="closed"><a class="folder">Folder 3 (closed at start)</a></li>
		<li><a class="file">File 4</a></li>
	</ul>
	
	Note: The top level owl:Thing never appears as a link.
	
	"""
	ontoFile = onto.ontologyMaskedLocation or onto.ontologyPhysicalLocation
	if not treedict:
		treedict = onto.ontologyClassTree
	stringa = "<ul>"
	for x in treedict[element]:
		if uri2niceString(x, onto.ontologyNamespaces) == "owl:Thing":
			stringa += """<li>%s""" % (uri2niceString(x, onto.ontologyNamespaces))			  
		else:
			stringa += """<li><a title=\"%s\" class=\"treelinks\" href=\"?model=%s&resource=%s\">%s</a>""" % (str(x), 
			ontoFile, encodeuri(x) , uri2niceString(x, onto.ontologyNamespaces))
		stringa += formatHTML_ClassTree(onto, treedict, x)
		stringa += "</li>"
	stringa += "</ul>"
	return stringa



	

def formatHTML_PropTree(onto, classPredicate, treedict = None, element = 0):
	""" outputs an html tree representation based on the dictionary we get from the Inspector
	object....	
	"""
	ontoFile = onto.ontologyMaskedLocation or onto.ontologyPhysicalLocation
	if not treedict:
		if classPredicate == "owl.objprop":
			treedict = onto.ontologyObjPropertyTree
		else:
			treedict = onto.ontologyDataPropertyTree
	stringa = "<ul>"
	for x in treedict[element]:
		stringa += "<li><a title=\"%s\" class=\"treelinks propcolor\" href=\"?model=%s&resource=%s\">%s</a>" % (str(x), 
			ontoFile, encodeuri(x) , uri2niceString(x, onto.ontologyNamespaces))
		stringa += formatHTML_PropTree(onto, classPredicate, treedict, x)
		stringa += "</li>"
	stringa += "</ul>"
	return stringa


	



