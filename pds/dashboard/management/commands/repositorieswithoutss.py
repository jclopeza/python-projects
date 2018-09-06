from django.core.management.base import BaseCommand
from vocteams import models
from utils import logging as pds_log


def process_repository(repository_git):
    try:
        repository = models.RepositoryGit.objects.get(name=repository_git.name)
    except models.RepositoryGit.MultipleObjectsReturned:
        pds_log.logger.info("-> Duplicated repository = %s" % repository_git.name)
        return
    # Analyzing the repository
    # 1.- Getting the software solutions
    ss = repository.softwaresolution_set.all()
    if ss.count() == 0:
        pds_log.logger.info("-> %s" % repository.name)


class Command(BaseCommand):
    pds_log.logger.info("-> Repositories without software solution")

    def handle(self, *args, **options):
        rg = models.RepositoryGit.objects.all()
        for r in rg:
            process_repository(r)
