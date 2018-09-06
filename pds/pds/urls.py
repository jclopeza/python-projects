"""pds URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import TemplateView
from django.contrib.auth.views import login, logout

import dashboard.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('api.urls')),
    url(r'^password/$', dashboard.views.change_password, name='change_password'),
    url(r'^password-success/$', TemplateView.as_view(template_name="accounts/change_password_success.html"), name='change-password-success'),
    url(r'^applications/$', dashboard.views.list_applications, name='applications'),
    url(r'^application-detail/(?P<pk>[0-9]+)/$', dashboard.views.application_detail, name='application-details'),
    url(r'^applications-environments/$', dashboard.views.list_applications_environments, name='applications-environments'),
    url(r'^application/version/(?P<pk>[0-9]+)/$', dashboard.views.list_application_versions, name='application-versions'),
    url(r'^application/versions-available/(?P<pk>[0-9]+)/$', dashboard.views.list_application_versions_available, name='versions-available'),
    url(r'^application/delete/(?P<pk>[0-9]+)/$', dashboard.views.application_version_delete, name='application-delete'),
    url(r'^application/version/components/(?P<pk>[0-9]+)/$', dashboard.views.list_application_versions_components, name='application-versions-components'),
    url(r'^artifact/details/(?P<pk>[0-9]+)/$', dashboard.views.artifact_details, name='artifact-details'),
    url(r'^artifact/delete/(?P<pk>[0-9]+)/$', dashboard.views.artifact_version_delete, name='artifact-delete'),
    url(r'^artifact/version/details/(?P<pk>[0-9]+)/$', dashboard.views.artifact_version_details, name='artifact-version-details'),
    url(r'^update-maturity-model/(?P<pk>[0-9]+)/$', dashboard.views.update_maturity_level_application, name='update-maturity-model'),
    url(r'^deploy/$', dashboard.views.deploy_application, name='deploy-application'),
    url(r'^create-infrastructure-project/$', dashboard.views.create_infrastructure_project, name='create-infrastructure-project'),
    url(r'^delta/versions/$', dashboard.views.analysis_delta_versions, name='delta-versions'),
    url(r'^delta/environments/$', dashboard.views.analysis_delta_environments, name='delta-environments'),
    url(r'^accounts/login/$', login),
    url(r'^accounts/logout/$', logout, {'next_page': '/'}),
    url(r'^accounts/profile/$', TemplateView.as_view(template_name="index.html")),
    url(r'^$', TemplateView.as_view(template_name="index.html")),
]
