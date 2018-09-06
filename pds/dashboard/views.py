from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from django.http import HttpResponseServerError
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django_tables2 import RequestConfig
from django.conf import settings
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.crumb_requester import CrumbRequester
import requests
import json

from dashboard import models
from dashboard import tables
from dashboard.management.commands.recycle import delete_artifact_version
from utils import logging as pds_log
from utils import commons


class CalculateDeltaVersions:

    def __init__(self, id_origin, id_destiny):
        self.id_origin = id_origin
        self.id_destiny = id_destiny

    def get_delta_data(self):
        id_o = int(self.id_origin)
        id_d = int(self.id_destiny)
        if id_d > id_o:
            aux = id_o
            id_o = id_d
            id_d = aux
        # Let's calculate delta between versions
        application_version_o = models.ApplicationVersion.objects.get(pk=id_o)
        application_version_d = models.ApplicationVersion.objects.get(pk=id_d)
        data_destiny = []
        data_delta = []
        for artifact_version_destiny in application_version_d.artifact_version.all():
            data_destiny.append(
                {
                    'artifact_id': artifact_version_destiny.artifact.id,
                    'version_id': artifact_version_destiny.id
                }
            )
        for artifact_version_origin in application_version_o.artifact_version.all():
            offset = -1
            for index_d in range(len(data_destiny)):
                if data_destiny[index_d]['artifact_id'] == artifact_version_origin.artifact.id:
                    offset = data_destiny[index_d]['version_id']
                    del data_destiny[index_d]
                    break
            global_list = []
            for av in artifact_version_origin.artifact.artifactversion_set.filter(id__gt=offset,
                                                                                  id__lte=artifact_version_origin.id):
                list_av_cl = {'av': av}
                list_cl = []
                for av_cl in av.artifactversionchangelog_set.all():
                    list_cl.append(av_cl.name)
                list_av_cl['cl'] = list_cl
                global_list.append(list_av_cl)
            data_delta.append({'artifact': artifact_version_origin.artifact, 'list_av_cl': global_list})
        return data_delta


@login_required
def change_password(request):
    errors = []
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect(reverse('change-password-success'))
        else:
            errors.append('Password no actualizada')
            return render(request, 'accounts/change_password.html', {'errors': errors})
    return render(request, 'accounts/change_password.html', {'errors': errors})


def get_versions_available_by_environment(app_id=None):
    if app_id is None:
        return {'development': [], 'testing': [], 'preproduction': [], 'production': []}
    app_versions_history = models.ApplicationVersionHistory.objects.filter(application_version__application=app_id)
    # Grouping by state
    v_by_state = {}
    for a_v_h in app_versions_history:
        try:
            v_by_state[a_v_h.state_application_version].append(a_v_h.application_version)
        except KeyError:
            v_by_state[a_v_h.state_application_version] = [a_v_h.application_version]
    build_ok = models.StateApplicationVersion.objects.get(name='Build OK')
    dep_dev = models.StateApplicationVersion.objects.get(name='Desplegado en DEV')
    released_pre = models.StateApplicationVersion.objects.get(name='Liberado a PRE')
    dep_pre = models.StateApplicationVersion.objects.get(name='Desplegado en PRE')
    released_pro = models.StateApplicationVersion.objects.get(name='Liberado a PRO')
    dep_pro = models.StateApplicationVersion.objects.get(name='Desplegado en PRO')
    dev_v = v_by_state.get(build_ok, []) + v_by_state.get(dep_dev, [])
    dev_v = dev_v + v_by_state.get(released_pre, []) + v_by_state.get(dep_pre, [])
    dev_v = dev_v + v_by_state.get(released_pro, []) + v_by_state.get(dep_pro, [])
    pre_v = v_by_state.get(released_pre, []) + v_by_state.get(dep_pre, [])
    pre_v = pre_v + v_by_state.get(released_pro, []) + v_by_state.get(dep_pro, [])
    pro_v = v_by_state.get(released_pro, []) + v_by_state.get(dep_pro, [])
    versions_by_environment = {
        'development': list(set(dev_v)),
        'preproduction': list(set(pre_v)),
        'production': list(set(pro_v))
    }
    return versions_by_environment


