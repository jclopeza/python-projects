from django.http import HttpResponse, HttpResponseServerError, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from dashboard import models
from vocteams import models as vocteams_models
import requests
import json

from utils import logging as pds_log


@csrf_exempt
def create_new_artifact_jenkinsfile(request):
    pds_log.logger.info("Empezamos a procesar la peticion de creacion de nuevo artefacto")
    if request.method == 'POST':
        json_data = json.loads(request.body.decode())
        pds_log.logger.info("Cargados los datos JSON")
        try:
            application = json_data['application']
            group_id = json_data['group_id']
            artifact_id = json_data['artifact_id']
            repository_git = json_data['repository_git']
            technology_type = json_data['technology_type']
            pom_directory = ".mvn"
            created_from_branch = json_data['created_from_branch']
            app_version = json_data['app_version']
            art_version = json_data['art_version']
            build_url = json_data.get('build_url', None)
            changelog = json_data['changelog']
            email = json_data.get('email', None)
            duration = 0
            repository_url = json_data.get('repository_url', None)
            pds_log.logger.info("Datos obtenidos:")
            pds_log.logger.info("    application=%s", application)
            pds_log.logger.info("    group_id=%s", group_id)
            pds_log.logger.info("    artifact_id=%s", artifact_id)
            pds_log.logger.info("    repository_git=%s", repository_git)
            pds_log.logger.info("    technology_type=%s", technology_type)
            pds_log.logger.info("    pom_directory=%s", pom_directory)
            pds_log.logger.info("    created_from_branch=%s", created_from_branch)
            pds_log.logger.info("    app_version=%s", app_version)
            pds_log.logger.info("    art_version=%s", art_version)
            pds_log.logger.info("    build_url=%s", build_url)
            pds_log.logger.info("    changelog=%s", changelog)
            pds_log.logger.info("    email=%s", email)
            pds_log.logger.info("    duration=%s", duration)
        except KeyError:
            return HttpResponseServerError("Malformed data!")

        app = models.Application.objects.get_or_create(name=application)[0]
        tt = models.TechnologyType.objects.get_or_create(name=technology_type)[0]

        try:
            pds_log.logger.info("Verificamos si existe el artefacto %s:%s", group_id, artifact_id)
            art = models.Artifact.objects.get(group_id=group_id, artifact_id=artifact_id)
            pds_log.logger.info("Existe en BDD, no hace falta crearlo")
        except models.Artifact.DoesNotExist:
            pds_log.logger.info("El artefacto NO EXISTE en base de datos, hace falta crearlo")
            art = models.Artifact.objects.create(group_id=group_id, artifact_id=artifact_id,
                                           repository_git=repository_git,
                                           application=app, technology_type=tt, pom_directory=pom_directory)

        # Get states available
        ssv = models.StateApplicationVersion.objects.get_or_create(name='Build OK')[0]
        sav = models.StateArtifactVersion.objects.get_or_create(name='Build OK')[0]
        app_ver = models.ApplicationVersion.objects.create(name=app_version,
                                                        application=app,
                                                        state_application_version=ssv,
                                                        created_from_branch=created_from_branch,
                                                        email=email)
        history_record = models.ApplicationVersionHistory(application_version=app_ver,
                                                        state_application_version=ssv)
        history_record.save()

        # Getting the last version for the application
        try:
            if created_from_branch.startswith('release'):
                startswith = app_version.split('-B')[0]
                last_application_version = models.ApplicationVersion.objects.filter(
                    application__name=application, name__startswith=startswith).exclude(name=app_version).order_by("-created")[0]
            else:
                last_application_version = models.ApplicationVersion.objects.filter(
                    application__name=application, created_from_branch__startswith='PR').exclude(name=app_version).order_by("-created")[0]
            pds_log.logger.info("    Application obtained ==> %s" % last_application_version.name)
            for a_v in last_application_version.artifact_version.exclude(artifact=art):
                pds_log.logger.info("-> %s" % a_v)
                app_ver.artifact_version.add(a_v)
        except IndexError:
            pds_log.logger.info("There aren't any versions available")

        new_a_v = models.ArtifactVersion.objects.create(name=art_version, artifact=art,
                                                        state_artifact_version=sav, build_url=build_url,
                                                        created_from_branch=created_from_branch,
                                                        email=email, duration=duration, repository_url=repository_url)

        history_record = models.ArtifactVersionHistory(artifact_version=new_a_v,
                                                    state_artifact_version=sav)
        history_record.save()

        # New records for Changelog
        for cl in changelog.split("@@@"):
            models.ArtifactVersionChangeLog.objects.create(name=cl, artifact_version=new_a_v)
        app_ver.artifact_version.add(new_a_v)

        return HttpResponse(status=201)

    return HttpResponseServerError("Peticion no soportada")


