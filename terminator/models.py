# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models


class MethodExecution(models.Model):
    """A single method execution on a concrete model instance."""

    content_type = models.ForeignKey(ContentType)
    instance_id = models.PositiveIntegerField()
    instance = generic.GenericForeignKey('content_type', 'object_id')

    method_name = models.TextField()
