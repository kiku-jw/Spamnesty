from annoying.decorators import render_to
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import OuterRef
from django.db.models import Subquery
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils.crypto import constant_time_compare
from django.views.decorators.http import require_POST

from ..models import Conversation
from ..models import Message
from ..models import SpamCategory


@render_to("home.html")
def home(request):
    if not (request.get_host().startswith("spa.") or settings.DEBUG):
        return {"TEMPLATE": "fake.html"}

    # Prepare a subquery of the most recent sent message in every conversation.
    newest = Message.objects.filter(
        direction="S", conversation=OuterRef("pk")
    ).order_by("-timestamp")

    # Retrieve conversations, ordering them by the most recent sent message from the subquery.
    conversations = cache.get("conversations")
    if not conversations:
        conversations = (
            Conversation.objects.annotate(
                last_message_time=Subquery(newest.values("timestamp")[:1]),
                num_messages=Count("message"),
            )
            .filter(num_messages__gt=15, num_messages__lt=50)
            .order_by("-last_message_time")
        )
        cache.set("conversations", list(conversations), 12 * 60 * 60)

    paginator = Paginator(conversations, 50)
    page = request.GET.get("page")
    try:
        conversations = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        conversations = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        conversations = paginator.page(paginator.num_pages)

    return {"conversations": conversations}


@require_POST
def conversation_delete(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    if (
        constant_time_compare(request.GET.get("key"), conversation.secret_key)
        or request.user.is_staff
    ):
        messages.success(request, "The conversation has been deleted.")
        conversation.delete()
    else:
        messages.error(request, "The conversation's secret key was invalid.")
    return redirect("main:home")


def conversation_change(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    category = get_object_or_404(SpamCategory, pk=request.GET.get("category", ""))
    if (
        constant_time_compare(request.GET.get("key"), conversation.secret_key)
        or request.user.is_staff
    ):
        messages.success(request, "The conversation's category has been changed.")
        conversation.category = category
        conversation.classified = request.user.is_staff
        conversation.save()
    else:
        messages.error(request, "The conversation's secret key was invalid.")
    return redirect(conversation)


@render_to("conversation_view.html")
def conversation_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    own_conversation = constant_time_compare(
        request.GET.get("key"), conversation.secret_key
    )

    if own_conversation and "@" in conversation.reporter_email:
        other_conversations = (
            Conversation.objects.filter(reporter_email=conversation.reporter_email)
            .annotate(num_messages=Count("message"))
            .order_by("-num_messages", "-created")
        )
    else:
        other_conversations = []

    # Sort with the default category being last.
    categories = SpamCategory.objects.order_by("default", "name")
    return {
        "conversation": conversation,
        "own": own_conversation,
        "spam_categories": categories,
        "other_conversations": other_conversations,
    }