@csrf_exempt
def create_new_artifact(request):
    pds_log.logger.info("Empezamos a procesar la peticion de creacion de nuevo artefacto")
    if request.method == 'POST':
        json_data = json.loads(request.body.decode())
        pds_log.logger.info("Cargados los datos JSON")
        try:
            application = json_data['application']
            component_group_id = json_data['component_group_id']
            component_artifact_id = json_data['component_artifact_id']
            repository_git = json_data['repository_git']
            technology_type = json_data['technology_type']
            pom_directory = json_data['pom_directory']
            pds_log.logger.info("Datos obtenidos:")
            pds_log.logger.info("    application=%s", application)
            pds_log.logger.info("    component_group_id=%s", component_group_id)
            pds_log.logger.info("    component_artifact_id=%s", component_artifact_id)
            pds_log.logger.info("    repository_git=%s", repository_git)
            pds_log.logger.info("    technology_type=%s", technology_type)
            pds_log.logger.info("    pom_directory=%s", pom_directory)
        except KeyError:
            return HttpResponseServerError("Malformed data!")

        app = models.Application.objects.get_or_create(name=application)[0]
        tt = models.TechnologyType.objects.get_or_create(name=technology_type)[0]
        pds_log.logger.info("Application obtenida de la base de datos de PDS = %s", app)
        pds_log.logger.info("TechnologyType obtenido de la base de datos de PDS = %s", tt)

        try:
            pds_log.logger.info("Verificamos si existe el artefacto %s:%s", component_group_id, component_artifact_id)
            models.Artifact.objects.get(group_id=component_group_id, artifact_id=component_artifact_id)
            pds_log.logger.info("Existe en BDD, no hace falta crearlo")
        except models.Artifact.DoesNotExist:
            pds_log.logger.info("El artefacto NO EXISTE en base de datos, hace falta crearlo")
            models.Artifact.objects.create(group_id=component_group_id, artifact_id=component_artifact_id,
                                           repository_git=repository_git,
                                           application=app, technology_type=tt, pom_directory=pom_directory)

        return HttpResponse(status=201)

    return HttpResponseServerError("Peticion no soportada")