def get_versions_applications_environment(app_id=None):
    dict_versions_applications_environments = []
    # Getting all applications
    if not app_id:
        objects = models.Application.objects.all()
    else:
        objects = models.Application.objects.filter(id=app_id)
    for application in objects:
        # Development
        environment = models.StateApplicationVersion.objects.get(name='Desplegado en DEV')
        development = models.ApplicationVersionHistory.objects.filter(
            application_version__application=application,
            state_application_version=environment
        ).order_by('-created')[0:1]
        # Preproduction
        environment = models.StateApplicationVersion.objects.get(name='Desplegado en PRE')
        preproduction = models.ApplicationVersionHistory.objects.filter(
            application_version__application=application,
            state_application_version=environment
        ).order_by('-created')[0:1]
        # Production
        environment = models.StateApplicationVersion.objects.get(name='Desplegado en PRO')
        production = models.ApplicationVersionHistory.objects.filter(
            application_version__application=application,
            state_application_version=environment
        ).order_by('-created')[0:1]
        applications_environments_current = {'application': application,
                                             'development': development,
                                             'preproduction': preproduction,
                                             'production': production
                                             }
        dict_versions_applications_environments.append(applications_environments_current)

    return dict_versions_applications_environments


@login_required
def list_applications(request):
    table = tables.ApplicationTable(models.Application.objects.all())
    RequestConfig(request).configure(table)
    return render(request, 'applications.html', {
        'section': 'applications',
        'table': table,
        'title': "Aplicaciones <small>Lista de aplicaciones existentes</small>",
    })


@login_required
def application_detail(request, pk):
    application = models.Application.objects.get(id=pk)
    try:
        del request.session['application_name']
        del request.session['application_id']
    except KeyError:
        pass
    request.session['application_name'] = application.name
    request.session['application_id'] = application.id
    artifacts = application.artifact_set.all()
    return render(request, 'application-detail.html', {
        'section': 'components',
        'title': "%s <small>Fecha de creación: %s</small>" % (application.name, application.created.strftime("%Y-%m-%d %H:%M")),
        'url_sonar': settings.SONAR_URL,
        'artifacts': artifacts,
    })


@login_required
def list_applications_environments(request):
    dict_versions_applications_environments = get_versions_applications_environment(
        app_id=request.session['application_id'])
    dict_versions_available_environments = get_versions_available_by_environment(
        app_id=request.session['application_id'])
    return render(request, 'app-versions-environment.html', {
        'section': 'applications-environments',
        'dict_versions_applications_environments': dict_versions_applications_environments,
        'dict_versions_available_environments': dict_versions_available_environments,
        'title': "Versiones instaladas por entorno<small></small>",
    })


@login_required
def list_application_versions(request, pk):
    application = models.Application.objects.get(id=request.session['application_id'])
    return render(request, 'application-versions.html', {
        'section': 'release-dashboard',
        'application_versions': models.ApplicationVersion.objects.filter(application=application).order_by("-created"),
        'states_application_versions': models.StateApplicationVersion.objects.all(),
        'title': "%s <small>Lista de versiones disponibles</small>" % application.name,
        'application_name': application.name,
    })


