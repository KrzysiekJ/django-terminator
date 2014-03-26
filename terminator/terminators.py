# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .exceptions import NotExecuted
from .models import MethodExecution


def get_methods_executed_once(model):
    methods = []
    for attribute_name in dir(model):
        attribute = getattr(model, attribute_name)
        if getattr(attribute, '_execute_once', False):
            methods.append(attribute)
    return methods


def terminate():
    for content_type in ContentType.objects.all():
        model = content_type.model_class()
        for method in get_methods_executed_once(model):
            execution_condition = getattr(method, '_execution_condition', Q())
            if callable(execution_condition):
                execution_condition = execution_condition(model)

            instances_to_execute_method = model.objects\
                                               .filter(execution_condition)\
                                               .exclude(pk__in=MethodExecution.objects.filter(content_type=content_type, method_name=method.__name__).values_list('pk', flat=True))
            for instance in instances_to_execute_method:
                try:
                    method(instance)
                except NotExecuted:
                    pass
