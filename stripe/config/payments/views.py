import logging

import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


def checkout(request):
    context = {
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'price_id': settings.STRIPE_PRICE_ID,
        'setup_incomplete': not all(
            [settings.STRIPE_PUBLISHABLE_KEY, settings.STRIPE_SECRET_KEY, settings.STRIPE_PRICE_ID]
        ),
    }
    return render(request, 'payments/checkout.html', context)


@require_POST
def create_checkout_session(request):
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_ID:
        return JsonResponse(
            {'error': 'Stripe keys or Price ID missing. Check your environment variables.'},
            status=500,
        )

    success_url = request.build_absolute_uri(
        reverse('payments:success')
    ) + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = request.build_absolute_uri(reverse('payments:cancel'))

    try:
        session = stripe.checkout.Session.create(
            mode='payment',
            payment_method_types=['card'],
            line_items=[
                {
                    'price': settings.STRIPE_PRICE_ID,
                    'quantity': 1,
                }
            ],
            automatic_tax={'enabled': True},
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'integration_check': 'accept_a_payment'},
        )
    except stripe.error.StripeError as exc:
        logger.exception('Stripe error while creating checkout session')
        return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({'sessionId': session.id})


def success(request):
    session_id = request.GET.get('session_id')
    context = {'session_id': session_id}
    return render(request, 'payments/success.html', context)


def cancel(request):
    return render(request, 'payments/cancel.html')


@csrf_exempt
def stripe_webhook(request):
    if settings.STRIPE_WEBHOOK_SECRET == '':
        logger.warning('Stripe webhook secret missing. Ignoring webhook call.')
        return HttpResponse(status=400)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error('Invalid payload for Stripe webhook')
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error('Invalid Stripe signature')
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        logger.info('Checkout session completed: %s', session.get('id'))

    return HttpResponse(status=200)
