FROM nginx

RUN echo "deb http://deb.debian.org/debian/ buster main contrib non-free" > /etc/apt/sources.list \
        && apt-get update \
        && apt-get install -y python-pip python-setuptools --no-install-recommends --no-install-suggests \
        && pip install requests_unixsocket

COPY config/scripts /scripts/

COPY config/proxy/stream.conf /etc/nginx/stream/stream.conf
COPY config/proxy/default.conf /etc/nginx/conf.d/default.conf

RUN echo "include /etc/nginx/stream/stream.conf;" >> /etc/nginx/nginx.conf \
        && rm -rf /var/lib/apt/lists/* \
# if we have leftovers from building, let's purge them (including extra, unnecessary build deps)
	&& if [ -n "$tempDir" ]; then \
		apt-get purge -y --auto-remove \
		&& rm -rf "$tempDir" /etc/apt/sources.list.d/temp.list; \
	fi

STOPSIGNAL SIGTERM

CMD ["/usr/bin/python", "/scripts/links.py"]
