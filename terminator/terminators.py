# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import functools

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from .exceptions import NotExecuted
from .models import MethodExecution


def get_methods_executed_once(models):
    methods = []
    for model in models:
        for attribute_name in dir(model):
            try:
                potential_method = getattr(model, attribute_name)
            except AttributeError:
                potential_method = None
            if getattr(potential_method, '_execute_once', False):
                methods.append(potential_method)
    return methods


@functools.total_ordering
class InheritanceSortingKey(object):
    """A wrapper for method which allows sorting by owner inheritance."""
    def __init__(self, method):
        self.method = method

    def __eq__(self, other):
        this_class = self.method.im_class
        other_class = other.method.im_class
        return not issubclass(this_class, other_class) and not issubclass(other_class, this_class)

    def __gt__(self, other):
        return issubclass(self.method.im_class, other.method.im_class)


def get_unique_methods_executed_once(models):
    """Return an iterable with methods executed once, containing only unique methods.

    In case when one method is contained in many models, the root one is chosen.
    """
    grouped_methods_dict = {}
    for method in get_methods_executed_once(models):
        if not method in grouped_methods_dict:
            grouped_methods_dict[method] = []
        grouped_methods_dict[method].append(method)
    grouped_methods = grouped_methods_dict.values()
    return {sorted(methods, key=InheritanceSortingKey)[0] for methods in grouped_methods}


def terminate():
    content_types = {content_type.model_class(): content_type for content_type in ContentType.objects.all()}
    for method in get_unique_methods_executed_once(content_types.keys()):
        model = method.im_class
        execution_condition = getattr(method, '_execution_condition', Q())
        if callable(execution_condition):
            execution_condition = execution_condition(model)

        instances_to_execute_method = model.objects\
                                           .filter(execution_condition)\
                                           .exclude(pk__in=MethodExecution.objects.filter(content_type=content_types[model], method_name=method.__name__).values_list('pk', flat=True))
        for instance in instances_to_execute_method:
            try:
                method(instance)
            except NotExecuted:
                pass
