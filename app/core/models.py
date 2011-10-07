from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.template import defaultfilters
from thirdparty.guardian.shortcuts import assign

class Company(models.Model):
    name = models.CharField(u'name', max_length=255, unique=True)
    
    def __unicode__(self):
        return u'%s' % (self.name)
    
    class Meta:
        verbose_name = u'Company'
        verbose_name_plural = u'Companies'

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    company = models.ForeignKey(Company, verbose_name=u'company', null=True, blank=True)
    phone1 = models.CharField(u'phone1', max_length=15, blank=True)
    phone2 = models.CharField(u'phone2', max_length=15, blank=True)

    def __unicode__(self):
        return u'%s\'s profile' % (self.user.get_full_name())
    
    class Meta:
        verbose_name = u'User Profile'
        verbose_name_plural = u'Users Profiles'

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
post_save.connect(create_user_profile, sender=User)

class Project(models.Model):
    name = models.CharField(u'name', max_length=255, unique=True)
    slug = models.SlugField(u'slug', editable=False, blank=True)
    description = models.TextField(u'description')
    
    def save(self, *args, **kwargs):
        self.slug = defaultfilters.slugify(self.name)
        return super(Project, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return u'%s' % (self.name)
 
    @models.permalink
    def get_absolute_url(self):
        return ('project-detail', [str(self.slug)])
    
    class Meta:
        verbose_name = u'Project'
        verbose_name_plural = u'Projects'
        permissions = (
            ('view_project', 'View project'),
        )

def create_group_and_project_permissions(sender, instance, created, **kwargs):
    group, created = Group.objects.get_or_create(name=instance.name)
    assign('view_project', group, instance)
                
post_save.connect(create_group_and_project_permissions, sender=Project)
        
class ProjectRole(models.Model):
    name = models.CharField(u'name', max_length=255, unique=True)
    description = models.TextField(u'description')
    
    def __unicode__(self):
        return u'%s' % (self.name)
    
    class Meta:
        verbose_name = u'Project Role'
        verbose_name_plural = u'Project Roles'

class BusinessRole(models.Model):
    name = models.CharField(u'name', max_length=255, unique=True)
    description = models.TextField(u'description')
    
    def __unicode__(self):
        return u'%s' % (self.name)
    
    class Meta:
        verbose_name = u'Business Role'
        verbose_name_plural = u'Business Roles'
        
class ProjectActor(models.Model):
    project = models.ForeignKey(Project, verbose_name=u'project', related_name=u'actors')
    user = models.ForeignKey(User, verbose_name=u'user')
    project_roles = models.ManyToManyField(ProjectRole, verbose_name=u'project roles')
    business_roles = models.ManyToManyField(BusinessRole, verbose_name=u'business roles', null=True, blank=True)
    
    def _get_full_business_roles(self):
        count = len(self.business_roles.all())
        if count > 0:
            str = u''
            i = 0
            for role in self.business_roles.all():
                i += 1
                str += role.__unicode__()
                if i < count:
                    str += u', '
            return str                
        else:
            return ''
    full_business_roles = property(_get_full_business_roles)
    
    def _get_full_project_roles(self):
        count = len(self.project_roles.all())
        if count > 0:
            str = u''
            i = 0
            for role in self.project_roles.all():
                i += 1
                str += role.__unicode__()
                if i < count:
                    str += u', '
            return str                
        else:
            return ''
    full_project_roles = property(_get_full_project_roles)

    def _get_full_name(self):
        return self.user.get_full_name()
    full_name = property(_get_full_name)
    
    def __unicode__(self):
        if self.full_business_roles:
            return u'%s (%s / %s)' % (self.full_name, self.full_project_roles, self.full_business_roles)
        else:
            return u'%s (%s)' % (self.full_name, self.full_project_roles)

    @models.permalink
    def get_absolute_url(self):
        return ('projectactor-detail', [str(self.project.slug), str(self.id)])
    
    class Meta:
        verbose_name = u'Project Actor'
        verbose_name_plural = u'Project Actors'
        unique_together = ('user', 'project')
        permissions = (
            ('view_projectactor', 'View project actor'),
            ('edit_projectactor', 'Edit project actor'),
        )

def create_projectactor_permissions_and_add_to_group(sender, instance, created, **kwargs):
    group = Group.objects.get(name=instance.project.name)
    instance.user.groups.add(group)
    assign('view_projectactor', group, instance)
    assign('edit_projectactor', instance.user, instance)
        
post_save.connect(create_projectactor_permissions_and_add_to_group, sender=ProjectActor)
