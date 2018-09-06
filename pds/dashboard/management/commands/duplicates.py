from django.core.management.base import BaseCommand
from vocteams import models
from utils import logging as pds_log


def get_team(software_solution):
    team = models.TeamVocento.objects.filter(software_solution=software_solution).first()
    if team is not None:
        team = team.name
    else:
        team = "Unknown"
    return team


def process_repository(repository_git):
    try:
        repository = models.RepositoryGit.objects.get(name=repository_git.name)
    except models.RepositoryGit.MultipleObjectsReturned:
        pds_log.logger.info("-> Duplicated repository = %s" % repository_git.name)
        return
    # Analyzing the repository
    # 1.- Getting the software solutions
    ss = repository.softwaresolution_set.all()
    if ss.count() > 1:
        pds_log.logger.info("-> Repository %s duplicated in:" % repository.name)
        for s2 in ss:
            team = get_team(s2)
            pds_log.logger.info(
                "-> - %s in team %s" % (s2.name, team))


def process_job_jenkins(job_jenkins):
    try:
        job_jenkins = models.JobJenkins.objects.get(jenkins_server=job_jenkins.jenkins_server, name=job_jenkins.name)
    except models.JobJenkins.MultipleObjectsReturned:
        pds_log.logger.info("-> Duplicated job_jenkins = %s - %s" % (job_jenkins.jenkins_server, job_jenkins.name))
        return
    # Analyzing the jenkins job
    # 1.- Getting the software solutions
    ss = job_jenkins.softwaresolution_set.all()
    if ss.count() > 1:
        pds_log.logger.info("-> Job %s - %s duplicated in:" % (job_jenkins.jenkins_server, job_jenkins.name))
        for s2 in ss:
            team = get_team(s2)
            pds_log.logger.info(
                "-> - %s in team %s" % (s2.name, team))


class Command(BaseCommand):
    def handle(self, *args, **options):
        rg = models.RepositoryGit.objects.all()
        for r in rg:
            process_repository(r)
        jj = models.JobJenkins.objects.all()
        for j in jj:
            process_job_jenkins(j)
