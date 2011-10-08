import os
import ast
from datetime import date, timedelta
from django.db import models
from django.db.models.signals import post_save
from django.template import defaultfilters
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.sites.models import Site
from django.core.files import File
from django.conf import settings
from app.core.models import Project, ProjectActor
from app.steering import fields
from thirdparty.guardian.shortcuts import assign
from thirdparty.xlwt import Workbook, XFStyle, Font

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
    
    def _get_total_replies(self):
        total_replies = 0
        for subject in self.subjects.all():
            total_replies += subject.total_replies
        return total_replies
    total_replies = property(_get_total_replies)
    
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
        try:
            current_iteration = Iteration.objects.get(project=project, current=1)
            new_subjects_list = Subject.objects.filter(iteration=current_iteration, created_at__gte=(today - timedelta(days=3)))
            new_subjects = {}
            total_replies = 0
            subjects = []
            for ns in new_subjects_list:
                subjects.append({
                    'name': ns.name,
                    'state': ns.state.name,
                    'posted_at': str(ns.created_at),
                    'total_replies': ns.total_replies
                })
                total_replies += ns.total_replies
            new_subjects.update({
                'total': len(new_subjects_list),
                'replies': total_replies,
                'subjects': subjects
            })
            open_subjects_list = Subject.objects.filter(iteration=current_iteration, state=State.objects.get(name='Open'))
            open_subjects = {}
            total_replies = 0
            subjects = []
            for ops in open_subjects_list:
                subjects.append({
                    'name': ops.name,
                    'posted_at': str(ops.created_at),
                    'total_replies': ops.total_replies
                })
                total_replies += ops.total_replies
            open_subjects.update({
                'total': len(open_subjects_list),
                'replies': total_replies,
                'subjects': subjects
            })
            closed_solved_subjects_list = Subject.objects.filter(iteration=current_iteration, state=State.objects.get(name='Closed [Solved]'))
            closed_solved_subjects = {}
            total_replies = 0
            subjects = []
            for css in closed_solved_subjects_list:
                subjects.append({
                    'name': css.name,
                    'posted_at': str(css.created_at),
                    'total_replies': css.total_replies
                })
                total_replies += css.total_replies
            closed_solved_subjects.update({
                'total': len(closed_solved_subjects_list),
                'replies': total_replies,
                'subjects': subjects
            })
            closed_unsolved_subjects_list = Subject.objects.filter(iteration=current_iteration, state=State.objects.get(name='Closed [Unsolved]'))
            closed_unsolved_subjects = {}
            total_replies = 0
            subjects = []
            for cus in closed_unsolved_subjects_list:
                subjects.append({
                    'name': cus.name,
                    'posted_at': str(cus.created_at),
                    'total_replies': cus.total_replies
                })
                total_replies += cus.total_replies
            closed_unsolved_subjects.update({
                'total': len(closed_unsolved_subjects_list),
                'replies': total_replies,
                'subjects': subjects
            })
            report = Report(
                date=today, 
                project=project, 
                current_iteration=current_iteration, 
                new_subjects=str(new_subjects), 
                open_subjects=str(open_subjects),
                closed_solved_subjects=str(closed_solved_subjects),
                closed_unsolved_subjects=str(closed_unsolved_subjects)
            )
            report.save()
            for iter in project.iterations.all():
                if iter.rank > report.current_iteration.rank and iter.state != State.objects.get(name='Finished'):
                    report.upcoming_iterations.add(iter)
                if iter.rank < report.current_iteration.rank and iter.state == State.objects.get(name='Finished'):
                    report.completed_iterations.add(iter)
            report.save()
            wb = Workbook()
            sheet = wb.add_sheet('Report')
            style = XFStyle()
            font = Font()
            font.name = 'Arial'
            font.bold = True
            font.height = 300
            style.font = font
            sheet.write(0, 1, project.name + ' - Report - ' + str(report.date), style)
            font.height = 25
            style.font = font
            sheet.write(2, 0, 'Current iteration', style)
            font.height = 200
            style.font = font
            sheet.write(3, 0, 'Name', style)
            sheet.write(3, 1, 'URL', style)
            sheet.write(3, 2, 'Provisional Start', style)
            sheet.write(3, 3, 'Provisional End', style)
            sheet.write(3, 4, 'Effective Start', style)
            sheet.write(3, 5, 'Effective End', style)
            sheet.write(3, 6, 'Total Subjects', style)
            sheet.write(3, 7, 'Total Replies', style)
            font.height = 140
            style.font = font
            sheet.write(4, 0, report.current_iteration.name, style)
            sheet.write(4, 1, 'http://' + Site.objects.get_current().domain + str(report.current_iteration.get_absolute_url()), style)
            sheet.write(4, 2, report.current_iteration.provisional_start_date, style)
            sheet.write(4, 3, report.current_iteration.provisional_end_date, style)
            sheet.write(4, 4, report.current_iteration.effective_start_date, style)
            sheet.write(4, 5, report.current_iteration.effective_end_date, style)
            sheet.write(4, 6, report.current_iteration.total_subjects, style)
            sheet.write(4, 7, report.current_iteration.total_replies, style)
            font.height = 250
            style.font = font
            ns = ast.literal_eval(report.new_subjects)
            sheet.write(6, 0, 'New subjects (posted during the last 3 days)', style)
            sheet.write(6, 1, 'Total subjects: ' + str(ns['total']), style)
            sheet.write(6, 2, 'Total replies: ' + str(ns['replies']), style)
            font.height = 200
            style.font = font
            sheet.write(7, 0, 'Name', style)
            sheet.write(7, 1, 'Posted At', style)
            sheet.write(7, 2, 'State', style)
            sheet.write(7, 3, 'Total Replies', style)
            font.height = 140
            style.font = font
            line = 8
            for s in ns['subjects']:
                sheet.write(line, 0, s['name'], style)
                sheet.write(line, 1, s['posted_at'], style)
                sheet.write(line, 2, s['state'], style)
                sheet.write(line, 3, s['total_replies'], style)
                line += 1
            font.height = 250
            style.font = font
            line += 1
            ops = ast.literal_eval(report.open_subjects)
            sheet.write(line, 0, 'Open subjects', style)
            sheet.write(line, 1, 'Total subjects: ' + str(ops['total']), style)
            sheet.write(line, 2, 'Total replies: ' + str(ops['replies']), style)
            font.height = 200
            style.font = font
            line += 1
            sheet.write(line, 0, 'Name', style)
            sheet.write(line, 1, 'Posted At', style)
            sheet.write(line, 2, 'Total Replies', style)
            font.height = 140
            style.font = font
            line += 1
            for s in ops['subjects']:
                sheet.write(line, 0, s['name'], style)
                sheet.write(line, 1, s['posted_at'], style)
                sheet.write(line, 3, s['total_replies'], style)
                line += 1
            font.height = 250
            style.font = font
            line += 1
            css = ast.literal_eval(report.closed_solved_subjects)
            sheet.write(line, 0, 'Closed [Solved] subjects', style)
            sheet.write(line, 1, 'Total subjects: ' + str(css['total']), style)
            sheet.write(line, 2, 'Total replies: ' + str(css['replies']), style)
            font.height = 200
            style.font = font
            line += 1
            sheet.write(line, 0, 'Name', style)
            sheet.write(line, 1, 'Posted At', style)
            sheet.write(line, 2, 'Total Replies', style)
            font.height = 140
            style.font = font
            line += 1
            for s in css['subjects']:
                sheet.write(line, 0, s['name'], style)
                sheet.write(line, 1, s['posted_at'], style)
                sheet.write(line, 3, s['total_replies'], style)
                line += 1
            font.height = 250
            style.font = font
            line += 1
            cus = ast.literal_eval(report.closed_unsolved_subjects)
            sheet.write(line, 0, 'Closed [Unsolved] subjects', style)
            sheet.write(line, 1, 'Total subjects: ' + str(cus['total']), style)
            sheet.write(line, 2, 'Total replies: ' + str(cus['replies']), style)
            font.height = 200
            style.font = font
            line += 1
            sheet.write(line, 0, 'Name', style)
            sheet.write(line, 1, 'Posted At', style)
            sheet.write(line, 2, 'Total Replies', style)
            font.height = 140
            style.font = font
            line += 1
            for s in cus['subjects']:
                sheet.write(line, 0, s['name'], style)
                sheet.write(line, 1, s['posted_at'], style)
                sheet.write(line, 3, s['total_replies'], style)
                line += 1
            font.height = 250
            style.font = font
            line += 1
            sheet.write(line, 0, 'Completed iterations', style)
            for i in report.completed_iterations.all():
                sheet.write(line, 1, i.name, style)
                line += 1
            line += 1
            sheet.write(line, 0, 'Upcoming iterations', style)
            for i in report.upcoming_iterations.all():
                sheet.write(line, 1, i.name, style)
                line += 1
            wb.save(os.path.join(settings.BASE_DIR, 'tmp/report.xls'))
#            f = open(os.path.join(settings.BASE_DIR, 'tmp/report.xls'), 'w')
#            report_file = File(f)
#            report.file.save(project.name + '_report_' + str(report.date) + '.xls', report_file, save=True)
        except Iteration.DoesNotExist:
            pass
        