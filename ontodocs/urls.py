from django.conf.urls.defaults import *



urlpatterns = patterns('ontodocs.views',
	
	url(r'^$', 'ontoDocsMain', name='ontodocs_main'),

	)
	



#
# ONTOVIEW URLS
#
#
# urlpatterns = patterns('',
# 	url(r'^ontology$', 'ontoview.views.ontology', name='ontology'),
# 	url(r'^classes$', 'ontoview.views.classes', name='classes'),
# 	url(r'^properties$', 'ontoview.views.properties', name='properties'),
# 	url(r'^individuals$', 'ontoview.views.individuals', name='individuals'),
#
# 	# url(r'^browser$', 'ontoview.views.testinglocal', name='testinglocal'),
#
#
# 	url(r'^about$',
# 		direct_to_template, {
# 			   'template': 'ontoview/pages-site/about.html' ,
# 		   }, name='aboutontoview' 	),
#
# 	# url(r'^$',
# 	# 	direct_to_template, {
# 	# 		   'template': 'ontoview/pages-site/startsearch.html' ,
# 	# 	   },  name='startsearch' ,
# 	# ),
#
# 	url(r'^$', 'ontoview.views.startsearch', name='startsearch'),
#
# )
#
