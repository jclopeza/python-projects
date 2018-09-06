from django.contrib import admin
from vocteams import models


# Register your models here

class BranchGitAdmin(admin.ModelAdmin):
    list_display = ('name',)


class TeamVocentoAdmin(admin.ModelAdmin):
    list_display = ('name', 'created')
    filter_horizontal = ('software_solution',)


class SoftwareSolutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'created')
    search_fields = ('name',)
    filter_horizontal = ('repository_git', 'job_jenkins',)


class RepositoryGitAdmin(admin.ModelAdmin):
    list_display = ('name', 'project_key',)
    search_fields = ('name', 'project_key',)
    filter_horizontal = ('branch_git',)


class JobJenkinsAdmin(admin.ModelAdmin):
    list_display = ('name', 'jenkins_server',)
    search_fields = ('name', 'jenkins_server',)


admin.site.register(models.BranchGit, BranchGitAdmin)
admin.site.register(models.TeamVocento, TeamVocentoAdmin)
admin.site.register(models.SoftwareSolution, SoftwareSolutionAdmin)
admin.site.register(models.RepositoryGit, RepositoryGitAdmin)
admin.site.register(models.JobJenkins, JobJenkinsAdmin)