@login_required
def list_application_versions_available(request, pk):
    # Getting the application
    application = models.Application.objects.get(id=request.session['application_id'])
    versions_available = []
    # Getting the versions available
    for a_v in models.ApplicationVersion.objects.filter(application=application).order_by("-created")[0:9]:
        dict_a_v = {'a_v': a_v}
        # Getting the modified component
        ar_vs = a_v.artifact_version.all().order_by("-created")[0]
        dict_a_v['ar_vs'] = ar_vs
        dict_a_v['bitbucket_url'] = commons.ssh_to_https_query_by_tag(ar_vs.artifact.repository_git, ar_vs.name)
        cl = ar_vs.artifactversionchangelog_set.all()
        dict_a_v['cl'] = cl
        versions_available.append(dict_a_v)
    dict_context = {'versions_available': versions_available}
    return render(request, 'application-versions-available.html', {
        'section': 'versions-available',
        'dict_context': dict_context,
        'title': "%s <small>Lista de versiones creadas</small>" % application.name,
    })


@login_required
def list_application_versions_components(request, pk):
    a_v = models.ApplicationVersion.objects.get(id=pk)
    artifact_version = []
    for ar_ver in a_v.artifact_version.all():
        artifact_version.append({"name": ar_ver.name, "artifact_id": ar_ver.artifact.id, "artifact": ar_ver.artifact,
                                 "state_artifact_version": ar_ver.state_artifact_version, "created": ar_ver.created,
                                 "created_from_branch": ar_ver.created_from_branch, "email": ar_ver.email,
                                 "bitbucket_url": commons.ssh_to_https_query_by_tag(ar_ver.artifact.repository_git, ar_ver.name)})
    return render(request, 'application-versions-components.html', {
        'section': 'versions-available',
        'artifact_version': artifact_version,
        'state_application_versions': models.StateApplicationVersion.objects.all(),
        'history_application_version': models.ApplicationVersionHistory.objects.filter(application_version=a_v).order_by("id"),
        'title': "%s <small>Componentes de la versión %s</small>" % (a_v.application, a_v.name),
    })


@login_required
def artifact_details(request, pk):
    a = models.Artifact.objects.get(id=pk)
    a_v = models.ArtifactVersion.objects.filter(artifact=a).order_by("-created")
    dict_versions_cl = []
    for art_ver in a_v:
        cl = models.ArtifactVersionChangeLog.objects.filter(artifact_version=art_ver)
        dict_cl = dict(version=art_ver, cl=cl,
                       bitbucket_url=commons.ssh_to_https_query_by_tag(a.repository_git, art_ver.name))
        dict_versions_cl.append(dict_cl)
    return render(request, 'artifact-details.html', {
        'section': 'components',
        'dict_versions_cl': dict_versions_cl,
        'artifact': a,
        'url_sonar': settings.SONAR_URL,
        'title': "%s <small>Detalles y ChangeLog para el componente %s</small>" % (a.application, a),
    })


@login_required
def artifact_version_details(request, pk):
    a_v = models.ArtifactVersion.objects.get(id=pk)
    a_v_h = models.ArtifactVersionHistory.objects.filter(artifact_version=a_v).order_by("-created")
    return render(request, 'artifact-version-details.html', {
        'section': 'components',
        'application_version': a_v,
        'application_version_history': a_v_h,
        'state_artifact_versions': models.StateArtifactVersion.objects.all(),
        'title': "%s <small>Histórico para la versión %s</small>" % (a_v.artifact, a_v.name),
    })


