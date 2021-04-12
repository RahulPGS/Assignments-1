from datetime import datetime
from django.contrib.auth.models import User
from django import forms as f
from django.shortcuts import render, redirect
from . import forms
from . import models


# Create your views here.
def main(response):
    if isinstance(response.user, User):
        if response.user.is_superuser:
            return redirect('logout')
        return redirect('/assignments')
    return redirect('login')


def register(response):
    if response.method == 'GET':
        return render(response, 'stu_register.html', {'form': forms.student()})

    if response.method == 'POST':
        form = forms.student(response.POST)

        if form.is_valid():
            cd = form.cleaned_data
            email = f'{cd["id"]}@rguktsklm.ac.in'
            user = User.objects.get_or_create(username=cd["username"], email=email)[0]
            user.set_password(cd["password1"])
            user.save()
            up = models.UserProfile(user=user)
            up.id = cd['id'].capitalize()
            up.branch = cd['branch']
            up.year = cd['year']
            up.save()

            return redirect('/')

        return render(response, 'stu_register.html', {'form': form})


def assignment(response):
    if not isinstance(response.user, User):
        if response.user.is_superuser:
            return redirect('logout')
        return redirect('login')

    if not response.user.profile.is_stu:
        return redirect("/teacher")

    assignments = models.Assignment.objects.filter(branch=response.user.profile.branch.lower(),
                                                   year=response.user.profile.year).order_by('-pub_date')
    asgmnts = [a for a in assignments
               if (not models.Completed.objects.get_or_create(assignment=a, student=response.user.profile)[0].completed)
               and a.pub_date.replace(tzinfo=None) + a.time >= datetime.now() >= a.pub_date.replace(tzinfo=None)]
    tasgmnts = [a for a in assignments if a.pub_date.replace(tzinfo=None) >= datetime.now()]

    return render(response, 'assignments.html', {'as': asgmnts, 'stu': response.user.profile.id, 'tas': tasgmnts})


def qstn(response, aid):
    asgmnt = models.Assignment.objects.get(id=aid)
    qstns = models.Question.objects.select_related().filter(assignment=asgmnt)

    if response.method == 'GET':
        stu = models.User.objects.filter(pk=response.user.pk).first()

        if models.Completed(asgmnt, stu).completed:
            return render(response, 'completed.html', {'stu': stu.profile.id})

        if asgmnt.pub_date.replace(tzinfo=None) + asgmnt.time <= datetime.now() or asgmnt.pub_date.replace(
                tzinfo=None) >= datetime.now() or response.user.profile.year != asgmnt.year:
            return redirect('/assignments')

        qn = 0
        cforms = []
        choices = []

        for q in qstns:
            ch = q.choices.all()
            chc = [(i + 1, c.choice) for i, c in zip(list(range(len(ch))), ch)]
            qn = qn + 1
            form = forms.choice(prefix=f'cform{qn}')
            form.fields['choice'] = f.CharField(label=choices, widget=f.RadioSelect(choices=chc))
            cforms.append(form)

        lenl = list(range(qn))
        img = []
        for i in qstns:
            try:
                img.append(i.img.url)
            except ValueError:
                img.append(None)
        qstns = [q.question for q in qstns]
        response.session['qn'] = qn

        return render(response, 'qstn.html',
                      {'qstns': qstns, 'len': lenl, 'img': img, 'time': asgmnt.pub_date + asgmnt.time,
                       'form': cforms, 'stu': stu.profile.id, 'an': asgmnt.name.title()})

    if response.method == 'POST':
        qn = response.session['qn']
        marks = 0
        ans = []

        for i in range(qn):
            cform = forms.choice(response.POST, prefix=f'cform{i + 1}')

            if cform.is_valid():
                choices = qstns[i].choices.all()
                choices = [c.choice for c in choices]
                selected = cform.cleaned_data['choice']
                selected = int(selected)
                selected = choices[(selected - 1)]
                ans.append(selected)

                if selected == qstns[i].answer.choice:
                    marks = marks + 1

        gac = models.GradedAssignment.objects.filter(assignment=asgmnt,
                                                     student=response.user.profile).first() is None

        if not gac:
            return render(response, 'already_submitted.html', {'stu': response.user.profile.id,
                                                               'heading': 'The response to this assignment is already '
                                                                          'submitted', 'error': '409 conflict'})

        if asgmnt.pub_date.replace(tzinfo=None) + asgmnt.time <= datetime.now():
            return render(response, 'already_submitted.html',
                          {'stu': response.user.profile.id, 'heading': 'This assignment has '
                                                                       'stopped taking '
                                                                       'responses', 'error': '406 Not Acceptable'})
        ga = models.GradedAssignment()
        ga.assignment = models.Assignment.objects.get(id=aid)
        ga.student = response.user.profile
        if qn == 0:
            ga.grades = 100.00

        else:
            ga.grades = (marks / qn) * 100
        ga.answers = ','.join(ans)
        ga.save()

        ca = models.Completed.objects.get(assignment=ga.assignment, student=ga.student)
        ca.completed = True
        ca.save()

        return render(response, 'submitted.html', {'stu': response.user.profile.id})


