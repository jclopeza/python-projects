from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class TechnologyType(models.Model):
    name = models.CharField(max_length=20)
    url_job_jenkins = models.CharField(max_length=120, blank=True)
    # el Name package tiene que ver con el tipo de empaquetado para Maven
    name_package = models.CharField(max_length=10, default='zip')
    # unpack tiene que ver a la hora de componer el DAR
    # se puede utilizar tambien para indicar como se debe hacer el despliegue
    # del artefacto
    unpack = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Application(models.Model):
    name = models.CharField(max_length=120)
    created = models.DateTimeField(auto_now_add=True)
    build_number = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Artifact(models.Model):
    group_id = models.CharField(max_length=120)
    artifact_id = models.CharField(max_length=40)
    repository_git = models.CharField(max_length=120, blank=True)
    application = models.ForeignKey(Application)
    technology_type = models.ForeignKey(TechnologyType)
    must_be_deployed = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    build_number = models.PositiveSmallIntegerField(blank=True, null=True)
    pom_directory = models.CharField(max_length=120, default='.mvn')

    class Meta:
        ordering = ["group_id", "artifact_id"]

    def __str__(self):
        return '%s:%s' % (self.group_id, self.artifact_id)


class StateApplicationVersion(models.Model):
    name = models.CharField(max_length=20)
    # Evitamos indicar por BDD el color sobre el estado de las versiones
    # color = models.CharField(max_length=20, default='active')

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class StateArtifactVersion(models.Model):
    name = models.CharField(max_length=20)
    # Evitamos indicar por BDD el color sobre el estado de las versiones
    # color = models.CharField(max_length=20, default='active')

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class ArtifactVersion(models.Model):
    name = models.CharField(max_length=40)
    artifact = models.ForeignKey(Artifact)
    state_artifact_version = models.ForeignKey(StateArtifactVersion)
    duration = models.PositiveSmallIntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    build_url = models.CharField(max_length=200, null=True)
    repository_url = models.CharField(max_length=200, null=True)
    created_from_branch = models.CharField(max_length=160, null=True)
    email = models.CharField(max_length=160, null=True)

    class Meta:
        ordering = ["-name"]

    def __str__(self):
        return '%s -> %s' % (self.artifact, self.name)


class ArtifactVersionHistory(models.Model):
    artifact_version = models.ForeignKey(ArtifactVersion)
    state_artifact_version = models.ForeignKey(StateArtifactVersion, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return '%s -> %s' % (self.artifact_version, self.state_artifact_version)


class ApplicationVersion(models.Model):
    name = models.CharField(max_length=40)
    application = models.ForeignKey(Application)
    state_application_version = models.ForeignKey(StateApplicationVersion)
    artifact_version = models.ManyToManyField(ArtifactVersion)
    created = models.DateTimeField(auto_now_add=True)
    created_from_branch = models.CharField(max_length=160, null=True)
    email = models.CharField(max_length=160, null=True)

    class Meta:
        ordering = ["-name"]

    def __str__(self):
        return '%s -> %s' % (self.application, self.name)


class ApplicationVersionHistory(models.Model):
    application_version = models.ForeignKey(ApplicationVersion)
    state_application_version = models.ForeignKey(StateApplicationVersion, null=True)
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, null=True)
    action = models.CharField(max_length=50, null=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return '%s -> %s' % (self.application_version, self.state_application_version)


class ArtifactVersionChangeLog(models.Model):
    name = models.CharField(max_length=250)
    artifact_version = models.ForeignKey(ArtifactVersion)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.name
