# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.test import TestCase
from django.test.utils import override_settings
import factory

from . import execute_once, terminate, MethodExecution, NotExecuted


class InstanceOnlyDescriptor(object):
    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError('You must access this attribute from a class instance.')
        else:
            return 'foo'


class Message(models.Model):
    sent_via_email = models.BooleanField(default=False)
    sent_via_snail_mail = models.BooleanField(default=False)
    sender_email = models.EmailField()
    recipient_email = models.EmailField()
    recipient_prefers_snail_mail = models.BooleanField(default=False)
    subject = models.CharField(max_length=128)
    body = models.TextField()

    instance_only_attribute = InstanceOnlyDescriptor()

    @execute_once(Q(recipient_prefers_snail_mail=False))
    def send_via_email(self):
        send_mail(
            self.subject,
            self.body,
            self.sender_email,
            [self.recipient_email],
        )
        self.sent_via_email = True
        self.save()

    @execute_once(Q(recipient_prefers_snail_mail=True))
    def send_via_snail_mail(self):
        if settings.POSTMAN_AVAILABLE:
            self.sent_via_snail_mail = True
            self.save()
        else:
            raise NotExecuted()


class MessageFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Message
    sender_email = factory.Sequence(lambda n: 'sender_{}@example.com'.format(n))
    recipient_email = factory.Sequence(lambda n: 'recipient_{}@example.com'.format(n))
    subject = factory.Sequence(lambda n: 'Subject no. {}'.format(n))
    body = factory.Sequence(lambda n: 'Body no. {}'.format(n))


class BirthdayGift(models.Model):
    sent = models.BooleanField(default=False)
    birthday_date = models.DateField()

    @execute_once(lambda cls: Q(birthday_date__lte=datetime.date.today()))
    def send(self):
        self.sent = True
        self.save()


@override_settings(POSTMAN_AVAILABLE=True)
class TerminatorTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.message_content_type = ContentType.objects.get_for_model(Message)

    def test_sending_via_email_works(self):
        message = MessageFactory()
        self.assertFalse(message.sent_via_email)
        message.send_via_email()
        message = Message.objects.get(pk=message.pk)
        self.assertTrue(message.sent_via_email)
        self.assertEqual(len(mail.outbox), 1)

    def test_marked_methods_are_executed_only_once_by_terminator(self):
        message = MessageFactory()

        terminate()

        message = Message.objects.get(pk=message.pk)
        self.assertTrue(message.sent_via_email)
        message.sent_via_email = False
        message.save()

        terminate()

        message = Message.objects.get(pk=message.pk)
        self.assertFalse(message.sent_via_email)

    def test_marked_methods_can_be_executed_twice_by_terminator_if_explicitly_allowed(self):
        """Methods can be executed multiple times if execution info is deleted."""
        message = MessageFactory()

        terminate()

        message = Message.objects.get(pk=message.pk)
        self.assertTrue(message.sent_via_email)
        message.sent_via_email = False
        message.save()

        MethodExecution.objects.filter(
            instance_id=message.id,
            content_type=self.message_content_type,
            method_name='send_via_email',
        ).delete()

        terminate()

        message = Message.objects.get(pk=message.pk)
        self.assertTrue(message.sent_via_email)

    def test_marked_methods_are_executed_only_for_filtered_objects(self):
        snail_message = MessageFactory(recipient_prefers_snail_mail=True)
        fast_message = MessageFactory(recipient_prefers_snail_mail=False)

        terminate()

        snail_message = Message.objects.get(pk=snail_message.pk)
        self.assertTrue(snail_message.sent_via_snail_mail)
        self.assertFalse(snail_message.sent_via_email)

        fast_message = Message.objects.get(pk=fast_message.pk)
        self.assertFalse(fast_message.sent_via_snail_mail)
        self.assertTrue(fast_message.sent_via_email)

    def test_method_execution_can_be_abandoned(self):
        message = MessageFactory(recipient_prefers_snail_mail=True)
        with override_settings(POSTMAN_AVAILABLE=False):
            terminate()
        self.assertFalse(
            MethodExecution.objects.filter(
                instance_id=message.id,
                content_type=self.message_content_type,
                method_name='send_via_snail_mail',
            ).exists()
        )
        message = Message.objects.get(pk=message.pk)
        self.assertFalse(message.sent_via_snail_mail)

    def test_execution_condition_can_be_callable(self):
        gift_from_future = BirthdayGift(birthday_date=datetime.date.today() + datetime.timedelta(days=2))
        gift_from_future.save()

        gift_from_past = BirthdayGift(birthday_date=datetime.date.today() - datetime.timedelta(days=2))
        gift_from_past.save()

        terminate()

        gift_from_future = BirthdayGift.objects.get(pk=gift_from_future.pk)
        self.assertFalse(gift_from_future.sent)

        gift_from_past = BirthdayGift.objects.get(pk=gift_from_past.pk)
        self.assertTrue(gift_from_past.sent)

    def test_attribute_errors_are_ignored_when_examining_model_attributes(self):
        Message().instance_only_attribute
        self.assertRaises(AttributeError, getattr, Message, 'instance_only_attribute')

        terminate()
