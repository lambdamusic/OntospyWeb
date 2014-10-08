from django.db import models
from django.contrib import admin

import datetime
from settings import printdebug

EXTRA_SAVING_ACTIONS = True




class HistoryEntry(models.Model):
	"""(HistoryEntry description)"""
	uri = models.CharField(max_length=350, )	
	description = models.TextField(blank=True, verbose_name="description")
	pubdate = models.DateTimeField(null=True, blank=True, verbose_name="date added" )
	score = models.IntegerField(blank=True, null=True)

	class Admin(admin.ModelAdmin):
		list_display = ('id', 'uri', 'pubdate', 'score')
		search_fields = ('uri',)
		list_filter = ('pubdate', )
		
	def save(self, force_insert=False, force_update=False):
		if EXTRA_SAVING_ACTIONS:
			super(HistoryEntry, self).save(force_insert, force_update)
			self.pubdate = datetime.datetime.today()
			if self.score:
				self.score = self.score + 1
			else:
				self.score = 1
		super(HistoryEntry, self).save(force_insert, force_update)	
			
	class Meta:
		verbose_name_plural="HistoryEntry"
		verbose_name = "HistoryEntry"
		ordering = ["id"]

	def __unicode__(self):
		return "HistoryEntry %d" % self.id


# TODO: put in admin.py
admin.site.register(HistoryEntry, HistoryEntry.Admin)


