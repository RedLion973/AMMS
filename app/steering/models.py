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
from thirdparty.xlwt import Workbook, XFStyle, Font, Alignment, Formula, Pattern

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
    
    def generate_excel_file(self):
        wb = Workbook()
        sheet_title = self.project.name + ' - Report'
        sheet = wb.add_sheet(sheet_title)
        # styles & fonts definitions
        pattern = Pattern()
        pattern.pattern = pattern.SOLID_PATTERN
        pattern.pattern_fore_color = 0x09
        pattern.pattern_back_color = 0x3A
        align_center = Alignment()
        align_center.horz = Alignment.HORZ_CENTER
        align_center.vert = Alignment.VERT_CENTER
        align_left = Alignment()
        align_left.horz = Alignment.HORZ_LEFT
        align_left.vert = Alignment.VERT_CENTER
        align_right = Alignment()
        align_right.horz = Alignment.HORZ_RIGHT
        align_right.vert = Alignment.VERT_CENTER
        title = XFStyle()
        font_title = Font()
        font_title.name = 'Arial'
        font_title.bold = True
        font_title.height = 400
        font_title.colour_index = 0x3A
        title.font = font_title
        title.alignment = align_right
        title_date = XFStyle()
        title_date.num_format_str = 'DD-MM-YY'
        title_date.font = font_title
        title_date.alignment = align_left
        subtitle = XFStyle()
        font_subtitle = Font()
        font_subtitle.name = 'Arial'
        font_subtitle.bold = True
        font_subtitle.height = 300
        font_subtitle.colour_index = 0x3A
        subtitle.font = font_subtitle
        subtitle.alignment = align_right
        header = XFStyle()
        font_header = Font()
        font_header.name = 'Arial'
        font_header.bold = True
        font_header.height = 250
        font_header.colour_index = 0x09
        header.font = font_header
        header.alignment = align_center
        header.pattern = pattern
        normal = XFStyle()
        font_normal = Font()
        font_normal.name = 'Arial'
        font_normal.height = 200
        normal.font = font_normal
        normal.alignment = align_center
        normal_date = XFStyle()
        normal_date.num_format_str = 'M/D/YY'
        normal_date.font = font_normal
        normal_date.alignment = align_center
        normal_datetime = XFStyle()
        normal_datetime.num_format_str = 'M/D/YY h:mm'
        normal_datetime.font = font_normal
        normal_datetime.alignment = align_center
        
        # writing
        n = "HYPERLINK"
        sheet.write(0, 1, self.project.name + ' - Report:', title)
        sheet.write(0, 2, self.date, title_date)
        sheet.write(2, 0, 'Current iteration', subtitle)
        sheet.write(4, 0, 'Name', header)
        sheet.write(4, 1, 'URL', header)
        sheet.write(4, 2, 'Provisional Start', header)
        sheet.write(4, 3, 'Provisional End', header)
        sheet.write(4, 4, 'Effective Start', header)
        sheet.write(4, 5, 'Effective End', header)
        sheet.write(4, 6, 'Total Subjects', header)
        sheet.write(4, 7, 'Total Replies', header)
        sheet.write(5, 0, self.current_iteration.name, normal)
        sheet.write(5, 1, Formula(n + '("http://' + Site.objects.get_current().domain + str(self.current_iteration.get_absolute_url()) + '")'), normal)
        sheet.write(5, 2, self.current_iteration.provisional_start_date, normal_date)
        sheet.write(5, 3, self.current_iteration.provisional_end_date, normal_date)
        sheet.write(5, 4, self.current_iteration.effective_start_date, normal_date)
        sheet.write(5, 5, self.current_iteration.effective_end_date, normal_date)
        sheet.write(5, 6, self.current_iteration.total_subjects, normal)
        sheet.write(5, 7, self.current_iteration.total_replies, normal)
        ns = ast.literal_eval(self.new_subjects)
        sheet.write(7, 0, 'New subjects (posted during the last 3 days)', subtitle)
        sheet.write(7, 1, 'Total subjects: ' + str(ns['total']), subtitle)
        sheet.write(7, 2, 'Total replies: ' + str(ns['replies']), subtitle)
        sheet.write(9, 0, 'Name', header)
        sheet.write(9, 1, 'Posted At', header)
        sheet.write(9, 2, 'State', header)
        sheet.write(9, 3, 'Total Replies', header)
        line = 10
        for s in ns['subjects']:
            sheet.write(line, 0, s['name'], normal)
            sheet.write(line, 1, s['posted_at'], normal_datetime)
            sheet.write(line, 2, s['state'], normal)
            sheet.write(line, 3, s['total_replies'], normal)
            line += 1
        line += 1
        ops = ast.literal_eval(self.open_subjects)
        sheet.write(line, 0, 'Open subjects', subtitle)
        sheet.write(line, 1, 'Total subjects: ' + str(ops['total']), subtitle)
        sheet.write(line, 2, 'Total replies: ' + str(ops['replies']), subtitle)
        line += 2
        sheet.write(line, 0, 'Name', header)
        sheet.write(line, 1, 'Posted At', header)
        sheet.write(line, 2, 'Total Replies', header)
        line += 1
        for s in ops['subjects']:
            sheet.write(line, 0, s['name'], normal)
            sheet.write(line, 1, s['posted_at'], normal_datetime)
            sheet.write(line, 2, s['total_replies'], normal)
            line += 1
        line += 1
        css = ast.literal_eval(self.closed_solved_subjects)
        sheet.write(line, 0, 'Closed [Solved] subjects', subtitle)
        sheet.write(line, 1, 'Total subjects: ' + str(css['total']), subtitle)
        sheet.write(line, 2, 'Total replies: ' + str(css['replies']), subtitle)
        line += 2
        sheet.write(line, 0, 'Name', header)
        sheet.write(line, 1, 'Posted At', header)
        sheet.write(line, 2, 'Total Replies', header)
        line += 1
        for s in css['subjects']:
            sheet.write(line, 0, s['name'], normal)
            sheet.write(line, 1, s['posted_at'], normal_datetime)
            sheet.write(line, 2, s['total_replies'], normal)
            line += 1
        line += 1
        cus = ast.literal_eval(self.closed_unsolved_subjects)
        sheet.write(line, 0, 'Closed [Unsolved] subjects', subtitle)
        sheet.write(line, 1, 'Total subjects: ' + str(cus['total']), subtitle)
        sheet.write(line, 2, 'Total replies: ' + str(cus['replies']), subtitle)
        line += 2
        sheet.write(line, 0, 'Name', header)
        sheet.write(line, 1, 'Posted At', header)
        sheet.write(line, 2, 'Total Replies', header)
        line += 1
        for s in cus['subjects']:
            sheet.write(line, 0, s['name'], normal)
            sheet.write(line, 1, s['posted_at'], normal_datetime)
            sheet.write(line, 2, s['total_replies'], normal)
            line += 1
        line += 1
        sheet.write(line, 0, 'Completed iterations', header)
        for i in self.completed_iterations.all():
            sheet.write(line, 1, i.name, normal)
            line += 1
        line += 2
        sheet.write(line, 0, 'Upcoming iterations', header)
        for i in self.upcoming_iterations.all():
            sheet.write(line, 1, i.name, normal)
            line += 1
        wb.save(os.path.join(settings.BASE_DIR, 'tmp/report.xls'))
        f = open(os.path.join(settings.BASE_DIR, 'tmp/report.xls'), 'r')
        report_file = File(f)
        self.file.save(self.project.name + '_report_' + str(self.date) + '.xls', report_file, save=True)
        report_file.close()
        f.close()
        os.remove(os.path.join(settings.BASE_DIR, 'tmp/report.xls'))

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
            report.generate_excel_file()
        except Iteration.DoesNotExist:
            pass
        