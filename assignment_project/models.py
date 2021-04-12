import datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True, related_name='profile', on_delete=models.CASCADE)
    id = models.CharField(max_length=7, primary_key=True)
    is_stu = models.BooleanField(default=True)
    branches = [('puc', 'PUC'), ('cse', 'CSE'), ('mech', 'MECH'), ('chem', 'CHEM'), ('ece', 'ECE'), ('mme', 'MME'), ('civil', 'CIVIL')]
    branch = models.CharField(max_length=5, choices=branches, default='cse')
    years = [('p1', 'P1'), ('p2', 'P2'), ('e1', 'E1'), ('e2', 'E2'), ('e3', 'E3'), ('e4', 'E4')]
    year = models.CharField(max_length=2, choices=years, default='e1')


class Choice(models.Model):
    choice = models.CharField(max_length=60)

    def __unicode__(self):
        return self.choice


class Assignment(models.Model):
    branch = models.CharField(max_length=5, default='clg')
    year = models.CharField(max_length=2, default='e1')
    name = models.CharField(max_length=40)
    Teacher = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, related_name='teacher', blank=True, null=True)
    pub_date = models.DateTimeField(default=timezone.now)
    time = models.DurationField(default=datetime.timedelta(minutes=15))


class Question(models.Model):
    question = models.CharField(max_length=200)
    assignment = models.ForeignKey(Assignment, on_delete=models.SET_NULL, related_name='assignment', blank=True, null=True)
    answer = models.ForeignKey(Choice, on_delete=models.SET_NULL, related_name='answer', blank=True, null=True)
    img = models.ImageField(upload_to='images/', default='images/night_owl.png', blank=True, null=True)
    choices = models.ManyToManyField(Choice)


class GradedAssignment(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='gassignment', blank=True, null=True)
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='student', blank=True, null=True)
    sub_date = models.DateTimeField(default=timezone.now)
    answers = models.CharField(max_length=100, default='')
    grades = models.FloatField()


class Completed(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='cassignment', blank=True, null=True)
    student = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='cstudent', blank=True, null=True)
    completed = models.BooleanField(default=False)