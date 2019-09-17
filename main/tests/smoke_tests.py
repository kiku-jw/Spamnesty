import json

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from ..models import Domain, Message, ReplyTemplate


class SmokeTests(TestCase):
    def test_urls(self):
        response = self.client.get(reverse("main:home"))
        self.assertEqual(response.status_code, 200)


class WebhookTests(TestCase):
    def setUp(self):
        Domain.objects.create(name="example.com", company_name="Company")
        ReplyTemplate.objects.create(body="Hello!")

    def test_invalid_forwarding(self):
        self.assertEqual(len(mail.outbox), 0)

        response = self.client.post(
            reverse("main:forwarded-webhook"), data={"From": "hi@example.com"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("didn't work out", mail.outbox[0].subject)

    def test_forwarding_request(self):
        self.assertEqual(len(mail.outbox), 0)

        response = self.client.post(
            reverse("main:forwarded-webhook"),
            data=json.load(open("main/tests/forward_requests/1.json")),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("from\nhi@test.com.", mail.outbox[0].body)
        self.assertIn("CEO, Company", mail.outbox[1].body)

        mail.outbox = []

        response = self.client.post(
            reverse("main:forwarded-webhook"),
            data=json.load(open("main/tests/forward_requests/1.json")),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
        self.assertEqual(len(mail.outbox), 0)

        mail.outbox = []

        # A blacklisted email.
        response = self.client.post(
            reverse("main:forwarded-webhook"),
            data=json.load(open("main/tests/forward_requests/2.json")),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
        self.assertEqual(len(mail.outbox), 1)

    def test_email_request(self):
        self.assertEqual(len(mail.outbox), 0)

        response = self.client.post(
            reverse("main:email-webhook"),
            data=json.load(open("main/tests/email_requests/1.json")),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
        self.assertEqual(len(mail.outbox), 0)

        self.assertEqual(Message.objects.exclude(send_on=None).count(), 1)

        # An email where the sender is us.
        response = self.client.post(
            reverse("main:email-webhook"),
            data=json.load(open("main/tests/email_requests/2.json")),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
        self.assertEqual(len(mail.outbox), 0)

        self.assertEqual(Message.objects.exclude(send_on=None).count(), 1)