def stu_login(response):
    if isinstance(response.user, User):
        return redirect("/assignments")
    return redirect('/login')


def teacher(response):
    if not isinstance(response.user, User):
        return redirect('login')
    branch = response.user.profile.branch.lower()
    asgmnts = models.Assignment.objects.filter(branch=response.user.profile.branch.lower()).order_by('-pub_date')
    return render(response, 'tassignments.html', {'as': asgmnts, 'stu': response.user.username, 'self': 'my',
                                                  'branch': f'All assignments of branch {branch.upper()}'
                                                , 'selfl': 'my_assignments'})


def qstn_view(response, aid):
    if response.user.profile.is_stu:
        return redirect('/assignments')
    asgmnt = models.Assignment.objects.get(id=aid)
    qstns = models.Question.objects.select_related().filter(assignment=asgmnt)
    response.session['aspk'] = aid

    if response.method == 'GET':
        stu = models.User.objects.filter(pk=response.user.pk).first()

        qn = 0
        choices = []

        for q in qstns:
            ch = q.choices.all()
            choices.append(ch)
            qn = qn + 1

        lenl = list(range(qn))
        img = []
        for i in qstns:
            try:
                img.append(i.img.url)
            except ValueError:
                img.append(None)
        ans = [a.answer.choice for a in qstns]
        qst = [q.question for q in qstns]
        qpk = [q.pk for q in qstns]
        if (not response.user.username == asgmnt.Teacher.user.username) or asgmnt.pub_date.replace(
                tzinfo=None) <= datetime.now():
            print('=' * 40, datetime.now())
            print(asgmnt.pub_date)
            heading = f"This is {models.Assignment.objects.get(pk=aid).Teacher.user.username}'s assignment, You cannot edit or delete this"
            if asgmnt.pub_date >= datetime.now(asgmnt.pub_date.tzinfo):
                heading = 'Test is already taken by students cannot edit or delete now'
            return render(response, 'qstnvr.html', {'qstns': qpk, 'choices': choices, 'qst': qst, 'img': img,
                                                    'len': lenl, 'stu': stu.username, 'ans': ans, 'heading': heading,
                                                    'an': asgmnt.name.title(), 'duration': asgmnt.time})

        return render(response, 'qstnv.html', {'qstns': qpk, 'choices': choices, 'qst': qst, 'img': img,
                                               'len': lenl, 'stu': stu.username, 'ans': ans, 'aspk': aid,
                                               'an': asgmnt.name.title(), 'duration': asgmnt.time})


def new_as(response):
    if not isinstance(response.user, User):
        return redirect('login')

    if response.user.profile.is_stu:
        return redirect('/assignments')

    na = models.Assignment()

    if response.method == 'GET':
        form = forms.new_as()
        return render(response, 'new_as.html', {'form': form, 'stu': response.user.username})

    if response.method == 'POST':
        form = forms.new_as(response.POST, response.FILES)

        if form.is_valid():
            t = response.user.profile
            na.branch = t.branch
            na.Teacher = t
            na.name = form.cleaned_data['as_name']
            na.pub_date = form.cleaned_data['pub_date']
            na.time = form.cleaned_data['duration']
            na.year = response.user.profile.year
            na.save()
            response.session['aspk'] = na.pk

            if 'True' in response.POST:
                return redirect(f'/add_qstn')

            else:
                return redirect('/assignments')

        else:
            return render(response, 'new_as.html', {'form': form, 'stu': response.user.username})