@csrf_exempt
def update_state_application_version_by_name(request):
    pds_log.logger.info("Empezamos a procesar la peticion para actualizar el estado de una version de aplicacion")
    if request.method == 'POST':
        json_data = json.loads(request.body.decode())
        pds_log.logger.info("Cargados los datos JSON")

        try:
            application_name_json = json_data['application_name']
            component_name_json = json_data.get('component_name')
            application_version_json = json_data['application_version']
            build_duration_json = int(json_data.get('duration', '0'))
            state_application_version_id_json = json_data['state_application_version_id']
            if state_application_version_id_json == "build_ok":
                state_application_version_id_json = "2"
            elif state_application_version_id_json == "development" or state_application_version_id_json == "des":
                state_application_version_id_json = "3"
            elif state_application_version_id_json == "preproduction" or state_application_version_id_json == "pre":
                state_application_version_id_json = "5"
            elif state_application_version_id_json == "production" or state_application_version_id_json == "pro":
                state_application_version_id_json = "7"
            else:
                state_application_version_id_json = "1"
            build_url_json = json_data.get('build_url', None)
            repository_url_json = json_data.get('repository_url', None)
            pds_log.logger.info("Datos obtenidos:")
            pds_log.logger.info("    application_name=%s", application_name_json)
            pds_log.logger.info("    component_name=%s", component_name_json)
            pds_log.logger.info("    application_version=%s", application_version_json)
            pds_log.logger.info("    duration=%s", build_duration_json)
            pds_log.logger.info("    state_application_version_id=%s", state_application_version_id_json)
            pds_log.logger.info("    build_url=%s", build_url_json)
            pds_log.logger.info("    repository_url=%s", repository_url_json)
            application = models.Application.objects.get(name=application_name_json)
            application_version = models.ApplicationVersion.objects.get(
                name=application_version_json,
                application=application)
            pds_log.logger.info("Application obtenida de la base de datos de PDS = %s", application)
            pds_log.logger.info("ApplicationVersion obtenida de la base de datos de PDS = %s", application_version)
            # Actualizamos el state de la version de la aplicacion
            new_state = models.StateApplicationVersion.objects.get(id=state_application_version_id_json)
            pds_log.logger.info("NUEVO state application obtenido de la base de datos de PDS = %s", new_state)
            application_version.state_application_version = new_state
            application_version.save()
            pds_log.logger.info("Actualizado el state del application a %s", new_state)
            # Creating a new history record
            history_record = models.ApplicationVersionHistory(application_version=application_version,
                                                              state_application_version=new_state)
            history_record.save()
            pds_log.logger.info("History record created successfully!")

        except KeyError:
            return HttpResponseServerError("Malformed data!")
        except models.Application.DoesNotExist:
            return HttpResponseServerError("No existe la aplicacion")
        except models.ApplicationVersion.DoesNotExist:
            return HttpResponseServerError("No existe la version de la aplicacion")
        except models.StateApplicationVersion.DoesNotExist:
            return HttpResponseServerError("No existe el nuevo estado para la version de la aplicacion")

        # Actualizamos el estado de todos los artefactos que componen la version del application
        # Primero obtenemos el nuevo estado
        try:
            new_state_artifact = models.StateArtifactVersion.objects.get(id=state_application_version_id_json)
            pds_log.logger.info("NUEVO state artifact obtenido de la base de datos de PDS = %s", new_state_artifact)
        except models.StateArtifactVersion.DoesNotExist:
            return HttpResponseServerError("No existe el nuevo estado para la version del artefacto")

        for av in application_version.artifact_version.all():
            # if av.state_artifact_version.id < application_version.state_application_version.id:
            av.state_artifact_version = new_state_artifact
            if av.artifact.artifact_id == component_name_json:
                av.duration = build_duration_json
                if build_url_json is not None:
                    av.build_url = build_url_json
                if repository_url_json is not None:
                    av.repository_url = repository_url_json
            av.save()
            pds_log.logger.info("Actualizado el state del artifact_version %s a %s", av, new_state_artifact)
            pds_log.logger.info("Creating a new history record!")
            history_record = models.ArtifactVersionHistory(artifact_version=av,
                                                           state_artifact_version=new_state_artifact)
            history_record.save()
            pds_log.logger.info("History record created successfully!")

        return HttpResponse(status=201)

    return HttpResponseServerError("Peticion no soportada")


