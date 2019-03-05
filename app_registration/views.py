from django.shortcuts import render
from app_person.models import Person
from app_person.forms import UserForm, SmsForm, UsersForm2
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .smsc_api import *  # точно нужно всё импортировать?
import uuid

from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect




def my_random_string(string_length=10):
    """Возвращает случайную строку"""  # а зачем случайная строка?
    random = str(uuid.uuid4())  # конвертирование UUID4 в строку.
    random = random.upper()
    random = random.replace("-", "")
    return random[0:string_length]


def registration(request):
    """
         Функция регистрации профиля персоны.
         Заменяет стандартную джанго-регистрацию.
         Вместо логина в админ-таблицу Пользователи Джанго прописывается номер телефона
          в формате без плюса, пробелов или тире - только цифры
         Вместо пароля прописывается "empty_password"
         Поля Фамилия, имя и мейл в админ-таблице оставляются пустыми
         Таблица Пользователь админки Персона связаны один-к-одному
         user_form -  работает из админки и содержит поле username пользователя
         sms_form -  Нужна для обработки кода смс
    """
    user_form = UserForm()
    sms_form = SmsForm()
    disabled, disabled2 = "", "disabled"  # Параметры кнопок,которые передаются в html

    if request.is_ajax():
        user_form = UserForm(request.POST)
        if user_form.is_valid():
            return JsonResponse({'s': True})
        else:
            return JsonResponse({'error': user_form.errors})

    if request.method == "POST" and 'code' in request.POST:

        user_form = UserForm(request.POST)

        if user_form.is_valid():
            #  Отправка сообщения и валидация номера в целях ?
            smsc = SMSC()
            phone = user_form.cleaned_data['username']

            mes = (my_random_string(4))
            print(mes)
            Sms_message = Person(id=1, sms_mes=mes)
            Sms_message.save()
            # counter = ['19', '1', '0.9', '194.4' ]
            # d = [ '-1' ]
            counter = smsc.send_sms(phones=phone, message=mes, sender="me") # Отправка смс с
            # введёными данными пользователя
            status_phone = smsc.get_status(phone=phone, id=counter[0])
            print(status_phone)

            if len(counter) < 3 and status_phone[0] != "-1":
                messages.error(request, "Такого номера нет в базе или Вы ошиблись при вводе номера")
            else:
                messages.success(request, "Код отправлен!")
                disabled = "disabled"
                disabled2 = ""

    if request.method == "POST" and 'reg' in request.POST:

        user_form = UserForm(request.POST)
        sms_form = SmsForm(request.POST)
        if user_form.is_valid() and sms_form.is_valid():
            get_id_first_person = Person.objects.get(id=1)
            print(get_id_first_person.sms_mes)
            print(sms_form.cleaned_data['sms_mes'],"\\/\/")
            # Проверка: совпадает ли код пользователя и код, отправленный ему
            if str(get_id_first_person.sms_mes) == sms_form.cleaned_data['sms_mes']:
                # создание или аутентификация персоны по введёным данным пользователя
                last_id = User.objects.latest('id').id
                last_i = Person.objects.latest('id').id
                password = "empty_password"
                User.objects.create_user (**user_form.cleaned_data, id=int(last_id)+1, password=password)
                create_person = Person(users_id = last_id+1, id = last_i+1)
                print(create_person)
                create_person.save()
                user = authenticate(
                    username=user_form.cleaned_data['username'],
                    password=password
                )
                login(request, user)
                messages.success(request, "Вы успешно зарегистрированы!")
                return redirect('edit_person', id=last_i+1)
            else:
                messages.error(request, "Код не подходит, Вы не ошиблись? Проверьте, пожалуйста")
                disabled2 = ""
    return render(request, 'sign_ip.html',
                   {"user_form": user_form,
                    "sms_form": sms_form,
                    "id": id,
                    "disabled": disabled,
                    "disabled2": disabled2})


def MyLoginView(request):
    """
         Функция авторизации
         user_form -  работает из админки и содержит поле username пользователя (номер телефона)
         sms_form -  Нужна для обработки кода смс
    """
    user_form = UsersForm2()
    sms_form = SmsForm()
    disabled, disabled2 = "","disabled"

    if request.is_ajax():
        user_form = UsersForm2(request.POST)
        if user_form.is_valid():
            if User.objects.filter(username=user_form.cleaned_data['username']).exists():
                return JsonResponse({'s': True})
            else:

                return JsonResponse({'error': {"username": "Этого номера еще нет, Вам нужно зарегистрироваться"}})
        else:
            return JsonResponse({'error': user_form.errors})

    if request.method == "POST" and 'code' in request.POST:

        user_form = UsersForm2(request.POST)
        if user_form.is_valid():
            # проверка существует ли пользователь с таким номером или нет
            if User.objects.filter(username=user_form.cleaned_data['username']).exists():
                # Отправка сообщения и валидация номера
                smsc = SMSC()
                phone = user_form.cleaned_data['username']
                mes = my_random_string(4)
                print(mes)
                # mes = "5"
                Sms_message = Person(id=1, sms_mes=mes)
                Sms_message.save()
                #counter = [ '19', '1', '0.9', '194.4' ]
                #d = [ '-1' ]
                counter = smsc.send_sms(phones=phone, message=mes, sender="me")
                phone_status = smsc.get_status(phone=phone, id=counter[0])

                if len(counter) < 3 and phone_status[ 0 ] != "-1":
                    messages.error(request, "Вы ввели неверный телефон!")

                else:
                    messages.success (request, "Код отправлен!")
                    disabled = "disabled"
                    disabled2 = ""
                    data = {'message': phone}
            else:
                messages.error (request, "Такого номера в базе не существует!")

    if request.method == "POST" and 'reg' in request.POST:

        user_form = UsersForm2(request.POST)
        sms_form = SmsForm (request.POST)
        if user_form.is_valid () and sms_form.is_valid ():
            password = "empty_password"
            # аутентификация пользователя
            user = authenticate(
                username=user_form.cleaned_data['username'],
                password=password
            )
            if user is not None:
                # Проверка валидности пользователя
                get_id_first_person = Person.objects.get(id=1)
                print(get_id_first_person.sms_mes)
                print(sms_form.cleaned_data['sms_mes'], "\\/\/")
                if str(get_id_first_person.sms_mes) == sms_form.cleaned_data['sms_mes']:
                    messages.success (request, "Вы успешно залогинили!")
                    login(request, user)
                    current_user = request.user.personshop.id
                    return redirect('app_person', id=current_user)
                else:
                    messages.error(request, "Вы ввели неверный код!")
                disabled2 = ""

    return render (request, 'login.html',
                   {"user_form": user_form,
                    "sms_form": sms_form,
                    "id": id,
                    "disabled": disabled,
                    "disabled2":disabled2})


def admin_add_person(request):
    """
          Функция отображения всех данных пользователей - список
    """

    return render (request, 'admin_add.html', {"user_form": Person.objects.all()})


