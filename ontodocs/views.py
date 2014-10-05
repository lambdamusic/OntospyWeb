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
from django.core.cache import cache

from StringIO import StringIO
import urllib2
import os

from ontoview.models import *
from settings import STATIC_URL

from ontutils import *


# ps: this uses the local installation
from ontospy_local.ontospy import *


		


def ontoDocsMain(request):
	""" 
	View that handle all initial requests
	- if a uri is passed and is valid, shows the ontology data as a single html page
	- else, return the initial start page (default)
	"""
	
	SHOW_SEARCH_PAGE = True
	
	if request.GET.get('uri', ''):	

		try:
			onto = get_current_ontology(request, request.GET.get('uri', ''), request.GET.get('startpage', ''))
			SHOW_SEARCH_PAGE = False
		except:# catch all errors while trying to load the ontology
			_message = "Sorry! The file you tried to load does not look like a valid RDF/OWL ontology."		
			messages.error(request, _message)



	if SHOW_SEARCH_PAGE:
		if request.user.is_authenticated():
			# show local files only to admin user
			local_ontologies = get_files()	# local files don't get added to history panel!
		else:
			local_ontologies = []
	
		history = HistoryEntry.objects.all().order_by('-pubdate')
		
		context = {	  
					'local_ontologies' : local_ontologies ,		
					'history' : history ,		
					'LOCAL_ONTOLOGIES_FOLDER' : LOCAL_ONTOLOGIES_FOLDER,
					}
		return render_to_response('ontodocs/startsearch.html', 
									context,
									context_instance=RequestContext(request))
	

	# If RETURN_SEARCH_PAGE = False, build up the docs
	
	context = getDefaultContext(onto)
	
	context.update(get_ontology(onto))
	context.update(get_classes(onto))
	context.update(get_objProperties(onto))
	context.update(get_dataProperties(onto))
	context.update(get_individuals(onto))
	
	return render_to_response('ontodocs/docspage.html', 
								context,
								context_instance=RequestContext(request))






# ===========
# methods to extract data for the tabs
# ===========



def get_ontology(onto):
	""""""
	ontologyAnnotations = onto.ontologyAnnotations(niceURI=True, excludeProps=False, excludeBNodes = False,)
		
	context = {	  
				'stats' : onto.ontologyStats() ,
				'toplayer' : [onto.classRepresentation(aClass) for aClass in onto.toplayer] ,
				# 'sourcecode1' : onto.serializeOntologyGraph("turtle").strip() ,
				# 'sourcecode2' : onto.serializeOntologyGraph("xml").strip() ,				
				'ontologyAnnotations' : ontologyAnnotations,	
											
				}

	return context



	
def get_classes(onto):
	""" 
	View that ..
	"""

	# CLASS TREE
	context = {	  
				# 'classtree' : formatHTML_ClassTree(onto) ,
				'classtreeTable' : formatHTML_ClassTreeTable(onto) ,
				}
				
	classesData = []
		
	for aClass in onto.allclasses:
		# CLASS INFO
		supers = onto.classAllSupers(aClass)
		# alltree = supers + [aClass]
		# subs = onto.classDirectSubs(aClass, sortUriName = True)
		# siblings = onto.classSiblings(aClass, sortUriName = True)			 
		
		_exclude_ = [RDF.type, RDFS.isDefinedBy, RDFS.subClassOf]  # ,		
		# alltriples = entityTriples(aClass, niceURI=True, excludeProps=_exclude_, excludeBNodes = False,) 
			
		alltriples = entityTriples(onto.rdfGraph, aClass, excludeProps=_exclude_, excludeBNodes = False,)
		alltriples = [(uri2niceString(y, onto.ontologyNamespaces), z) for y,z in alltriples]
										
		domain_info = onto.classDomainFor(aClass, inherited = True)		
		# explode the domain info nested list so to include all prop/class representation
		allDomainProperties = []
		for tupl in domain_info:
			classExploded = onto.classRepresentation(tupl[0])
			propExploded = [onto.propertyRepresentation(p) for p in tupl[1]]
			allDomainProperties.append((classExploded, propExploded))
		
		mydict = {	  
					'class' : onto.classRepresentation(aClass) ,
					'supers' : [onto.classRepresentation(x) for x in supers] ,
					# 'alltree' : [onto.classRepresentation(x) for x in alltree] ,
					# 'subs' : [onto.classRepresentation(x) for x in subs] ,
					# 'siblings' : [onto.classRepresentation(x) for x in siblings] ,
					'allDomainProperties' : allDomainProperties ,
					# 'instances' : onto.classInstances(aClass) ,
					'alltriples' : alltriples,
					}
		
		classesData += [mydict]

	context.update({'classesData' : classesData})
	return context













