# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType

from .models import MethodExecution


def execute_once(execution_condition):
    def execution_decorator(decorated_method):
        def new_method(self, *args, **kwargs):
            result = decorated_method(self, *args, **kwargs)
            execution = MethodExecution(
                method_name=decorated_method.__name__,
                content_type=ContentType.objects.get_for_model(self.__class__),
                instance_id=self.id,
            )
            execution.save()
            return result
        new_method._execution_condition = execution_condition
        new_method._execute_once = True
        new_method.__name__ = decorated_method.__name__
        return new_method
    return execution_decorator
