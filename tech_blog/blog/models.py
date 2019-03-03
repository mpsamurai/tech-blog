from django.db import models
from people.models import Employee, Member
from django.utils import timezone


class ArticleTag(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return str(self.name)


class Article(models.Model):
    image = models.ImageField(upload_to='uploads/blog/article/image')
    thumbnail = models.ImageField(
        upload_to='uploads/blog/article/thumbnail', default='')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(default=timezone.now, blank=True)
    title = models.CharField(max_length=70, default='')
    article = models.TextField(default='')
    employee = models.ManyToManyField(Employee, blank=True)
    member = models.ManyToManyField(Member, blank=True)
    tags = models.ManyToManyField(ArticleTag, blank=True)
    is_topic = models.BooleanField(default=False)

    def __str__(self):
        return str(self.title)


class Top(models.Model):
    image = models.ImageField(
        upload_to='uploads/blog/top/image', null=True, blank=True)
    title = models.CharField(max_length=32)
    update_at = models.DateField(auto_now=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ('-update_at', )

    def __str__(self):
        return str(self.title)
