"""from django.db import models
from app.core.models import Project

class Theme(models.Model):
    name = models.CharField(u'name', max_length=255, unique=True)
    project = models.ForeignKey(Project, verbose_name=u'project', related_name=u'actors')
    activated = models.BooleanField(u'activated')
    icon = models.ImageField(upload_to='theme_icons/', blank=True)
    main_color = models.CharField(u'main color', max_length=7)
    second_color = models.CharField(u'second color', max_length=7, blank=True)
    third_color = models.CharField(u'third color', max_length=7, blank=True)
    
    def __unicode__(self):
        if self.full_business_roles:
            return u'%s (%s / %s)' % (self.user.get_full_name(), self.full_project_roles, self.full_business_roles)
        else:
            return u'%s (%s)' % (self.user.get_full_name(), self.full_project_roles)
    
    class Meta:
        verbose_name = u'Theme'
        verbose_name_plural = u'Themes'
        unique_together = ('activated', 'project')"""
