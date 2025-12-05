#!/bin/bash

python manage.py collectstatic && sudo systemctl reload nginx && sudo systemctl restart django_projects.gunicorn.service
