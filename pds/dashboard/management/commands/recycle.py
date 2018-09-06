from django.core.management.base import BaseCommand, CommandError
from dashboard import models
from utils import logging as pds_log
from django.conf import settings
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.crumb_requester import CrumbRequester
import requests
import json


def delete_artifact(artifact_version):
    models.ApplicationVersion.objects.filter(artifact_version=artifact_version).delete()
    artifact_version.delete()
    pds_log.logger.info("-> version %s deleted" % artifact_version.name)


def delete_artifact_version(a_v, referring="cron"):
    artifact_version = a_v
    artifact = a_v.artifact
    # Getting the objectId if Nexus Version = 3
    nexus_v3_object_id = '0'
    if settings.NEXUS_VERSION == '3':
        url = settings.NEXUS_API_URL
        headers = {"Content-type": "application/json"}
        data = {"sort": [{"property": "group", "direction": "ASC"}],
                "action": "coreui_Component", "method": "read",
                "data": [{"page": 1, "start": 0, "limit": 1000000,
                          "filter": [{"property": "repositoryName",
                                      "value": settings.NEXUS_REPOSITORY}]}],
                "type": "rpc",
                "tid": 21}
        r = requests.post(url, data=json.dumps(data), headers=headers, verify=False)
        data_json = json.loads(r.text)
        for it in data_json["result"]["data"]:
            if it["group"] == artifact.group_id and \
                it["name"] == artifact.artifact_id and \
                    it["version"] == artifact_version.name:
                        nexus_v3_object_id = it["id"]

    params_job_delete = {'repositorio_git': artifact.repository_git,
                         'group_id': artifact.group_id,
                         'artifact_id': artifact.artifact_id,
                         'version': artifact_version.name,
                         'object_id': nexus_v3_object_id
                         }

    # Data for the tasks engine
    if settings.TASKS_ENGINE == 'rundeck':
        data = {
            'options': params_job_delete
        }
    elif settings.TASKS_ENGINE == 'jenkins':
        data = params_job_delete
    else:
        data = {}

    message = None
    if settings.TASKS_ENGINE == 'rundeck':
        # Data for RunDeck
        url = settings.DEPLOY_SERVER_URL + settings.JOB_DELETE_URL
        headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                   'X-Rundeck-Auth-Token': settings.AUTH_TOKEN}
        pds_log.logger.info("-> url = %s" % url)
        pds_log.logger.info("-> headers = %s" % headers)
        pds_log.logger.info("-> data = %s" % data)
        try:
            r = requests.post(url, data=json.dumps(data), headers=headers)
            # Aqui esta el enlace al job iniciado: r.json()['permalink']
            message = '<font color="green">Job de borrado lanzado:</font> puedes consultar el progreso <a href="%s" target="_blank"><b>aqui</b></a>' % \
                      r.json()['permalink']
            delete_artifact(artifact_version)
        except requests.exceptions.RequestException as e:
            pds_log.logger.error("Se ha producido un error al invocar al script de borrado")
            pds_log.logger.error(e)
            message = "<font color='red'>Se ha producido un error al invocar al script de borrado</font>"
    elif settings.TASKS_ENGINE == 'jenkins':
        try:
            requester = CrumbRequester(
                baseurl=settings.JENKINS_URL,
                username=settings.JENKINS_USER,
                password=settings.JENKINS_PASSWORD
            )
            jenkins = Jenkins(settings.JENKINS_URL, requester=requester)
            jenkins.build_job(settings.JENKINS_JOB_DELETE_ARTIFACT, data)
            url_query_job_status = settings.JENKINS_URL + "/job/" + settings.JENKINS_JOB_DELETE_ARTIFACT
            message = '<font color="green">Job de borrado lanzado:</font> puedes consultar el progreso <a href="%s" target="_blank"><b>aqui</b></a>' % \
                      url_query_job_status
            delete_artifact(artifact_version)
        except Exception as e:
            pds_log.logger.error("Se ha producido un error al invocar al script de borrado")
            pds_log.logger.error(e)
            message = "<font color='red'>Se ha producido un error al invocar al script de borrado</font>"
    else:
        pass

    if referring == "gui":
        return message


def get_max_state_artifact_version(artifact_version):
    try:
        # Max state will let us to create a dictionary with the states
        max_state = models.ArtifactVersionHistory.objects.filter(
            artifact_version=artifact_version).order_by("-state_artifact_version")[0]
        return max_state.state_artifact_version.name
    except IndexError:
        return None


def get_states_and_versions(artifact):
    dictionary = {}
    for a_v in models.ArtifactVersion.objects.filter(artifact=artifact).order_by("-created"):
        max_state = get_max_state_artifact_version(a_v)
        # We must return a dictionary whit the versions
        if max_state is not None:
            try:
                dictionary[max_state].append(a_v)
            except KeyError:
                dictionary[max_state] = [a_v]
    return dictionary


def process_artifacts(application):
    for artifact in models.Artifact.objects.filter(application=application):
        pds_log.logger.info("- Processing artifact %s" % artifact)
        states_and_versions = get_states_and_versions(artifact)
        # Getting the versions to delete
        for state in states_and_versions:
            total_versions_state = len(states_and_versions[state])
            pds_log.logger.info("-- Processing %s elements at state %s" % (total_versions_state, state))
            for a_v in states_and_versions[state][3:]:
                delete_artifact_version(a_v)


class Command(BaseCommand):
    def handle(self, *args, **options):
        app = models.Application.objects.all()
        for a in app:
            pds_log.logger.info("Processing application %s" % a.name)
            process_artifacts(a)