@csrf_exempt
def analyze_bitbucket_data(request):
    pds_log.logger.info("Empezamos a procesar la peticion recibida de BitBucket")
    if request.method == 'POST':
        json_data = json.loads(request.body.decode())
        pds_log.logger.info("Cargados los datos JSON")
        try:
            # Vamos a obtener los datos necesarios
            project_key = json_data['repository']['project']['key']
            application = json_data['repository']['project']['name']
            component = json_data['repository']['name']
            slug = json_data['repository']['slug']
            branch = json_data['refChanges'][0]['refId']
            pds_log.logger.info(" -->> project key = %s", project_key)
            pds_log.logger.info(" -->> application = %s", application)
            pds_log.logger.info(" -->> component = %s", component)
            pds_log.logger.info(" -->> slug = %s", slug)
            pds_log.logger.info(" -->> branch = %s", branch)
            pds_log.logger.info(" -->> BITBUCKET_URL = %s", settings.BITBUCKET_URL)
            # Vamos a recoger los comentarios asociados al commit/push
            change_sets = json_data['changesets']['values']
            for change in change_sets:
                message = change['toCommit']['message']
                pds_log.logger.info(" -->> message = %s", message)

        except KeyError:
            return HttpResponseServerError("Malformed data!")

    return HttpResponse(status=201)


@csrf_exempt
def get_applications_available(request):
    pds_log.logger.info("Asking for available applications")
    applications_available = models.Application.objects.all()
    output = []
    for application_available in applications_available:
        output.append(application_available.name)

    return JsonResponse(output, safe=False)


@csrf_exempt
def get_versions_available(request, app, environment, show_all=None):
    pds_log.logger.info("Asking for available versions for:")
    pds_log.logger.info("    Application: %s" % app)
    pds_log.logger.info("    Environment: %s" % environment)
    pds_log.logger.info("    show_all: %s" % show_all)
    if environment == 'des':
        index_offset = 2
    elif environment == 'test':
        index_offset = 4
    elif environment == 'pre':
        index_offset = 6
    else:
        index_offset = 9
    if show_all:
        levels = models.StateApplicationVersion.objects.filter(id__gte=2).values_list('id', flat=True)
    else:
        levels = models.StateApplicationVersion.objects.filter(id__gte=index_offset).values_list('id', flat=True)
    # Getting the versions
    versions_available = models.ApplicationVersion.objects.filter(
        application__name=app, state_application_version__in=levels)
    output = []
    for version_available in versions_available:
        output.append(version_available.name)

    return JsonResponse(output, safe=False)


@csrf_exempt
def get_artifacts_versions_of_application_version(request, application, application_version=None, infra=None):
    pds_log.logger.info("Asking for artifact versions for:")
    pds_log.logger.info("    Application: %s" % application)
    pds_log.logger.info("    Application version: %s" % application_version)
    pds_log.logger.info("    Infra: %s" % infra)
    # Getting the artifact versions
    try:
        if application_version:
            pds_log.logger.info("    Application version informada")
            application_version = models.ApplicationVersion.objects.get(
                name=application_version,
                application__name=application)
        else:
            pds_log.logger.info("    Application version NO informada")
            application_version = models.ApplicationVersion.objects.filter(
                application__name=application).order_by("-created")[0]
    except models.ApplicationVersion.DoesNotExist:
        return HttpResponseServerError("Application Version doesn't exist")

    output = {}
    infra_url = None
    for artifact_version in application_version.artifact_version.all():
        artifact_dictionary = {'url': artifact_version.repository_url, 'version': artifact_version.name}
        output[artifact_version.artifact.group_id + ':' + artifact_version.artifact.artifact_id] = artifact_dictionary
        # Adding this line for Ansible scripts
        if artifact_version.artifact.group_id == "vocento.ansible":
            infra_url = artifact_version.repository_url

    if infra and infra_url:
        return HttpResponse(infra_url, status=200)
    elif infra:
        return HttpResponseServerError("ERROR: Infrastructure component doesn't exist")
    return JsonResponse(output, safe=False)