def add_qstn(response):
    if not isinstance(response.user, User):
        return redirect('login')

    if response.user.profile.is_stu:
        return redirect('/assignments')

    else:
        aid = response.session['aspk']
        na = models.Assignment.objects.get(pk=aid)
        if not response.user.username == na.Teacher.user.username:
            redirect(f'/qstnv/{aid}')

        if response.method == 'GET':
            form = forms.new_qn()
            response.session['apkaq'] = aid
            return render(response, 'add_qstn.html',
                          {'form': form, 'as': na, 'stu': response.user.username, 'an': na.name})

        if response.method == 'POST':
            form = forms.new_qn(response.POST, response.FILES)

            if form.is_valid():
                q = models.Question()
                q.assignment = na
                q.img = form.cleaned_data['img']
                choices = form.cleaned_data['choices'].split(',')
                chpk = []

                for i, c in enumerate(choices):
                    ch = models.Choice()
                    ch.choice = c
                    ch.save()
                    if (i + 1) == int(form.cleaned_data['answer']):
                        q.answer = ch
                    chpk.append(ch.pk)

                q.question = form.cleaned_data['question']
                q.save()
                q.choices.add(*chpk)

                if 'True' in response.POST:
                    return redirect(f'/add_qstn')

                else:
                    return redirect(f'/qstnv/{aid}')
            else:
                return render(response, 'add_qstn.html',
                              {'form': form, 'as': na, 'stu': response.user.username, 'an': na.name})


def delo(response, xoy, aorq):
    response.session['pk'] = xoy
    if response.user.profile.is_stu:
        return redirect('/assignments')
    if aorq == 1:
        a = models.Assignment.objects.get(pk=xoy)
        name = a.name
        target = 'del_as'
        obj = 'assignment'
        cancel = f'/qstnv/{xoy}/qstnv'

        if not response.user.username == a.Teacher.user.username:
            return redirect(f'/qstnv/{xoy}')

    else:
        q = models.Question.objects.get(pk=xoy)
        name = q.question
        target = 'del_qstn'
        obj = 'question'
        apk = q.assignment.pk
        cancel = f'/qstnv/{apk}/qstnv'

        if not response.user.username == models.Assignment.objects.get(pk=q.assignment.pk).Teacher.user.username:
            return redirect(f'/qstnv/{xoy}')

    return render(response, 'delo.html',
                  {'name': name.title(), 'obj': obj, 'target': target, 'id': xoy, 'cancel': cancel
                      , 'stu': response.user.username})


def del_as(response):
    if response.user.profile.is_stu:
        return redirect('/assignments')
    pk = response.session['pk']
    a = models.Assignment.objects.get(pk=pk)
    if not response.user.username == a.Teacher.user.username:
        redirect(f'/qstnv/{pk}')
    a.delete()
    return redirect('/assignments')


def del_qstn(response):
    if response.user.profile.is_stu:
        return redirect('/assignments')
    pk = response.session['pk']
    q = models.Question.objects.get(pk=pk)
    a = q.assignment
    if not response.user.username == a.Teacher.user.username:
        redirect(f'/qstnv/{a.pk}')
    q.delete()
    return redirect(f'/qstnv/{a.pk}/qstnv')


def edit_q(response, pk):
    if not isinstance(response.user, User):
        return redirect('login')
    if response.user.profile.is_stu:
        return redirect('/assignments')
    qstn = models.Question.objects.get(pk=pk)
    apk = qstn.assignment
    if response.method == 'GET':

        if not response.user.username == apk.Teacher.user.username:
            return redirect(f'/qstnv/{apk.pk}')

        form = forms.new_qn()
        form.fields['question'] = f.CharField(label='question', max_length=200,
                                              widget=f.Textarea(attrs={'rows': 4, 'cols': 50,
                                                                       'placeholder': qstn.question}))
        form.fields['choices'] = f.CharField(
            label='choices(Enter all choices as comma separated string eg:option1,option2,option3...)',
            max_length=500, widget=f.Textarea(attrs={'rows': 2, 'cols': 30,
                                                     'placeholder': ','.join([c.choice for c in qstn.choices.all()])}))
        form.fields['answer'] = f.CharField(
            label='answer(Enter the index of one of the choices above eg:if ans is option3, enter 3')
        return render(response, 'edit_q.html', {'form': form, 'qpk': pk, 'stu': response.user.username, 'an': apk.name
            , 'oq': qstn.question})

    if response.method == 'POST':
        form = forms.new_qn(response.POST, response.FILES)
        if form.is_valid():
            qstn.question = form.cleaned_data['question']
            choices = form.cleaned_data['choices'].split(',')
            chpk = []

            for i, c in enumerate(choices):
                ch = models.Choice()
                ch.choice = c
                ch.save()
                if (i + 1) == int(form.cleaned_data['answer']):
                    qstn.answer = ch
                chpk.append(ch.pk)
            qstn.img = form.cleaned_data['img']
            qstn.choices.clear()
            qstn.save()
            qstn.choices.add(*chpk)

            return redirect(f'/qstnv/{apk.pk}/qstnv')

        else:
            return render(response, 'edit_q.html', {'form': form, 'qpk': pk, 'stu': response.user.username,
                                                    'an': apk.name, 'oq': qstn.question})