@login_required
def deploy_application(request):
    if not request.user.is_authenticated():
        return HttpResponseServerError("User not authenticated!")
    if request.method == 'POST':
        pds_log.logger.info("Asking for a new deployment:")
        params_job_deploy = {'application': request.POST.get('application', ''),
                             'environment': request.POST.get('environment', ''),
                             'version': request.POST.get('version', '')
                             }
        # Action requested
        action = "Despliegue solicitado a '%s'" % params_job_deploy["environment"]
        # Data for the tasks engine
        if settings.TASKS_ENGINE == 'rundeck':
            data = {
                'options': params_job_deploy
            }
        elif settings.TASKS_ENGINE == 'jenkins':
            data = params_job_deploy
        else:
            data = {}
        pds_log.logger.info("-> Data = %s" % data)
        message = None
        if settings.TASKS_ENGINE == 'rundeck':
            url = settings.DEPLOY_SERVER_URL + settings.JOB_DEPLOY_URL
            headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                       'X-Rundeck-Auth-Token': settings.AUTH_TOKEN}
            pds_log.logger.info("-> Url = %s" % url)
            pds_log.logger.info("-> Headers = %s" % headers)
            try:
                r = requests.post(url, data=json.dumps(data), headers=headers)
                # Aqui esta el enlace al job iniciado: r.json()['permalink']
                message = '<font color="green">Job de ejecucion lanzado:</font> puedes consultar el progreso <a href="%s" target="_blank"><b>aqui</b></a>' % \
                          r.json()['permalink']
            except requests.exceptions.RequestException as e:
                pds_log.logger.error("Error al conectar con el sistema de despliegue")
                pds_log.logger.error(e)
                message = "<font color='red'>Se ha producido un error al invocar al sistema de despliegue</font>"
            except KeyError as e:
                pds_log.logger.error("Error al conectar con el sistema de despliegue")
                pds_log.logger.error(e)
                message = "<font color='red'>Se ha producido un error al invocar al sistema de despliegue</font>"
        elif settings.TASKS_ENGINE == 'jenkins':
            try:
                requester = CrumbRequester(
                    baseurl=settings.JENKINS_URL,
                    username=settings.JENKINS_USER,
                    password=settings.JENKINS_PASSWORD
                )
                jenkins = Jenkins(settings.JENKINS_URL, requester=requester)
                jenkins.build_job(settings.JENKINS_JOB_DEPLOY_APPLICATION, data)
                url_query_job_status = settings.JENKINS_URL + "/job/" + settings.JENKINS_JOB_DEPLOY_APPLICATION
                message = '<font color="green">Job de despliegue lanzado:</font> puedes consultar el progreso <a href="%s" target="_blank"><b>aqui</b></a>' % \
                          url_query_job_status
            except Exception as e:
                pds_log.logger.error("Se ha producido un error al invocar al script de despliegue")
                pds_log.logger.error(e)
                message = "<font color='red'>Se ha producido un error al invocar al script de despliegue</font>"
        else:
            pass

        messages.success(request, message)
        # We must registry a new history record
        application_version = models.ApplicationVersion.objects.get(name=params_job_deploy["version"], application__name=params_job_deploy["application"])
        history_record = models.ApplicationVersionHistory(application_version=application_version,
                                                          author=request.user,
                                                          action=action)
        history_record.save()

        if "applications-environments" in request.META['HTTP_REFERER']:
            return HttpResponseRedirect(reverse('applications-environments'))
        else:
            return HttpResponseRedirect(reverse('application-versions', args=("1",)))

    return HttpResponseServerError("Request not supported!")


