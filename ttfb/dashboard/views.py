from django.shortcuts import render
from dashboard.models import TTFB
from .tables import TTFBTable
from django_tables2 import RequestConfig
import pycurl
import netifaces as ni


def get_ip_address(ifname):
    ip = ni.ifaddresses(ifname)[ni.AF_INET][0]['addr']
    return ip


def ttfb_find(request):
    empty = False
    # if request.method == 'POST':

    if 'url' in request.GET:
        url = request.GET['url']
        if not url:
            empty = True
        else:
            ip = get_ip_address('wlp2s0')
            # Podemos empezar con el calculo del TTFB
            c = pycurl.Curl()
            # Establecemos la URL, propiedades y ejecutamos
            c.setopt(pycurl.URL, url)
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            c.perform()
            # Calculamos los datos necesarios
            dns_time = c.getinfo(pycurl.NAMELOOKUP_TIME)
            connection_time = c.getinfo(pycurl.CONNECT_TIME)
            time_to_first_byte = c.getinfo(pycurl.STARTTRANSFER_TIME)
            total_time = c.getinfo(pycurl.TOTAL_TIME)
            # Cerramos la sesion
            c.close()
            registry = TTFB(url=url, ip=ip, dns_time=dns_time, connection_time=connection_time,
                            time_to_first_byte=time_to_first_byte, total_time=total_time)
            registry.save()
            message = 'TTFB: %r, IP: %r' % (time_to_first_byte, ip)
            table = TTFBTable(TTFB.objects.all())
            RequestConfig(request).configure(table)
            return render(request, 'ttfb_find.html', {'table': table})
    return render(request, 'ttfb_find.html', {'empty': empty})
