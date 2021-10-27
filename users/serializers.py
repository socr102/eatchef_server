from django.db.models.fields import IntegerField
from users.enums import UserTypes
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from django.utils import timezone
from main.validators import validate_images_file_max_size
from django.db.models import Count, Case, When, IntegerField, Q, query, Value
from recipe.models import Recipe
from recipe.models import SavedRecipe, Recipe
from django.db.models import Count, Case, When, IntegerField, Q, Sum
from social.models import Comment, CommentLike
from users.models import User
from itertools import chain
from django.contrib.postgres.aggregates import ArrayAgg

from users.errors import (
    EmailDoesNotExist,
    MailAlreadyExists,
    ResetCodeOrEmailInvalid,
    PasswordsDoNotMatch
)
from users.models import FavoriteRecipe, User, UserViewHistoryRecord, WorkExperienceRecord
from users.redis import NewMailCache
from users.tokens.serializers import TokenObtainPairSerializer
from users.services.user import UserService
from users.models import RoleModel
from recipe.models import (
    Recipe
)
import users
import recipe


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault('style', {})

        kwargs['style']['input_type'] = 'password'
        kwargs['write_only'] = True

        super().__init__(**kwargs)


class EmailField(serializers.EmailField):
    def __init__(self, **kwargs):
        kwargs.setdefault('style', {})

        kwargs['style']['input_type'] = 'email'

        super().__init__(**kwargs)


class CodeField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault('style', {})

        super().__init__(**kwargs)


class UserRegisterSerializer(serializers.ModelSerializer):
    email = EmailField(required=True)
    password = PasswordField(required=True, write_only=True, min_length=1)
    full_name = CharField(required=True, allow_blank=False)
    user_type = serializers.IntegerField(
        required=False,
        allow_null=True,
        default=UserTypes.CUSTOMER.value
    )

    class Meta:
        model = User
        fields = [
            'pk',
            'user_type',
            'full_name',
            'email',
            'password',
        ]
        read_only_fields = ['pk']

    def validate(self, attrs):
        try:
            User.objects.all().get_by_email(attrs['email'])
            raise ValidationError({'email': 'User already exist.'})
        except User.DoesNotExist:
            pass
        return super().validate(attrs)

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data.get('email'),
            password=validated_data.get('password'),
            user_type=validated_data.get('user_type'),
            full_name=validated_data.get('full_name')
        )
        return user


class UserCustomerSerializer(serializers.ModelSerializer):
    """
    This serializer is used only when customer edits his profile
    """

    email = CharField(required=True, allow_blank=False)
    full_name = CharField(required=True, allow_blank=False)


    class Meta:
        model = User
        fields = [
            'pk',
            'full_name',
            'user_type',
            'phone_number',
            'email',
            'avatar',
            'city',
            'language'
        ]
        read_only_fields = ['pk', 'user_type']


