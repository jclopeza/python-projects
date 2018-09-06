from django.contrib import admin

from dashboard import models


# Register your models here.

class TechnologyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'url_job_jenkins', 'name_package', 'unpack')


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ArtifactAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'artifact_id', 'repository_git', 'application',
                    'technology_type', 'must_be_deployed')


class StateApplicationVersionAdmin(admin.ModelAdmin):
    list_display = ('name',)


class StateArtifactVersionAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ArtifactVersionAdmin(admin.ModelAdmin):
    list_display = ('name', 'artifact', 'state_artifact_version',)


class ApplicationVersionAdmin(admin.ModelAdmin):
    list_display = ('name', 'application', 'state_application_version',)
    filter_horizontal = ('artifact_version',)


class ArtifactVersionChangeLogAdmin(admin.ModelAdmin):
    list_display = ('name', 'artifact_version',)


class ArtifactVersionHistoryAdmin(admin.ModelAdmin):
    list_display = ('artifact_version', 'state_artifact_version', 'created',)


class ApplicationVersionHistoryAdmin(admin.ModelAdmin):
    list_display = ('application_version', 'state_application_version', 'created',)


admin.site.register(models.TechnologyType, TechnologyTypeAdmin)
admin.site.register(models.Application, ApplicationAdmin)
admin.site.register(models.Artifact, ArtifactAdmin)
admin.site.register(models.StateApplicationVersion, StateApplicationVersionAdmin)
admin.site.register(models.StateArtifactVersion, StateArtifactVersionAdmin)
admin.site.register(models.ArtifactVersion, ArtifactVersionAdmin)
admin.site.register(models.ApplicationVersion, ApplicationVersionAdmin)
admin.site.register(models.ArtifactVersionChangeLog, ArtifactVersionChangeLogAdmin)
admin.site.register(models.ArtifactVersionHistory, ArtifactVersionHistoryAdmin)
admin.site.register(models.ApplicationVersionHistory, ApplicationVersionHistoryAdmin)
