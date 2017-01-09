### Intro
OntospyWeb is a tool made for navigating ontologies ('vocabularies') encoded using the RDF family of languages which are part of the W3C Semantic Web standards.

<blockquote>
This project is not supported anymore and soon will be retired. If you are looking for a way to generate docs for an ontology, check out https://github.com/lambdamusic/ontosPy 
</blockquote>

<blockquote>
This project was previously called Django Semantic Browser: https://github.com/lambdamusic/django-semantic-browser.
</blockquote>

Version: 0.9.3

### Installation

1. pre-install the required libraries: `RDFlib` and `ontosPy`:     
https://github.com/RDFLib/rdflib    
https://github.com/lambdamusic/ontosPy    
  
2. copy the app in your django project and load it the usual way in `settings.py`


3. wire up the application in your main urls.py

```python
(r'^ontospyweb/', include('ontospyweb.urls') ),
```	

### Demo

A demo installation is available here: http://hacks.michelepasin.org/ontospy/

### Notes
The folder `..ontospyweb/static/ontospyweb/ontologies/` contains a few ontology files which are displayed on the start page only to logged in users. 

You can add more files to that folder if you want the application to display local files.




