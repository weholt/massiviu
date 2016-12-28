from dse import dse_value_parser
from django.db import models
from datetime import datetime
import random


class AbstractMoo(models.Model):
    headline = models.CharField(max_length=50)

    class Meta:
        abstract = True


class foo(models.Model):
    name = models.CharField(max_length=200)
    age = models.IntegerField(default=20)
    sex = models.CharField(max_length=1, choices=(('F', 'F'), ('M', 'M')), default="M")


class bar(models.Model):
    text = models.TextField()
    active = models.BooleanField(default=True)
    foreign_foo = models.ForeignKey(foo)


class foobar(models.Model):
    number = models.IntegerField()
    dt = models.DateTimeField(default=datetime.now)


class ImplementedFoo(AbstractMoo):
    body = models.TextField()
    many_foos = models.ManyToManyField(foo)


class Parent(models.Model):
    name = models.CharField(max_length=50)


class Child(Parent):
    age = models.PositiveSmallIntegerField()


class ModelWithValidation(models.Model):
    name = models.CharField(max_length=50)

    @dse_value_parser
    def validation(cls, values):
        name = values.get('name')
        if not name:
            return None
        if len(name) > 50:
            values['name'] = values['name'][:50]
        return values


class ModelWithSQLKeywordAsField(models.Model):
    key = models.IntegerField()
    update = models.CharField(max_length=200)
    where = models.CharField(max_length=200)


class WiktionaryPage(models.Model):
    # Handle id by hand to match Wiktionary's IDs
    id = models.IntegerField(primary_key=True, db_index=True)
    title = models.CharField(max_length=255, blank=False, null=False, db_index=True)


class Photo(models.Model):
    filename = models.CharField(max_length=100)
    camera_model = models.CharField(max_length=50)
    rating = models.IntegerField(default=0)