class UserHomeChefSerializer(serializers.ModelSerializer):
    """
    This is a serializer containing all fields - for homechef user

    Used for homechef request and editing Homechef profile
    """

    full_name = serializers.CharField(required=True)
    email = CharField(required=True)
    city = CharField(required=True)

    # homechef fields
    favorite_recipes = serializers.ListField(
        required=False,
        child=serializers.IntegerField(),  # ids of the Recipe, not FavoriteRecipe!
        write_only=True
    )
    experience = serializers.ListField(
        required=False,
        child=serializers.CharField(),
        write_only=True
    )
    cooking_philosophy = serializers.ListField(
        required=False,
        child=serializers.CharField(allow_blank=True),
        max_length=3
    )
    personal_cooking_mission = serializers.ListField(
        required=False,
        child=serializers.CharField(allow_blank=True),
        max_length=3
    )
    source_of_inspiration = serializers.ListField(
        required=False,
        child=serializers.CharField(allow_blank=True),
        max_length=3
    )

    role_models_to_delete = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'pk',
            'full_name',
            'user_type',
            'email',
            'phone_number',
            'username',
            'avatar',
            'city',
            'language',
            'bio',  # homechef-only fields below
            'experience',
            'cooking_philosophy',
            'personal_cooking_mission',
            'source_of_inspiration',
            'favorite_recipes',
            'experience',
            'role_models_to_delete'
        ]
        read_only_fields = ['pk', 'user_type']

    def validate(self, attrs):
        if not self.instance.avatar and 'avatar' not in attrs:
            raise ValidationError({'avatar': 'Avatar is required'})
        return super().validate(attrs)

    def update(self, instance, validated_data):
        """
        Make customer a HomeChef
        """
        instance.user_type = UserTypes.HOME_CHEF.value

        if 'role_models_to_delete' in validated_data:
            RoleModel.objects.filter(
                user=instance,
                pk__in=self.validated_data['role_models_to_delete']
            ).delete()

        # favorite recipes
        # 1. delete old if any
        FavoriteRecipe.objects.filter(user=instance).delete()

        frs = []
        for recipe_id in validated_data.get('favorite_recipes', []):
            try:
                recipe = Recipe.objects.get(pk=recipe_id)
            except Recipe.DoesNotExist:
                pass
            else:
                fr = FavoriteRecipe.objects.create(
                    recipe=recipe,
                    user=instance
                )
                frs.append(fr)
        if frs:
            validated_data['favorite_recipes'] = frs   # expects FavoriteRecipe

        # experience records
        # 1. delete old if any
        WorkExperienceRecord.objects.filter(user=instance).delete()

        wers = []
        for text in validated_data.get('experience', []):
            wer = WorkExperienceRecord.objects.create(
                user=instance,
                text=text
            )
            wers.append(wer)
        if wers:
            # expects WorkExperienceRecord
            validated_data['experience'] = wers

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        res = []
        for rm in instance.role_models.all():
            serializer = users.serializers.RoleModelSerializer(instance=rm)
            res.append(serializer.data)
        ret['role_models'] = res

        res = []
        for fr in instance.favorite_recipes.all():
            serializer = recipe.serializers.RecipeSerializer(
                instance=fr.recipe)
            res.append(serializer.data)
        ret['favorite_recipes'] = res

        res = []
        for wer in instance.work_experience_records.all():
            res.append(wer.text)
        ret['experience'] = res

        return ret


class UserSerializer(UserHomeChefSerializer):
    """
    This is basically a copy of HomeChef serializer - used to display
    User information in other serializers

    for customer all unnecessary fields will be empty
    """


class UserCardSerializer(UserCustomerSerializer):
    """
    Used in the cards, where only basic fields are necessary
    """