def results(response):
    if isinstance(response.user, User):
        if response.user.is_superuser:
            return redirect('logout')

    ga = models.GradedAssignment.objects.select_related().filter(student=response.user.profile).order_by('-sub_date')
    return render(response, 'results.html', {'ga': ga, 'stu': response.user.profile.id})


def mas(response):
    if isinstance(response.user, User):
        if response.user.is_superuser:
            return redirect('logout')

    if response.user.profile.is_stu:
        return redirect('/assignments')
    asgmnts = models.Assignment.objects.select_related().filter(Teacher=response.user.profile).order_by('-pub_date')
    return render(response, 'tassignments.html', {'as': asgmnts, 'stu': response.user.username, 'self': 'all',
                                                  'branch': f'Assignments posted by {response.user.username}({response.user.profile.branch})'
        , 'selfl': '/teacher'})


def vresults(response):
    if isinstance(response.user, User):
        if response.user.is_superuser:
            return redirect('logout')

    if response.user.profile.is_stu:
        return redirect('/assignments')

    asgmnt = models.Assignment.objects.get(pk=response.session['aspk'])
    ga = models.GradedAssignment.objects.select_related().filter(assignment=asgmnt).order_by('grades')
    return render(response, 'vresults.html', {'ga': ga, 'stu': response.user.username, 'an': asgmnt.name})


def viewr(response, spk):
    if isinstance(response.user, User):
        if response.user.is_superuser:
            return redirect('logout')

    if response.user.profile.is_stu:
        asgmnt = models.Assignment.objects.get(pk=int(spk))
        student = response.user.profile
        stu = response.user.profile.id
        heading = f'Your response for assignmnet: {asgmnt.name}'
        self = 'your'
        color = 'white'
        c = '#0062cc'

    else:
        asgmnt = models.Assignment.objects.get(pk=response.session['aspk'])
        student = models.UserProfile.objects.get(pk=spk)
        stu = response.user.username
        heading = f'Response of {student.id} for assignment: {asgmnt.name}'
        self = "student's"
        color = '#0062cc'
        c = 'white'

    qstns = models.Question.objects.select_related().filter(assignment=asgmnt)
    ga = models.GradedAssignment.objects.get(student=student, assignment=asgmnt)
    ans = []
    rans = ga.answers.split(',')
    oans = [a.answer.choice for a in qstns]
    for i, a in enumerate(oans):

        if rans[i] == a:
            ans.append(True)

        else:
            ans.append(False)

    qst = [q.question for q in qstns]
    choices = []
    for q in qstns:
        ch = q.choices.all()
        choices.append(ch)
    img = []
    for i in qstns:
        try:
            img.append(i.img.url)
        except ValueError:
            img.append(None)

    return render(response, 'viewr.html',
                  {'stu': stu, 'qst': qst, 'ans': ans, 'choices': choices, 'oans': oans, 'self': self,
                   'heading': heading, 'rans': rans, 'len': list(range(len(rans))), 'img': img,
                   'color': color, 'c': c})


def edit_as(response):
    if isinstance(response.user, User):
        if response.user.is_superuser:
            return redirect('logout')

    if response.user.profile.is_stu:
        return redirect('/assignment')

    asgmnt = models.Assignment.objects.get(pk=response.session['aspk'])

    if response.method == 'GET':
        form = forms.new_as()
        form.fields['as_name'] = f.CharField(max_length=200, label='Name of the assignment',
                                             widget=f.TextInput(attrs={'placeholder':
                                                                           asgmnt.name}))
        return render(response, 'edit_as.html', {'form': form, 'name': asgmnt.name, 'stu': response.user.username})

    if response.method == 'POST':
        form = forms.new_as(response.POST)
        if form.is_valid():
            asgmnt.name = form.cleaned_data['as_name']
            asgmnt.pub_date = form.cleaned_data['pub_date']
            asgmnt.time = form.cleaned_data['duration']
            asgmnt.save()
            return redirect(f'/qstn/{response.session["aspk"]}/qstn')
        return render(response, 'edit_as.html', {'form': form, 'name': asgmnt.name, 'stu': response.user.username})
