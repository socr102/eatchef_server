from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Template
from django.template.loader import get_template
from rest_framework.reverse import reverse

if TYPE_CHECKING:
    from users.models import User

SEND_CONFIRM_EMAIL_SUBJECT = 'Email confirmation'
SEND_NEW_USER_GREETING = 'Welcome to EatChefs!'
SEND_RESET_PASSWORD_SUBJECT = 'Password recovery of your account'

SEND_NEW_COMMENTS_IN_RECIPE = 'New comments in recipe'
SEND_RECIPE_CREATED = 'Successful Submission: {title}'
SEND_RECIPE_APPROVED = 'Dish Approved: {title}'
SEND_RECIPE_REJECTED = 'Dish Rejected: {title}'

SEND_NEW_COMMENTS_IN_CHEF_PENCIL_RECORD = 'New comments in Chef Pencil\'s record'
SEND_CHEF_PENCIL_RECORD_CREATED = 'Successful Submission: {title}'
SEND_CHEF_PENCIL_RECORD_APPROVED = 'Chef Pencil\'s record Approved: {title}'
SEND_CHEF_PENCIL_RECORD_REJECTED = 'Chef Pencil\'s record Rejected: {title}'

SEND_PROMO1 = ''
SEND_PROMO6 = ''


def __main_client_terms_endpoint():
    return '%s%s' % (settings.BASE_CLIENT_URL, '/terms-of-service')


def __send_mail(plaintext: Template, html: Template, to_emails, context=None,
                subject='Info', from_email=settings.EMAIL_FROM):
    if context is None:
        context = {}

    context['BASE_CLIENT_URL'] = settings.BASE_CLIENT_URL
    context['logo_url'] = f'{settings.BASE_CLIENT_URL}/images/logo.png'
    text_content = plaintext.render(context)
    html_content = html.render(context)
    msg = EmailMultiAlternatives(subject=subject, body=text_content,
                                 from_email=from_email, to=to_emails)
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_confirm_email(emails: list, code: str, user: User):
    __send_mail(
        plaintext=get_template('emails/users/confirm/content.txt'),
        html=get_template('emails/users/confirm/content.html'),
        context={
            'url': '%s%s' % (settings.BASE_CLIENT_URL, '/confirm/email/%s' % code),
            'user': user,
            'email_from': settings.EMAIL_FROM
        },
        subject=SEND_CONFIRM_EMAIL_SUBJECT,
        to_emails=emails
    )


def send_reset_password_message(emails: list, new_password: str):
    __send_mail(
        plaintext=get_template('emails/users/reset/content.txt'),
        html=get_template('emails/users/reset/content.html'),
        context={
            'new_password': new_password,
            'auth_url': settings.BASE_CLIENT_URL
        },
        subject=SEND_RESET_PASSWORD_SUBJECT,
        to_emails=emails
    )


def send_new_user_greeting(emails: list, user: 'User'):
    __send_mail(
        plaintext=get_template('emails/users/new_user_greeting.txt'),
        html=get_template('emails/users/new_user_greeting.html'),
        context={
            'url': settings.BASE_CLIENT_URL + '/profile/account-settings',
            'site_url': settings.BASE_CLIENT_URL,
            'user': user
        },
        subject=SEND_NEW_USER_GREETING,
        to_emails=emails
    )


def send_promo1(emails: list, user: 'User'):
    __send_mail(
        plaintext=get_template('emails/users/promo1.txt'),
        html=get_template('emails/users/promo1.html'),
        context={
            'url': settings.BASE_CLIENT_URL + '/profile/account-settings',
            'site_url': settings.BASE_CLIENT_URL,
            'user': user
        },
        subject=SEND_PROMO1,
        to_emails=emails
    )


def send_promo6(emails: list, user: 'User'):
    __send_mail(
        plaintext=get_template('emails/users/promo6.txt'),
        html=get_template('emails/users/promo6.html'),
        context={
            'url': settings.BASE_CLIENT_URL + '/profile/account-settings',
            'site_url': settings.BASE_CLIENT_URL,
            'user': user
        },
        subject=SEND_PROMO6,
        to_emails=emails
    )


# Recipes

def send_new_comments_for_recipe(emails: list, user: 'User', recipe, comments):
    __send_mail(
        plaintext=get_template('emails/recipe/new_comments_in_recipe.txt'),
        html=get_template('emails/recipe/new_comments_in_recipe.html'),
        context={
            'url': settings.BASE_CLIENT_URL + f'/recipe/{recipe.pk}',
            'user': user,
            'recipe': recipe,
            'comments': comments,
            'image_url': _get_recipe_image_url(recipe),
        },
        subject=SEND_NEW_COMMENTS_IN_RECIPE,
        to_emails=emails
    )


def _get_recipe_image_url(recipe):
    ri = recipe.images.first()
    return ri.file.storage.url(name=ri.file.name) if ri else ''


def send_recipe_created_email(emails: list, user: 'User', recipe):
    from recipe.models import Recipe

    __send_mail(
        plaintext=get_template('emails/recipe/recipe_created.txt'),
        html=get_template('emails/recipe/recipe_created.html'),
        context={
            'url': settings.BASE_CLIENT_URL + f'/recipe/{recipe.pk}',
            'uploads_url': settings.BASE_CLIENT_URL + '/my-uploads',
            'user': user,
            'recipe': recipe,
            'image_url': _get_recipe_image_url(recipe),
        },
        subject=SEND_RECIPE_CREATED.format(title=recipe.title),
        to_emails=emails
    )