class UserStatSerializer(UserCustomerSerializer):
    """
    This serializer is used only in stats for users
    """

    total = serializers.IntegerField(read_only=True)
    accepted = serializers.IntegerField(read_only=True)
    rejected = serializers.IntegerField(read_only=True)
    awaiting_acceptance = serializers.IntegerField(read_only=True)
    published = serializers.IntegerField(read_only=True)
    in_recommendations = serializers.IntegerField(read_only=True)
    total_views = serializers.IntegerField(read_only=True)
    total_shares = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'pk',
            'full_name',
            'user_type',
            'phone_number',
            'email',
            'avatar',
            'city',
            'language',
            'total',
            'accepted',
            'rejected',
            'awaiting_acceptance',
            'published',
            'in_recommendations',
            'total_views',
            'total_shares'
        ]
        read_only_fields = ['pk', 'user_type']

    @staticmethod
    def retrieve_stats(users):

        arrays = [v for v in User.objects.all().values_list(
            'recommended_recipes', flat=True) if v]

        in_recommendations = []
        for array in arrays:
            in_recommendations += array

        users = users.annotate(
            total=Count('recipes'),
            accepted=Count(
                'recipes',
                filter=Q(recipes__status=Recipe.Status.ACCEPTED),
                distinct=True
            ),
            rejected=Count(
                'recipes',
                filter=Q(recipes__status=Recipe.Status.REJECTED),
                distinct=True
            ),
            awaiting_acceptance=Count(
                'recipes',
                filter=Q(recipes__status=Recipe.Status.AWAITING_ACCEPTANCE),
                distinct=True
            ),
            published=Count(
                'recipes',
                filter=Q(
                    recipes__publish_status=Recipe.PublishStatus.PUBLISHED),
                distinct=True
            ),
            in_recommendations=Count(
                'recipes',
                filter=Q(
                    recipes__pk__in=set(in_recommendations)),
                distinct=True
            ),
            total_views=Value(0),
            total_shares=Value(0),
            comments_count=Value(0),
            likes_count=Value(0),
            saved_recipes_count=Value(0)
        )

        pks = [u.pk for u in users]

        # Views & Shares

        rc = Recipe.objects.filter(user__in=users) \
            .values('user') \
            .annotate(
                recipes=ArrayAgg("pk")
        )  # {'user: 1, 'recipes': [3,4,5], 'user: 2, 'recipes': [6,7]}

        rr = Recipe.objects.filter(
            pk__in=list(chain(*[r['recipes'] for r in rc]))
        ) \
            .select_related('user') \
            .annotate(
            total_views=Sum('stat_records__views_counter__count'),
            total_shares=Sum('stat_records__shares_counter__count')
        ) \
        .values('pk', 'user', 'total_views', 'total_shares')

        stats_per_users = {u.pk: {'total_views': 0, 'total_shares': 0} for u in users}
        for r in rr:
            stats_per_users[r['user']]['total_views'] += r['total_views']
            stats_per_users[r['user']]['total_shares'] += r['total_shares']

        for res in users:
            res.total_views += stats_per_users[res.pk]['total_views']
            res.total_shares += stats_per_users[res.pk]['total_shares']

        # Comments by user
        comments_values = Comment.objects \
            .filter(user__in=pks, content_type__model='recipe') \
            .values('user') \
            .annotate(
                total=Count('pk')
            )
        comments_values_counter = {u['user']: u['total']
                                   for u in comments_values}
        for res in users:
            res.comments_count = comments_values_counter.get(res.pk, 0)

        # Votes (=likes)
        like_values = CommentLike.objects \
            .filter(user__in=pks) \
            .values('user') \
            .annotate(
                total=Count('pk')
            )
        like_values_counter = {u['user']: u['total'] for u in like_values}
        for res in users:
            res.likes_count = like_values_counter.get(res.pk, 0)

        # SavedRecipe
        saved_recipes_values = SavedRecipe.objects \
            .filter(user__in=pks) \
            .values('user') \
            .annotate(
                total=Count('pk')
            )
        saved_recipes_counter = {u['user']: u['total']
                                 for u in saved_recipes_values}
        for res in users:
            res.saved_recipes_count = saved_recipes_counter.get(res.pk, 0)

        # TODO: possible support - when and if exists

        return users


class RoleModelSerializer(serializers.ModelSerializer):

    file = serializers.FileField(
        allow_null=False,
        allow_empty_file=True,
        validators=[validate_images_file_max_size],
        required=True
    )

    class Meta:
        model = RoleModel
        fields = ['pk', 'name', 'file', 'user']
        read_only_fields = ['pk']


class ChangePasswordSerializer(serializers.Serializer):
    password = PasswordField()
    new_password = PasswordField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, attrs):
        super().validate(attrs)
        if not self.context['request'].user.check_password(attrs.get('password')):
            raise PasswordsDoNotMatch({
                'password': 'Wrong password'
            })
        return {'password': attrs.get('new_password')}

    def set_password(self):
        UserService.set_password(
            self.context['request'].user, self.validated_data.get('password'))


class RequestResetPasswordSerializer(serializers.Serializer):
    email = EmailField()
    user = None

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, attrs):
        try:
            email = attrs.get('email').lower()
            self.user = User.objects.all().get_by_email(attrs['email'])
        except User.DoesNotExist:
            raise EmailDoesNotExist()
        return {'email': email}

    def send_make_new_password(self):
        UserService().send_make_new_password(self.user)


