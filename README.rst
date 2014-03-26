=================
django-terminator
=================

One-time execution of Django model methods, when model instance meets
specific conditions.

Examples
========
::

    import datetime

    from django.db import models
    from django.db.models import Q
    from terminator import execute_once


    class Message(models.Model):
        sent = models.BooleanField(default=False)
        sender_email = models.EmailField()
        recipient_email = models.EmailField()
        subject = models.CharField(max_length=128)
        body = models.TextField()

        @execute_once(Q())
        def send(self):
            # Some code which sends the email…
            pass


    class BirthdayGift(models.Model):
        birthday_date = models.DateField()

        @execute_once(lambda cls: Q(birthday_date__lte=datetime.date.today()))
        def send(self):
            # Some code which sends the gift…
            pass

Later::

    from terminator import terminate

    terminate()

For more extensive documentation, see the tests.