def get_objProperties(onto):
	""" 
	Return the properties info 
	"""

	objPropertiesData = []
	
	#PROPERTY TREE	
	context = {	  
				'objpropertiesTree' : formatHTML_PropTreeTable(onto, classPredicate="owl.objprop") ,
				}
	
	for aProp in onto.allobjproperties:
		
		# PROPERTY INFO
		supers = onto.propertyAllSupers(aProp)
		# alltree = supers + [aProp]
		# subs = onto.propertyDirectSubs(aProp, sortUriName = True)

		# alltriples = entityTriples(aProp, niceURI=True, excludeProps=[RDF.type, RDFS.subPropertyOf, RDFS.isDefinedBy, RDFS.domain, RDFS.range], excludeBNodes = False,) 
		
		_exclude_ = [RDF.type, RDFS.subPropertyOf, RDFS.isDefinedBy, RDFS.domain, RDFS.range]
		alltriples = entityTriples(onto.rdfGraph, aProp, excludeProps=_exclude_, excludeBNodes = False,)
		alltriples = [(uri2niceString(y, onto.ontologyNamespaces), z) for y,z in alltriples]
		
		mydict = {	  
					'prop' : onto.propertyRepresentation(aProp) ,
					'supers' : [onto.propertyRepresentation(x) for x in supers] ,
					# 'subs' : [onto.propertyRepresentation(x) for x in subs] ,
					'alltriples' : alltriples,
					}
		
		objPropertiesData += [mydict]

						
	context.update({'objPropertiesData' : objPropertiesData})	
	return context







def get_dataProperties(onto):
	""" 
	Return the properties info 
	"""

	dataPropertiesData = []
	
	#PROPERTY TREE	
	context = {	  
				'datapropertiesTree' : formatHTML_PropTreeTable(onto, classPredicate="owl.dataprop") ,
				}
	
	for aProp in onto.alldataproperties:
		
		# PROPERTY INFO
		supers = onto.propertyAllSupers(aProp)
		# alltree = supers + [aProp]
		# subs = onto.propertyDirectSubs(aProp, sortUriName = True)

		# alltriples = entityTriples(aProp, niceURI=True, excludeProps=[RDF.type, RDFS.subPropertyOf, RDFS.isDefinedBy, RDFS.domain, RDFS.range], excludeBNodes = False,) 
		
		_exclude_ = [RDF.type, RDFS.subPropertyOf, RDFS.isDefinedBy, RDFS.domain, RDFS.range]
		alltriples = entityTriples(onto.rdfGraph, aProp, excludeProps=_exclude_, excludeBNodes = False,)
		alltriples = [(uri2niceString(y, onto.ontologyNamespaces), z) for y,z in alltriples]
		
		mydict = {	  
					'prop' : onto.propertyRepresentation(aProp) ,
					'supers' : [onto.propertyRepresentation(x) for x in supers] ,
					# 'subs' : [onto.propertyRepresentation(x) for x in subs] ,
					'alltriples' : alltriples,
					}
		
		dataPropertiesData += [mydict]

						
	context.update({'dataPropertiesData' : dataPropertiesData})	
	return context






def get_individuals(onto):
	""" 
	
	"""

	# ALL INDIVIDUALS	
	
	context = {	  
				'instances' : [onto.instanceRepresentation(instance) for instance in onto.allinstances] ,
				}

	if False:
		if onto.instanceFind(resource):
			instance = onto.instanceFind(resource)[0]
			instance_repr = onto.instanceRepresentation(instance)
			siblings = onto.instanceSiblings(instance)
			# triples = entityTriples(instance, excludeProps=[RDF.type, RDFS.comment])
			# INDIVIDUAL INFO
			context = {	  
						'instance' : instance_repr ,
						'siblings' : siblings ,
						'triples' : [(onto.propertyRepresentation(p), o) for p,o in instance_repr['alltriples']] ,
						}
			defaul_context = getDefaultContext(onto)
			context.update(defaul_context)
		else:
			# ERROR MSG
			context = {	  
						'resource404' : True ,
						'resource' : resource ,
						}
			defaul_context = getDefaultContext(onto)
			context.update(defaul_context)
							
	return context