@login_required
def update_maturity_level_application(request, pk):
    pds_log.logger.info("Asking for updating maturity level")
    if request.method == 'POST':
        data = {'application': request.POST.get('application', ''),
                'version': request.POST.get('version', '')
                }
        pds_log.logger.info("-> Data = %s" % data)
        try:
            application = models.Application.objects.get(name=data['application'])
            application_version = models.ApplicationVersion.objects.get(
                name=data['version'],
                application=application)
            # Updating the state
            new_state = models.StateApplicationVersion.objects.get(id=pk)
            pds_log.logger.info("New request state = %s", new_state)
            application_version.state_application_version = new_state
            application_version.save()
            pds_log.logger.info("State updated to %s!", new_state)
            # Action requested
            action = new_state.name
            history_record = models.ApplicationVersionHistory(application_version=application_version,
                                                              state_application_version=new_state,
                                                              author=request.user,
                                                              action=action)
            history_record.save()
            pds_log.logger.info("History record created successfully!")

        except KeyError:
            return HttpResponseServerError("Malformed data!")
        except models.Application.DoesNotExist:
            return HttpResponseServerError("Application doesn't exist")
        except models.ApplicationVersion.DoesNotExist:
            return HttpResponseServerError("Application Version doesn't exist")
        except models.StateApplicationVersion.DoesNotExist:
            return HttpResponseServerError("Application State doesn't exist")

        # Actualizamos el estado de todos los artefactos que componen la version del application
        # Primero obtenemos el nuevo estado
        try:
            new_state_artifact = models.StateArtifactVersion.objects.get(id=pk)
            pds_log.logger.info("NUEVO state artifact obtenido de la base de datos de PDS = %s", new_state_artifact)
        except models.StateArtifactVersion.DoesNotExist:
            return HttpResponseServerError("No existe el nuevo estado para la version del artefacto")

        for av in application_version.artifact_version.all():
            # if av.state_artifact_version.id < application_version.state_application_version.id:
            av.state_artifact_version = new_state_artifact
            av.save()
            pds_log.logger.info("Actualizado el state del artifact_version %s a %s", av, new_state_artifact)
            pds_log.logger.info("Creating a new history record!")
            history_record = models.ArtifactVersionHistory(artifact_version=av,
                                                           state_artifact_version=new_state_artifact)
            history_record.save()
            pds_log.logger.info("History record created successfully!")

        return HttpResponseRedirect(reverse('application-versions', args=(application.id,)))

    return HttpResponseServerError("Request not supported")


@login_required
def analysis_delta_versions(request):
    if request.method == 'POST':
        id_o = request.POST['v_a']
        id_d = request.POST['v_b']
        cdv = CalculateDeltaVersions(id_o, id_d)
        return render(request, 'analysis-delta.html', {
            'section': 'delta',
            'delta_data': cdv.get_delta_data(),
            'title': "Delta <small>Entre versiones</small>",
        })

    applications = models.Application.objects.all()
    dict_applications_versions = []
    for a in applications:
        versions = models.ApplicationVersion.objects.filter(application=a)
        dict_a_v = {'application': a, 'versions': versions}
        dict_applications_versions.append(dict_a_v)
    return render(request, 'delta-versions.html', {
        'section': 'delta',
        'dict_applications_versions': dict_applications_versions,
        'title': "Análisis delta <small>Entre versiones</small>",
    })


@login_required
def analysis_delta_environments(request):
    if request.method == 'POST':
        id_o = request.POST['id_environment_o']
        id_d = request.POST['id_environment_d']
        cdv = CalculateDeltaVersions(id_o, id_d)
        return render(request, 'analysis-delta.html', {
            'section': 'delta',
            'delta_data': cdv.get_delta_data(),
            'title': "Delta <small>Entre entornos</small>",
        })

    dict_versions_applications_environments = get_versions_applications_environment()
    return render(request, 'delta-environments.html', {
        'section': 'delta',
        'dict_versions_applications_environments': dict_versions_applications_environments,
        'title': "Análisis delta <small>Entre entornos</small>",
    })


@login_required
def artifact_version_delete(request, pk):
    try:
        artifact_version = models.ArtifactVersion.objects.get(id=pk, artifact__application=request.session['application_id'])
        artifact = artifact_version.artifact
    except models.ArtifactVersion.DoesNotExist:
        return HttpResponseServerError("Artifact Version doesn't exist")

    # We can remove the application version and the artifact version itself
    pds_log.logger.info("Asking for deleting artifact from GUI:")
    message = delete_artifact_version(artifact_version, referring="gui")
    messages.success(request, message)
    return HttpResponseRedirect(reverse('artifact-details', args=(artifact.id,)))


@login_required
def application_version_delete(request, pk):
    try:
        application_version = models.ApplicationVersion.objects.get(id=pk, application=request.session['application_id'])
    except models.ApplicationVersion.DoesNotExist:
        return HttpResponseServerError("Application Version doesn't exist")

    # We can remove the application version
    pds_log.logger.info("Asking for deleting application version from GUI:")
    application_version.delete()
    message = '<font color="green">Versión eliminada de forma correcta</font>'
    messages.success(request, message)
    return HttpResponseRedirect(reverse('versions-available', args=(pk,)))