@csrf_exempt
def get_last_version_of_application(request, application):
    pds_log.logger.info("Asking for last version:")
    pds_log.logger.info("    Application: %s" % application)
    # Getting the artifact versions
    try:
        application_version = models.ApplicationVersion.objects.filter(
            application__name=application).order_by("-created")[0]
    except models.ApplicationVersion.DoesNotExist:
        return HttpResponseServerError("Application doesn't exist")

    output = {'version': application_version.name}

    return JsonResponse(output, safe=False)


@csrf_exempt
def get_next_build_number(request, application, group_id, artifact_id):
    pds_log.logger.info("Asking for next build number for:")
    pds_log.logger.info("    Application: %s, Artifact: %s:%s" % (application, group_id, artifact_id))
    # Getting the artifact versions
    output = "0:0"
    try:
        application = models.Application.objects.get(name=application)
        artifact = models.Artifact.objects.get(group_id=group_id, artifact_id=artifact_id)
    except models.Application.DoesNotExist:
        pds_log.logger.info("    Application %s doesn't exist" % application)
        return HttpResponse(output, status=404)
    except models.Artifact.DoesNotExist:
        pds_log.logger.info("    Artifact %s:%s doesn't exist" % (group_id, artifact_id))
        return HttpResponse(output, status=404)
    if application.build_number is None:
        next_build_number_app = 1
    else:
        next_build_number_app = application.build_number + 1
    if artifact.build_number is None:
        next_build_number_art = 1
    else:
        next_build_number_art = artifact.build_number + 1
    # Updating the build number
    application.build_number = next_build_number_app
    artifact.build_number = next_build_number_art
    application.save()
    artifact.save()
    output = str(next_build_number_app) + ":" + str(next_build_number_art)
    return HttpResponse(output, status=201)


@csrf_exempt
def get_next_build_number_application(request, application):
    pds_log.logger.info("Asking for next build number for:")
    pds_log.logger.info("    Application: %s" % application)
    # Getting the artifact versions
    output = "0"
    try:
        application = models.Application.objects.get(name=application)
    except models.Application.DoesNotExist:
        pds_log.logger.info("    Application %s doesn't exist" % application)
        return HttpResponse(output, status=404)
    if application.build_number is None:
        next_build_number_app = 1
    else:
        next_build_number_app = application.build_number + 1
    # Updating the build number
    application.build_number = next_build_number_app
    application.save()
    output = str(next_build_number_app)
    return HttpResponse(output, status=201)


