from datetime import date, timedelta
from django.db import models
from django.db.models.signals import post_save
from django.template import defaultfilters
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.files import File
from django.utils import simplejson as json
from django.core import serializers
from app.core.models import Project, ProjectActor
from app.core import fields
from thirdparty.guardian.shortcuts import assign
from thirdparty.xlwt import Workbook

class Tag(models.Model):
    name = models.SlugField(u'name', unique=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    def save(self, *args, **kwargs):
        self.name = defaultfilters.slugify(self.name)
        return super(Tag, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % (self.name)
    
    class Meta:
        verbose_name = u'Tag'
        verbose_name_plural = u'Tags'

class State(models.Model):
    name = models.CharField(u'name', max_length=255, unique=True)
    type = models.CharField(u'type', max_length=255, editable=False)
    rank = models.PositiveIntegerField(u'rank', unique=True)
    icon = models.ImageField(upload_to='states_icon/')
        
    def __unicode__(self):
        return u'%s' % (self.name)
    
    class Meta:
        verbose_name = u'State'
        verbose_name_plural = u'States'

class Iteration(models.Model):
    name = models.CharField(u'name', max_length=255)
    rank = models.PositiveIntegerField(u'rank')
    description = models.TextField(u'description')
    provisional_start_date = models.DateField(u'provisional start date', blank=True, null=True)
    provisional_end_date = models.DateField(u'provisional end date', blank=True, null=True)
    effective_start_date = models.DateField(u'effective start date', blank=True, null=True)
    effective_end_date = models.DateField(u'effective end date', blank=True, null=True)
    state = models.ForeignKey(State, verbose_name=u'state')
    project = models.ForeignKey(Project, verbose_name=u'project', related_name=u'iterations')
    slug = models.SlugField(u'slug', editable=False, blank=True)
    current = models.BooleanField(u'current iteration')
    
    def save(self, *args, **kwargs):
        self.slug = str(self.project.id) + '-' + defaultfilters.slugify(self.name)
        if self.current == 1:
            for iteration in self.project.iterations.all():
                iteration.current = 0
                iteration.save()
        return super(Iteration, self).save(*args, **kwargs)

    def has_provisional_timetable(self):
        if self.provisional_start_date is not None and self.provisional_end_date is not None:
            return True
        else:
            return False

    def has_effective_timetable(self):
        if self.effective_start_date is not None and self.effective_end_date is not None:
            return True
        else:
            return False

    def has_timetable(self):
        if self.has_provisional_timetable() == True and self.has_effective_timetable() == True:
            return 'complete'
        else:
            if self.has_provisional_timetable() == False and not self.has_effective_timetable() == False:
                return False
            else:
                if self.has_effective_timetable() == True:
                    return 'effective'
                else:
                    return 'provisional'
    
    def _get_total_subjects(self):
        return self.subjects.all().count()
    total_subjects = property(_get_total_subjects)
    
    def __unicode__(self):
        return u'%s' % (self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('iteration-detail', [str(self.project.slug), str(self.slug)])
    
    class Meta:
        verbose_name = u'Iteration'
        verbose_name_plural = u'Iterations'
        unique_together = (('name', 'project'), ('rank', 'project'), ('current', 'project'))
        ordering = ['rank']
        permissions = (
            ('view_iteration', 'View iteration'),
        )

def create_iteration_permissions(sender, instance, created, **kwargs):
    group = Group.objects.get(name=instance.project.name)
    assign('view_iteration', group, instance)
                
post_save.connect(create_iteration_permissions, sender=Iteration)
    
class Subject(models.Model):
    name = models.CharField(u'name', max_length=255)
    content = models.TextField(u'content')
    author = models.ForeignKey(ProjectActor, verbose_name=u'author')
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    state = models.ForeignKey(State, verbose_name=u'state')
    iteration = models.ForeignKey(Iteration, verbose_name=u'iteration', related_name=u'subjects')
    tags = generic.GenericRelation(Tag, verbose_name=u'tags')
    slug = models.SlugField(u'slug', editable=False, blank=True)
    
    def save(self, *args, **kwargs):
        self.slug = str(self.iteration.id) + '-' + defaultfilters.slugify(self.name)
        return super(Subject, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return u'%s' % (self.name)
    
    def _get_total_replies(self):
        return self.replies.all().count()
    total_replies = property(_get_total_replies)

    @models.permalink
    def get_absolute_url(self):
        return ('subject-detail', [str(self.iteration.project.slug), str(self.iteration.slug), str(self.id), str(self.slug)])
    
    class Meta:
        verbose_name = u'Subject'
        verbose_name_plural = u'Subjects'
        permissions = (
            ('view_subject', 'View subject'),
        )
        
def create_subject_permissions(sender, instance, created, **kwargs):
    group = Group.objects.get(name=instance.iteration.project.name)
    assign('view_subject', group, instance)
                
post_save.connect(create_subject_permissions, sender=Subject)
        
class Reply(models.Model):
    title = models.CharField(u'name', max_length=255)
    content = models.TextField(u'content')
    author = models.ForeignKey(ProjectActor, verbose_name=u'author')
    subject = models.ForeignKey(Subject, verbose_name=u'subject', related_name=u'replies')
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return u'%s' % (self.title)

    class Meta:
        verbose_name = u'Reply'
        verbose_name_plural = u'Replies'

class Report(models.Model):
    date = models.DateField(u'date')
    project = models.ForeignKey(Project, verbose_name=u'project', related_name=u'reports')
    current_iteration = models.ForeignKey(Iteration, verbose_name=u'current iteration', related_name='reports_in_which_is_current')
    new_subjects = fields.JSONField(u'new subjects')
    open_subjects = fields.JSONField(u'open subjects')
    closed_solved_subjects = fields.JSONField(u'closed solved subjects')
    closed_unsolved_subjects = fields.JSONField(u'closed unsolved subjects')
    upcoming_iterations = models.ManyToManyField(Iteration, verbose_name=u'upcoming iterations', related_name='reports_in_which_is_upcoming', null=True, blank=True)
    completed_iterations = models.ManyToManyField(Iteration, verbose_name=u'completed iterations', related_name='reports_in_which_is_completed', null=True, blank=True)
    file = models.FileField(u'report file', upload_to='report_files/')
 
    def __unicode__(self):
        return u'Report - %s' % (self.date)
    
    @models.permalink
    def get_absolute_url(self):
        return ('project-detail', [str(self.project.slug), str(self.id)])

    class Meta:
        verbose_name = u'Report'
        verbose_name_plural = u'Reports'
        permissions = (
            ('view_report', 'View report'),
        )

def create_report_permissions(sender, instance, created, **kwargs):
    group = Group.objects.get(name=instance.project.name)
    assign('view_report', group, instance)
                
post_save.connect(create_report_permissions, sender=Report)
        
def create_state(name, rank, type, icon, verbosity=1):
    try:
        state = State.objects.get(name=name)
        updated = False
        if rank != state.rank:
            state.rank = rank
            updated = True
        if type != state.type:
            state.type = type
            updated = True
        if icon != state.icon:
            state.icon = icon
            updated = True
        if updated:
            state.save()
            if verbosity > 1:
                print "Updated %s State" % name
    except State.DoesNotExist:
        State(name=name, rank=rank, type=type, icon=icon).save()
        if verbosity > 1:
            print "Created %s State" % name

def generate_report(project):
    today = date.today()
    try:
        report = Report.objects.get(date=today, project=project)
    except Report.DoesNotExist:
        json_serializer = serializers.get_serializer("json")()
        try:
            current_iteration = Iteration.objects.get(project=project, current=1)
            new_subjects_list = Subject.objects.filter(iteration=current_iteration, created_at__gte=(today - timedelta(days=3)))
            new_subjects = {}
            total_replies = 0
            for ns in new_subjects_list:
                new_subjects[ns.id] = {}
                new_subjects[ns.id].update({
                    'name': ns.name,
                    'state': ns.state.name,
                    'total_replies': ns.total_replies
                })
                total_replies += ns.total_replies
            new_subjects.update({
                'total': len(new_subjects_list),
                'replies': total_replies
            })
            open_subjects_list = Subject.objects.filter(iteration=current_iteration, state=State.objects.get(name='Open'))
            open_subjects = {}
            total_replies = 0
            for ops in open_subjects_list:
                open_subjects[ops.id] = {}
                open_subjects[ops.id].update({
                    'name': ops.name,
                    'total_replies': ops.total_replies
                })
                total_replies += ops.total_replies
            open_subjects.update({
                'total': len(open_subjects_list),
                'replies': total_replies
            })
            closed_solved_subjects_list = Subject.objects.filter(iteration=current_iteration, state=State.objects.get(name='Closed [Solved]'))
            closed_solved_subjects = {}
            total_replies = 0
            for css in closed_solved_subjects_list:
                closed_solved_subjects[css.id] = {}
                closed_solved_subjects[css.id].update({
                    'name': css.name,
                    'total_replies': css.total_replies
                })
                total_replies += css.total_replies
            closed_solved_subjects.update({
                'total': len(closed_solved_subjects_list),
                'replies': total_replies
            })
            closed_unsolved_subjects_list = Subject.objects.filter(iteration=current_iteration, state=State.objects.get(name='Closed [Unsolved]'))
            closed_unsolved_subjects = {}
            total_replies = 0
            for cus in closed_unsolved_subjects_list:
                closed_unsolved_subjects[cus.id] = {}
                closed_unsolved_subjects[cus.id].update({
                    'name': cus.name,
                    'total_replies': cus.total_replies
                })
                total_replies += cus.total_replies
            closed_unsolved_subjects.update({
                'total': len(closed_unsolved_subjects_list),
                'replies': total_replies
            })
            report = Report(
                date=today, 
                project=project, 
                current_iteration=current_iteration, 
                new_subjects=json.dumps(new_subjects), 
                open_subjects=json.dumps(open_subjects),
                closed_solved_subjects=json.dumps(closed_solved_subjects),
                closed_unsolved_subjects=json.dumps(closed_unsolved_subjects)
            )
            report.save()
            for iter in project.iterations.all():
                if iter.rank > report.current_iteration.rank and iter.state != State.objects.get(name='Finished'):
                    report.upcoming_iterations.add(iter)
                if iter.rank < report.current_iteration.rank and iter.state == State.objects.get(name='Finished'):
                    report.completed_iterations.add(iter)
            report.save()
            report_file = Workbook()
            sheet = report_file.add_sheet(project + ' - Report - ' + str(report.date))
            sheet.write(0,1,'Report')
            sheet.write(2,0,'Current iteration')
        except Iteration.DoesNotExist:
            pass
        