def send_recipe_review_result_email(emails: list, user: 'User', recipe):
    from recipe.models import Recipe

    if recipe.status == Recipe.Status.ACCEPTED:

        __send_mail(
            plaintext=get_template('emails/recipe/recipe_approved.txt'),
            html=get_template('emails/recipe/recipe_approved.html'),
            context={
                'url': settings.BASE_CLIENT_URL + f'/recipe/{recipe.pk}',
                'uploads_url': settings.BASE_CLIENT_URL + '/my-uploads',
                'user': user,
                'recipe': recipe,
                'image_url': _get_recipe_image_url(recipe)
            },
            subject=SEND_RECIPE_APPROVED.format(title=recipe.title),
            to_emails=emails
        )

    elif recipe.status == Recipe.Status.REJECTED:

        __send_mail(
            plaintext=get_template('emails/recipe/recipe_rejected.txt'),
            html=get_template('emails/recipe/recipe_rejected.html'),
            context={
                'url': settings.BASE_CLIENT_URL + f'/recipe/{recipe.pk}',
                'uploads_url': settings.BASE_CLIENT_URL + '/my-uploads',
                'user': user,
                'recipe': recipe,
                'image_url': _get_recipe_image_url(recipe),
                'rejection_reason': recipe.rejection_reason
            },
            subject=SEND_RECIPE_REJECTED.format(title=recipe.title),
            to_emails=emails
        )


# Chef Pencil's Record

def send_new_comments_for_chef_pencils_record(emails: list, user: 'User', chef_pencil_record, comments):
    __send_mail(
        plaintext=get_template('emails/chef_pencils/new_comments_in_chef_pencil_record.txt'),
        html=get_template('emails/recipe/new_comments_in_chef_pencil_record.html'),
        context={
            'url': settings.BASE_CLIENT_URL + f'/chef-pencil/{chef_pencil_record.pk}',
            'user': user,
            'chef_pencil_record': chef_pencil_record,
            'comments': comments,
            'image_url': _get_chef_pencil_record_image_url(chef_pencil_record),
        },
        subject=SEND_NEW_COMMENTS_IN_CHEF_PENCIL_RECORD,
        to_emails=emails
    )


def _get_chef_pencil_record_image_url(cp):
    if cp:
        main_image = cp.images.filter(main_image=True).first()
        if main_image:
            return main_image.image.storage.url(name=main_image.image.name)
    return ''


def send_chef_pencils_record_created_email(emails: list, user: 'User', chef_pencil_record):

    __send_mail(
        plaintext=get_template('emails/chef_pencil_records/chef_pencil_record_created.txt'),
        html=get_template('emails/chef_pencil_records/chef_pencil_record_created.html'),
        context={
            'url': settings.BASE_CLIENT_URL + f'/chef-pencil/{chef_pencil_record.pk}',
            'uploads_url': settings.BASE_CLIENT_URL + '/chef-pencil/upload',
            'user': user,
            'chef_pencil_record': chef_pencil_record,
            'image_url': _get_chef_pencil_record_image_url(chef_pencil_record),
        },
        subject=SEND_CHEF_PENCIL_RECORD_CREATED.format(title=chef_pencil_record.title),
        to_emails=emails
    )


def send_chef_pencils_record_review_result_email(emails: list, user: 'User', chef_pencil_record):
    from chef_pencils.models import ChefPencilRecord

    if chef_pencil_record.status == ChefPencilRecord.Status.APPROVED:

        __send_mail(
            plaintext=get_template('emails/chef_pencil_records/chef_pencil_record_approved.txt'),
            html=get_template('emails/chef_pencil_records/chef_pencil_record_approved.html'),
            context={
                'url': settings.BASE_CLIENT_URL + f'/chef-pencil/{chef_pencil_record.pk}',
                'uploads_url': settings.BASE_CLIENT_URL + '/chef-pencil/upload',
                'user': user,
                'recipe': chef_pencil_record,
                'image_url': _get_chef_pencil_record_image_url(chef_pencil_record)
            },
            subject=SEND_CHEF_PENCIL_RECORD_APPROVED.format(title=chef_pencil_record.title),
            to_emails=emails
        )

    elif chef_pencil_record.status == ChefPencilRecord.Status.REJECTED:

        __send_mail(
            plaintext=get_template('emails/chef_pencil_records/chef_pencil_record_rejected.txt'),
            html=get_template('emails/chef_pencil_records/chef_pencil_record_rejected.html'),
            context={
                'url': settings.BASE_CLIENT_URL + f'/chef-pencil/{chef_pencil_record.pk}',
                'uploads_url': settings.BASE_CLIENT_URL + '/chef-pencil/upload',
                'user': user,
                'chef_pencils_record': chef_pencil_record,
                'image_url': _get_chef_pencil_record_image_url(chef_pencil_record),
                'rejection_reason': chef_pencil_record.rejection_reason
            },
            subject=SEND_CHEF_PENCIL_RECORD_REJECTED.format(title=chef_pencil_record.title),
            to_emails=emails
        )