@login_required
def create_infrastructure_project(request):
    if not request.user.is_authenticated():
        return HttpResponseServerError("User not authenticated!")
    if request.method == 'POST':
        pds_log.logger.info("Asking for a new infrastructure project:")
        try:
            artifact = models.Artifact.objects.get(id=request.POST.get('component_id', ''), application=request.session['application_id'])
        except models.Artifact.DoesNotExist:
            return HttpResponseServerError("Object doesn't exist!")
        application_name = artifact.application.name
        version = artifact.artifactversion_set.order_by('-created')[0].name.split("-")[0] + "-SNAPSHOT"
        group_id = artifact.group_id
        artifact_name = artifact.artifact_id
        technology_type = artifact.technology_type.name
        params_job_deploy = {'application': application_name,
                             'version': version,
                             'technology': technology_type,
                             'artifact': artifact_name
                             }
        # Does the infrastructure component exist?
        try:
            models.Artifact.objects.get(group_id='vocento.ansible', application=request.session['application_id'])
            message = "<font color='red'>Ya existe componente de infraestructura para este proyecto</font>"
            messages.success(request, message)
            return HttpResponseRedirect(reverse('application-details', args=(request.session['application_id'],)))
        except models.Artifact.DoesNotExist:
            pass
        # Data for the tasks engine
        if settings.TASKS_ENGINE == 'rundeck':
            data = {
                'options': params_job_deploy
            }
        elif settings.TASKS_ENGINE == 'jenkins':
            data = params_job_deploy
        else:
            data = {}
        pds_log.logger.info("-> Data = %s" % data)
        message = None
        if settings.TASKS_ENGINE == 'rundeck':
            url = settings.DEPLOY_SERVER_URL + settings.JOB_CREATE_INFRASTRUCTURE_COMPONENT_URL
            headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                       'X-Rundeck-Auth-Token': settings.AUTH_TOKEN}
            pds_log.logger.info("-> Url = %s" % url)
            pds_log.logger.info("-> Headers = %s" % headers)
            try:
                r = requests.post(url, data=json.dumps(data), headers=headers)
                # Aqui esta el enlace al job iniciado: r.json()['permalink']
                message = '<font color="green">Job de ejecución lanzado:</font> puedes consultar el progreso <a href="%s" target="_blank"><b>aquí</b></a>' % \
                          r.json()['permalink']
            except requests.exceptions.RequestException as e:
                pds_log.logger.error("Error al conectar con el sistema de creación de infraestructura")
                pds_log.logger.error(e)
                message = "<font color='red'>Se ha producido un error al invocar al sistema automatizado</font>"
        elif settings.TASKS_ENGINE == 'jenkins':
            try:
                requester = CrumbRequester(
                    baseurl=settings.JENKINS_URL,
                    username=settings.JENKINS_USER,
                    password=settings.JENKINS_PASSWORD
                )
                jenkins = Jenkins(settings.JENKINS_URL, requester=requester)
                jenkins.build_job(settings.JENKINS_JOB_CREATE_INFRASTRUCTURE_COMPONENT, data)
                url_query_job_status = settings.JENKINS_URL + "/job/" + settings.JENKINS_JOB_CREATE_INFRASTRUCTURE_COMPONENT
                message = '<font color="green">Job de ejecución lanzado:</font> puedes consultar el progreso <a href="%s" target="_blank"><b>aquí</b></a>' % \
                          url_query_job_status
            except Exception as e:
                pds_log.logger.error("Se ha producido un error al invocar al script de creación de infraestructura")
                pds_log.logger.error(e)
                message = "<font color='red'>Se ha producido un error al invocar al script de despliegue</font>"
        else:
            pass

        messages.success(request, message)

        return HttpResponseRedirect(reverse('application-details', args=(request.session['application_id'],)))

    return HttpResponseServerError("Request not supported!")
