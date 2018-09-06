from django.db import models

# Create your models here.


class TTFB(models.Model):
    url = models.CharField(max_length=200)
    ip = models.CharField(max_length=20)
    dns_time = models.DecimalField(max_digits=20, decimal_places=6)
    connection_time = models.DecimalField(max_digits=20, decimal_places=6)
    time_to_first_byte = models.DecimalField(max_digits=20, decimal_places=6)
    total_time = models.DecimalField(max_digits=20, decimal_places=6)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.url