@csrf_exempt
def create_new_application_version(request):
    if request.method == 'POST':
        pass
    else:
        return HttpResponseServerError("Method not supported!")
    json_data = json.loads(request.body.decode())
    pds_log.logger.info(json_data)
    try:
        application = json_data['application']
        group_id = json_data['group_id']
        artifact_id = json_data['artifact_id']
        created_from_branch = json_data['created_from_branch']
        app_version = json_data['app_version']
        art_version = json_data['art_version']
        build_url = json_data.get('build_url', None)
        changelog = json_data['changelog']
        email = json_data.get('email', None)
        pds_log.logger.info("Asking for creating new application version:")
        pds_log.logger.info("    application: %s" % application)
        pds_log.logger.info("    group_id: %s" % group_id)
        pds_log.logger.info("    artifact_id: %s" % artifact_id)
        pds_log.logger.info("    created_from_branch: %s" % created_from_branch)
        pds_log.logger.info("    app_version: %s" % app_version)
        pds_log.logger.info("    art_version: %s" % art_version)
        pds_log.logger.info("    build_url=%s", build_url)
        pds_log.logger.info("    changelog: %s" % changelog)
        pds_log.logger.info("    email: %s" % email)
    except KeyError:
        return HttpResponseServerError("Malformed data!")
    try:
        app = models.Application.objects.get(name=application)
        art = models.Artifact.objects.get(group_id=group_id, artifact_id=artifact_id)
    except models.Application.DoesNotExist:
        return HttpResponseServerError("Application doesn't exist")
    except models.Artifact.DoesNotExist:
        return HttpResponseServerError("Artifact doesn't exist")
    # Get states available
    ssv = models.StateApplicationVersion.objects.get_or_create(name='Inicial')[0]
    sav = models.StateArtifactVersion.objects.get_or_create(name='Inicial')[0]
    app_ver = models.ApplicationVersion.objects.create(name=app_version,
                                                       application=app,
                                                       state_application_version=ssv,
                                                       created_from_branch=created_from_branch,
                                                       email=email)
    history_record = models.ApplicationVersionHistory(application_version=app_ver,
                                                      state_application_version=ssv)
    history_record.save()
    # Getting the last version for the application
    try:
        if created_from_branch.startswith('release-'):
            startswith = app_version.split('-B')[0]
            last_application_version = models.ApplicationVersion.objects.filter(
                application__name=application, name__startswith=startswith).exclude(name=app_version).order_by("-created")[0]
        else:
            # last_application_version = models.ApplicationVersion.objects.filter(
            #     application__name=application, created_from_branch__startswith='feature').exclude(name=app_version).order_by("-created")[0]
            last_application_version = models.ApplicationVersion.objects.filter(
                application__name=application).exclude(
                name=app_version).order_by("-created")[0]
        pds_log.logger.info("    Application obtained ==> %s" % last_application_version.name)
        for a_v in last_application_version.artifact_version.exclude(artifact=art):
            pds_log.logger.info("-> %s" % a_v)
            app_ver.artifact_version.add(a_v)
    except IndexError:
        pds_log.logger.info("There aren't any versions available")

    new_a_v = models.ArtifactVersion.objects.create(name=art_version, artifact=art,
                                                    state_artifact_version=sav, build_url=build_url,
                                                    created_from_branch=created_from_branch,
                                                    email=email)
    history_record = models.ArtifactVersionHistory(artifact_version=new_a_v,
                                                   state_artifact_version=sav)
    history_record.save()
    # New records for Changelog
    for cl in changelog.split("@@@"):
        models.ArtifactVersionChangeLog.objects.create(name=cl, artifact_version=new_a_v)
    app_ver.artifact_version.add(new_a_v)
    return HttpResponse(status=201)


# This view is for getting the projects available in BitBucket
@csrf_exempt
def get_available_projects_bitbucket(request):
    pds_log.logger.info("Asking for available projects in BitBucket")
    r = requests.get('https://bitbucket.vocento.com/rest/api/1.0/projects?limit=10000',
                     auth=(settings.USER_BITBUCKET, settings.PASSWORD_BITBUCKET))
    output = []
    for p in r.json()['values']:
        output.append({"name": p['key'] + " - " + p['name'], "value": p['key']})

    return JsonResponse(output, safe=False)


# This view is for getting the projects available in BitBucket
@csrf_exempt
def get_available_repositories_bitbucket(request, project):
    pds_log.logger.info("Asking for available repositories in BitBucket in " + project)
    r = requests.get('https://bitbucket.vocento.com/rest/api/1.0/projects/' + project + '/repos?limit=10000',
                     auth=(settings.USER_BITBUCKET, settings.PASSWORD_BITBUCKET))
    output = []
    for p in r.json()['values']:
        output.append(p['slug'])

    return JsonResponse(output, safe=False)


# This view is for getting the technology types available
@csrf_exempt
def get_technology_types_available(request):
    pds_log.logger.info("Asking for technology types")
    technology_types_available = models.TechnologyType.objects.all()
    output = []
    for t_t in technology_types_available:
        output.append(t_t.name)

    return JsonResponse(output, safe=False)


# This view is for getting the artifacts belonging to a technology type
@csrf_exempt
def get_artifacts_by_technology_type(request, technology_type):
    pds_log.logger.info("Asking for artifacts belonging to " + technology_type)
    try:
        t_t = models.TechnologyType.objects.get(name=technology_type)
    except models.TechnologyType.DoesNotExist:
        t_t = None
    artifacts = models.Artifact.objects.filter(technology_type=t_t)
    output = []
    for a in artifacts:
        output.append(a.artifact_id)

    return JsonResponse(output, safe=False)


