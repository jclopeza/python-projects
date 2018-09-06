from django.conf.urls import url
from api import views

urlpatterns = [
    url(r'^create-new-artifact/$', views.create_new_artifact),
    url(r'^create-new-artifact-jenkinsfile/$', views.create_new_artifact_jenkinsfile),
    url(r'^update-ml-application/$', views.update_state_application_version_by_name),
    url(r'^post-receive-bitbucket/$', views.analyze_bitbucket_data),
    url(r'^get-available-applications/$', views.get_applications_available),
    url(r'^get-technology-types/$', views.get_technology_types_available),
    url(r'^get-group-id-by-technology-type/([\w\-\.]+)/$', views.get_group_id_by_technology_type),
    url(r'^get-artifacts-by-technology-type/([\w\-\.]+)/$', views.get_artifacts_by_technology_type),
    url(r'^get-artifacts-by-technology-type-and-application/([\w\-\.]+)/([\w\-\.]+)/$', views.get_artifacts_by_technology_type_and_application),
    url(r'^get-available-projects-bitbucket/$', views.get_available_projects_bitbucket),
    url(r'^get-available-repositories-bitbucket/([\w\-]+)/$', views.get_available_repositories_bitbucket),
    url(r'^get-available-versions/([\w\-]+)/(des|test|pre|pro)/$', views.get_versions_available),
    url(r'^get-available-versions/([\w\-]+)/(all)/(true)/$', views.get_versions_available),
    url(r'^get-artifacts-versions/([\w\-]+)/([\w\-\.]+)/$', views.get_artifacts_versions_of_application_version),
    url(r'^get-artifacts-versions/([\w\-]+)/$', views.get_artifacts_versions_of_application_version),
    url(r'^get-last-version/([\w\-]+)/$', views.get_last_version_of_application),
    url(r'^get-artifacts-versions/([\w\-]+)/([\w\-\.]+)/(infra)/$', views.get_artifacts_versions_of_application_version),
    url(r'^get-next-build-number/([\w\-]+)/([\w\-\.]+)/([\w\-]+)/$', views.get_next_build_number),
    url(r'^get-next-build-number-application/([\w\-]+)/$', views.get_next_build_number_application),
    url(r'^create-new-application-version/$', views.create_new_application_version),
    url(r'^create-new-release-branches/([\w\-]+)/([\w\-\.]+)/([\w\-\.]+)/$', views.create_release_branches),
    url(r'^update-git-repository/$', views.update_git_repository),
]
