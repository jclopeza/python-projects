from django.db import models

# Create your models here.


class BranchGit(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Branches git"

    def __str__(self):
        return self.name


class RepositoryGit(models.Model):
    project_key = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    branch_git = models.ManyToManyField(BranchGit, blank=True)
    has_branch_develop = models.NullBooleanField()
    has_branch_master = models.NullBooleanField()

    class Meta:
        ordering = ["project_key", "name"]
        verbose_name_plural = "Repositories git"

    def __str__(self):
        return '%s -> %s' % (self.project_key, self.name)


class JobJenkins(models.Model):
    jenkins_server = models.CharField(max_length=10)
    name = models.CharField(max_length=200)

    class Meta:
        ordering = ["jenkins_server", "name"]
        verbose_name_plural = "Jobs jenkins"

    def __str__(self):
        return '%s -> %s' % (self.jenkins_server, self.name)


class SoftwareSolution(models.Model):
    name = models.CharField(max_length=100)
    # The relation to the RepositoryGit table is many to many. A single repository can belong to many solutions.
    repository_git = models.ManyToManyField(RepositoryGit, blank=True)
    # The relation to the JobJenkins table is many to many. A single job can belong to many solutions.
    job_jenkins = models.ManyToManyField(JobJenkins, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Software solutions"

    def __str__(self):
        return self.name


class TeamVocento(models.Model):
    name = models.CharField(max_length=100)
    # The relation to the SoftwareSolution table is many to many. A single solution can belong to many teams.
    software_solution = models.ManyToManyField(SoftwareSolution, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Teams vocento"

    def __str__(self):
        return self.name