# This view is for getting the artifacts belonging to a technology type and a group_id
@csrf_exempt
def get_artifacts_by_technology_type_and_application(request, technology_type, application):
    pds_log.logger.info("Asking for artifacts belonging to " + technology_type + " and its application is " + application)
    try:
        t_t = models.TechnologyType.objects.get(name=technology_type)
    except models.TechnologyType.DoesNotExist:
        t_t = None
    artifacts = models.Artifact.objects.filter(application__name=application, technology_type=t_t)
    output = []
    for a in artifacts:
        output.append(a.artifact_id)

    return JsonResponse(output, safe=False)


# This view is for getting the groups ids belonging to a technology type
@csrf_exempt
def get_group_id_by_technology_type(request, technology_type):
    pds_log.logger.info("Asking for groups ids belonging to " + technology_type)
    try:
        t_t = models.TechnologyType.objects.get(name=technology_type)
    except models.TechnologyType.DoesNotExist:
        t_t = None
    output = list(set(models.Artifact.objects.filter(technology_type=t_t).values_list('group_id', flat=True)))

    return JsonResponse(output, safe=False)


# This view is for creating new release branches
@csrf_exempt
def create_release_branches(request, application, version, new_version):
    pds_log.logger.info("Asking for creating new release branches")

    try:
        application_version = models.ApplicationVersion.objects.get(name=version, application__name=application)
    except models.ApplicationVersion.DoesNotExist:
        return HttpResponseServerError("Application version doesn't exist!")

    for a_v in application_version.artifact_version.all():
        pds_log.logger.info("Repository git = %s" % a_v.artifact.repository_git)
        repository_ssh = a_v.artifact.repository_git.replace(
            'ssh://git@bitbucket.vocento.com:7999',
            'https://bitbucket.vocento.com:443/rest/api/latest/projects')
        slug_ssh = repository_ssh.split('/')[-1]
        slug = slug_ssh.replace('.git', '')
        url_create_branch = repository_ssh.replace(slug_ssh, 'repos/' + slug + '/branches')
        url_delete_branch = url_create_branch.replace('rest/api/latest/projects', 'rest/branch-utils/latest/projects')
        pds_log.logger.info("URL create branch = %s" % url_create_branch)
        pds_log.logger.info("URL delete branch = %s" % url_delete_branch)
        # Setting parameters for creating release branch
        version = version.split('-B')[0]
        params_delete_release_branches = {'name': 'release-' + version}
        params_create_release_branches = {'name': 'release-' + version, 'startPoint': a_v.name}
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
        try:
            # Delete branch
            request_delete = requests.delete(url_delete_branch,
                                             auth=(settings.USER_BITBUCKET, settings.PASSWORD_BITBUCKET),
                                             data=json.dumps(params_delete_release_branches), headers=headers)
            pds_log.logger.info("Request delete code = %s" % request_delete.status_code)
            # Create branch
            request_create = requests.post(url_create_branch,
                                           auth=(settings.USER_BITBUCKET, settings.PASSWORD_BITBUCKET),
                                           data=json.dumps(params_create_release_branches), headers=headers)
            if request_create.status_code != 200:
                pds_log.logger.error(request_create.status_code)
                return HttpResponseServerError(request_create.status_code)
        except requests.exceptions.RequestException as e:
            pds_log.logger.error("Error al borrar/crear la rama en BitBucket")
            pds_log.logger.error(e)
            return HttpResponseServerError("Error al borrar/crear la rama en BitBucket")

        # We've created the releases branches. Now we must update the pom version
        params_job_update = {'repositorio': a_v.artifact.repository_git,
                             'pom': a_v.artifact.pom_directory,
                             'version': new_version
                             }
        # Data for the tasks engine
        if settings.TASKS_ENGINE == 'rundeck':
            data = {
                'options': params_job_update
            }
        elif settings.TASKS_ENGINE == 'jenkins':
            data = params_job_update
        else:
            data = {}
        pds_log.logger.info("-> Data = %s" % data)
        if settings.TASKS_ENGINE == 'rundeck':
            url = settings.DEPLOY_SERVER_URL + settings.JOB_UPDATE_POM_VERSION
            headers = {'Content-type': 'application/json', 'Accept': 'application/json',
                       'X-Rundeck-Auth-Token': settings.AUTH_TOKEN}
            pds_log.logger.info("-> Url = %s" % url)
            pds_log.logger.info("-> Headers = %s" % headers)
            try:
                r = requests.post(url, data=json.dumps(data), headers=headers)
                pds_log.logger.info("-> Permalink = %s" % r.json()['permalink'])
            except requests.exceptions.RequestException as e:
                pds_log.logger.error("Error al conectar con el sistema de despliegue")
                pds_log.logger.error(e)
                return HttpResponseServerError("KO")
            except KeyError as e:
                pds_log.logger.error("Error al conectar con el sistema de despliegue")
                pds_log.logger.error(e)
                return HttpResponseServerError("KO")
        elif settings.TASKS_ENGINE == 'jenkins':
            pass
        else:
            pass

    return HttpResponse("OK")