class ConfirmEmailSerializer(serializers.Serializer):
    code = CodeField(write_only=True)
    access = CharField(read_only=True)
    refresh = CharField(read_only=True)
    user = None

    class Meta:
        fields = ['code', 'access', 'refresh']
        read_only_fields = ['access', 'refresh']

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, attrs):
        try:
            self.user = User.objects.all().get_by_activation_code(attrs.get('code'))
        except User.DoesNotExist:
            raise ValidationError({'code': 'Not found'})
        return super().validate(attrs)

    def confirm_email(self):
        UserService.confirm_email(self.user)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        refresh = TokenObtainPairSerializer.get_token(self.user)
        ret['refresh'] = str(refresh)
        ret['access'] = str(refresh.access_token)
        return ret


class RequestChangeEmailSerializer(serializers.ModelSerializer):
    new_email = EmailField(write_only=True)

    class Meta:
        model = User
        fields = ['new_email']

    def validate(self, attrs):
        new_email = User.objects.normalize_email(
            email=attrs.get('new_email').lower())
        old_email = User.objects.normalize_email(
            email=self.context['request'].user.email)

        if new_email == old_email:
            raise ValidationError(
                {'new_email': 'New mail should not be the same as old'})

        try:
            User.objects.get_by_email(new_email)
            raise MailAlreadyExists()
        except User.DoesNotExist:
            pass

        return super().validate(attrs)

    def send_confirm_new_email(self):
        UserService().send_new_email_activation_code(user=self.context['request'].user,
                                                     new_email=self.validated_data.get('new_email'))


class ConfirmNewEmailSerializer(serializers.Serializer):
    user = None

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, attrs):
        code = attrs.get('code')
        cache = NewMailCache()
        new_email = cache.get_new_email(activation_email_code=code)

        if new_email is None:
            raise ValidationError({'code': f'Code expired {code}'})

        try:
            self.user = User.objects.all().get_by_activation_email(code)
        except User.DoesNotExist:
            raise ValidationError({'code': 'Not found'})

        return {'new_email': new_email, 'code': code}

    def confirm_new_email(self):
        UserService.confirm_new_email(
            user=self.user, new_email=self.validated_data.get('new_email'))


class CheckResetCodeSerializer(serializers.Serializer):
    code = CodeField()

    class Meta:
        fields = ['code']

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, attrs):
        try:
            User.objects.get(
                reset_password_code=attrs.get('code'),
                reset_password_code_expire__gte=timezone.now()
            )
        except User.DoesNotExist:
            raise ResetCodeOrEmailInvalid()
        return {}


class ResetPasswordSerializer(CheckResetCodeSerializer):
    password = PasswordField()
    user: User

    class Meta:
        fields = ['email', 'code', 'password']

    def validate(self, attrs):
        super().validate(attrs)
        try:
            self.user = User.objects.all(
            ).get_by_reset_password_code(attrs['code'])
        except User.DoesNotExist:
            raise ResetCodeOrEmailInvalid()
        return attrs

    def reset_password(self):
        UserService.set_password(
            user=self.user, raw_new_password=self.validated_data.get('password'))


class ResendConfirmEmailSerializer(serializers.Serializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def send_confirm_email(self):
        user = self.context['request'].user
        if user.email is None or user.email == "":
            raise ValidationError({'email': 'Mail not specified'})
        UserService().send_email_activation_code(user)


class UserViewHistoryRecordSerializer(serializers.ModelSerializer):

    from recipe.serializers import RecipeCardSerializer

    user = UserCardSerializer(read_only=True)
    recipe = RecipeCardSerializer(read_only=True)

    class Meta:
        model = UserViewHistoryRecord
        fields = ['pk', 'user', 'recipe', 'created_at', 'updated_at']
        read_only_fields = ['pk', 'user', 'recipe', 'created_at', 'updated_at']
