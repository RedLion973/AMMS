
import logging

from django.core.management.base import NoArgsCommand

from app.core.models import Project
from app.steering import models as steering
from thirdparty.notification import models as notification

class Command(NoArgsCommand):
    help = "Generate daily reports."
    
    def handle_noargs(self, **options):
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        logging.info("-" * 72)
        for project in Project.objects.filter(enable_reports_generation=1):
            report_id = steering.generate_report(project)
            to_users = []
            for actor in project.actors.all():
                to_users.append(actor.user)
            notification.queue(to_users, "daily_report_generated", {'report': steering.Report.objects.get(id=report_id)})