@csrf_exempt
def update_git_repository(request):
    pds_log.logger.info("New request for changing the git repository")
    if request.method == 'POST':
        json_data = json.loads(request.body.decode())
        pds_log.logger.info("Data JSON loaded")
        try:
            old_git_repository = json_data['old_git_repository']
            old_project_key = old_git_repository.split("/")[-2].upper()
            new_git_repository = json_data['new_git_repository']
            new_project_key = new_git_repository.split("/")[-2].upper()
            pds_log.logger.info("Data received:")
            pds_log.logger.info("    old_git_repository=%s", old_git_repository)
            pds_log.logger.info("    old_project_key=%s", old_project_key)
            pds_log.logger.info("    new_git_repository=%s", new_git_repository)
            pds_log.logger.info("    new_project_key=%s", new_project_key)
        except KeyError:
            return HttpResponseServerError("Malformed data!")
        except IndexError:
            return HttpResponseServerError("It wasn't possible to get the project key!")

        try:
            pds_log.logger.info("Loading the old repository")
            old_git_repository_bdd = vocteams_models.RepositoryGit.objects.get(name=old_git_repository,
                                                                               project_key=old_project_key)
            pds_log.logger.info("Old repository loaded")
        except vocteams_models.RepositoryGit.DoesNotExist:
            msg = "Old repository doesn't exist!"
            pds_log.logger.info(msg)
            return HttpResponse(status=404)

        # Getting or creating the new git repository
        pds_log.logger.info("Getting or creating the new repository")
        new_git_repository_bdd = vocteams_models.RepositoryGit.objects.get_or_create(name=new_git_repository,
                                                                                     project_key=new_project_key)[0]
        pds_log.logger.info("New repository: %s-%s" % (new_git_repository_bdd.id, new_git_repository_bdd))

        # Update branches
        for branch in old_git_repository_bdd.branch_git.all():
            pds_log.logger.info("Adding branch = %s" % branch)
            new_git_repository_bdd.branch_git.add(branch)

        # Update software solutions
        pds_log.logger.info("Updating software solutions")
        for ss in vocteams_models.SoftwareSolution.objects.filter(repository_git=old_git_repository_bdd):
            pds_log.logger.info("Updating %s ..." % ss)
            ss.repository_git.add(new_git_repository_bdd)
            ss.repository_git.remove(old_git_repository_bdd)
            pds_log.logger.info("%s updated" % ss)

        return HttpResponse(status=201)

    return HttpResponseServerError("Method not allowed!")
