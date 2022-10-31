import uuid

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from reviews.models import Category, Code, Comment, Genre, Review, Title, User

from api_yamdb.settings import DOMAIN_NAME

from .filters import TitleFilter
from .mixins import ListCreateDestroyViewSet
from .permissions import (
    IsAdmin, IsAdminOrReadOnly, NobodyAllow, IsAdminModeratorOwnerOrReadOnly
)
from .serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    ReviewSerializer,
    TitleReadSerializer,
    TitleWriteSerializer,
    TokenGeneratorSerialiser,
    UserForUserSerializer,
    UserSerializer
)

EMAIL_THEME = 'Подтверждающий код для API YAMDB'
EMAIL_FROM = f'from@{DOMAIN_NAME}'


class CodeTokenClass(viewsets.ModelViewSet):
    """Класс авторизации пользователей"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (NobodyAllow, )

    @action(
        detail=False, methods=['post'],
        url_path='signup', permission_classes=(AllowAny, )
    )
    def CodGenerator(self, request):
        """Функция генерациии кода по юзернейму и email."""
        confirmation_code = str(uuid.uuid4())
        username = request.data.get('username')
        email = request.data.get('email')
        serializer = self.get_serializer(data=request.data)
        if not User.objects.filter(username=username, email=email).exists():
            if serializer.is_valid(raise_exception=True):
                user = User.objects.create(username=username, email=email)
                Code.objects.create(
                    user=user,
                    confirmation_code=confirmation_code
                )
                send_mail(
                    EMAIL_THEME,
                    confirmation_code,
                    EMAIL_FROM,
                    [email],
                    fail_silently=False,
                )
                return Response(request.data, status=status.HTTP_200_OK)
        user = get_object_or_404(User, username=username, email=email)
        Code.objects.update(
            user=user,
            confirmation_code=confirmation_code
        )
        send_mail(
            EMAIL_THEME,
            confirmation_code,
            EMAIL_FROM,
            [email],
            fail_silently=False,
        )
        return Response(request.data, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=['post'],
        url_path='token', permission_classes=(AllowAny, )
    )
    def TokenGenerator(self, request):
        """Функция генерациии токена по юзернейму и коду."""
        serializer = TokenGeneratorSerialiser(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = request.data['username']
        user_valid = get_object_or_404(User, username=username)
        if Code.DoesNotExist:
            return Response(
                {'message': 'Проверь confirmation_code'},
                status=status.HTTP_400_BAD_REQUEST
            )
        refresh = RefreshToken.for_user(user_valid)
        return Response({
            'token': str(refresh.access_token),
        })


class UserViewSet(viewsets.ModelViewSet):
    """Класс представления пользователей."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    permission_classes = (IsAdmin,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    def get_object(self):
        return get_object_or_404(
            self.queryset, username=self.kwargs["username"])

    @action(
        detail=False, methods=['get', 'patch'],
        url_path='me', permission_classes=(IsAuthenticated, )
    )
    def user_rool_users_detail(self, request, username=None):
        user = get_object_or_404(User, username=self.request.user)
        if request.method == 'PATCH':
            serializer = UserForUserSerializer(
                user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                user.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
        serializer = UserForUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CategoryViewSet(ListCreateDestroyViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"

    def perform_create(self, serializer):
        serializer.save(
            name=self.request.data["name"], slug=self.request.data["slug"]
        )

    def perform_destroy(self, serializer):
        serializer = get_object_or_404(Category, slug=self.kwargs.get("slug"))
        serializer.delete()


class GenreViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ("name",)
    lookup_field = "slug"

    def perform_create(self, serializer):
        serializer.save(
            name=self.request.data["name"], slug=self.request.data["slug"]
        )

    def perform_destroy(self, serializer):
        serializer = get_object_or_404(Genre, slug=self.kwargs.get("slug"))
        serializer.delete()


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleWriteSerializer
    permission_classes = (
        IsAdminOrReadOnly,
        permissions.IsAuthenticatedOrReadOnly,
    )
    filter_backends = [DjangoFilterBackend]
    filterset_class = TitleFilter

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PATCH']:
            return TitleWriteSerializer
        return TitleReadSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """API для работы с моделью отзывов."""
    queryset = Review.objects.all()

    serializer_class = ReviewSerializer
    permission_classes = (IsAdminModeratorOwnerOrReadOnly,)

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        new_queryset = title.reviews.all()
        return new_queryset

    def perform_create(self, serializer):
        title = get_object_or_404(
            Title,
            id=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)


class CommentViewSet(viewsets.ModelViewSet):
    """API для работы с моделью комментариев."""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = (IsAdminModeratorOwnerOrReadOnly,)

    def get_queryset(self):
        review = get_object_or_404(Review, pk=self.kwargs.get('review_id'))
        new_queryset_comments = review.comments.all()
        return new_queryset_comments

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id, title=title_id)
        serializer.save(author=self.request.user, review=review)
