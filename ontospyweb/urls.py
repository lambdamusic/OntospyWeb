from django.conf.urls.defaults import *



urlpatterns = patterns('ontospyweb.views',
	
	url(r'^$', 'ontoDocsMain', name='ontodocs_main'),

	)
	
