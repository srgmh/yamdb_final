from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg

from .validators import max_value_current_year


class User(AbstractUser):
    """Расширенная пользовательская модель."""
    CHOICES = (
        ('user', 'user'),
        ('moderator', 'moderator'),
        ('admin', 'admin'),
    )
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    role = models.CharField(max_length=150, choices=CHOICES, default='user')

    def __str__(self):
        return self.username


class Code(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    confirmation_code = models.CharField(max_length=150, null=True, blank=True)


class Category(models.Model):
    """Модель категорий произведений."""
    name = models.CharField(
        "Категория произведения",
        max_length=200,
        unique=True,
        help_text="Введите категорию произведения.",
    )
    slug = models.SlugField(
        "URL",
        unique=True,
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Genre(models.Model):
    """Модель жанров произведений."""
    name = models.CharField(
        "Название жанра",
        max_length=200,
        unique=True,
        help_text="Введите название жанра",
    )
    slug = models.SlugField(
        "URL",
        unique=True,
    )

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Title(models.Model):
    """Модель произведений."""
    name = models.CharField(
        "Название произведения",
        max_length=200,
        help_text="Введите название произведения",
    )
    year = models.PositiveSmallIntegerField(
        "Год выпуска",
        null=True,
        blank=True,
        help_text="Год выпуска",
        validators=[MinValueValidator(1700), max_value_current_year]
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Категория",
        related_name="title",
    )
    genre = models.ManyToManyField(
        Genre,
        verbose_name="Жанр",
        through='GenreTitle'
    )
    description = models.TextField(blank=True, verbose_name='description')

    class Meta:
        verbose_name = "Произведение"
        verbose_name_plural = "Произведения"
        ordering = ["name"]

    @property
    def rating(self):
        rating = self.reviews.aggregate(Avg('score'))['score__avg']
        if rating:
            return (
                round(rating)
                if isinstance(rating, int)
                else float(f'{rating:.2f}')
            )
        return None

    def __str__(self):
        return self.name


class GenreTitle(models.Model):
    """Модель Произведения и жанры."""
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name="Произведение"
    )
    genre = models.ForeignKey(
        Genre,
        on_delete=models.CASCADE,
        verbose_name="Жанр"
    )

    class Meta:
        verbose_name = "Произведение и жанр"
        verbose_name_plural = "Произведения и жанры"

    def __str__(self):
        return f"{self.title}, жанр - {self.genre}"


class Review(models.Model):
    """Модель для отзывов к произведениям."""
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        verbose_name="Произведение",
        related_name='reviews'
    )
    text = models.TextField(verbose_name="Текст отзыва")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name='reviews'
    )
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="Рейтинг произведений"
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'author'],
                name='unique_author_review'
            )
        ]
        ordering = ("-pub_date",)
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзыв"

    def __str__(self):
        return self.text


class Comment(models.Model):
    """Модель комментария."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        verbose_name="Отзыв",
        related_name='comments'
    )
    text = models.TextField(verbose_name="Комментарий")
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name='comments'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["pub_date"]

    def __str__(self):
        return self.text
