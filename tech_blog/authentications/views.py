from django.urls import reverse_lazy
from .forms import (
    MyPasswordChangeForm, MyPasswordResetForm, MySetPasswordForm
)
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.template.loader import get_template
from django.contrib.auth.views import (
    LoginView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from .forms import LoginForm, UserCreateForm
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.urls import reverse
from django.http import Http404
from django.views.decorators.cache import never_cache
from django.shortcuts import render
from django.contrib.auth.views import LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from social_core.actions import do_auth, do_complete, do_disconnect
from social_core.backends.utils import get_backend
from social_core.exceptions import MissingBackend
from social_django.strategy import DjangoStrategy
from social_django.models import DjangoStorage
from social_django.views import _do_login as login_func
from django.views import generic
from django.core.mail import send_mail, EmailMessage


BACKENDS = settings.AUTHENTICATION_BACKENDS

User = get_user_model()


@never_cache
def auth(request, provider):
    redirect_uri = reverse("authentications:complete", args=(provider,))
    request.social_strategy = DjangoStrategy(DjangoStorage, request)
    try:
        backend_cls = get_backend(BACKENDS, provider)
        backend_obj = backend_cls(request.social_strategy, redirect_uri)
    except MissingBackend:
        raise Http404('Backend not found')

    return do_auth(backend_obj, redirect_name=REDIRECT_FIELD_NAME)


@never_cache
def complete(request, provider):
    redirect_uri = reverse("authentications:complete", args=(provider,))
    request.social_strategy = DjangoStrategy(DjangoStorage, request)
    try:
        backend_cls = get_backend(BACKENDS, provider)
        backend_obj = backend_cls(request.social_strategy, redirect_uri)
    except MissingBackend:
        raise Http404('Backend not found')
    return do_complete(backend_obj, login_func, request.user,
                       redirect_name=REDIRECT_FIELD_NAME, request=request)


@never_cache
def disconnect(request, provider, association_id=None):
    request.social_strategy = DjangoStrategy(DjangoStorage, request)
    try:
        backend_cls = get_backend(BACKENDS, provider)
        backend_obj = backend_cls(request.social_strategy, "")
    except MissingBackend:
        raise Http404('Backend not found')

    return do_disconnect(backend_obj, request.user, association_id,
                         redirect_name=REDIRECT_FIELD_NAME)


class Logout(LoginRequiredMixin, LogoutView):
    """LoginRequiredMixinでログイン確認"""
    template_name = 'authentications/demo.html'
    login_url = '/'


class Login(LoginView):
    """Login View"""
    form_class = LoginForm
    template_name = 'registration/login.html'


class SignUp(generic.CreateView):
    """Login View"""
    form_class = UserCreateForm
    template_name = 'registration/signup.html'


class Demo(View):
    """Base View"""

    @method_decorator(login_required)
    def get(self, request):
        return render(request, 'authentications/demo.html')

    @method_decorator(login_required)
    def post(self, request):
        return render(request, 'authentications/demo.html')


class UserCreate(generic.CreateView):
    """ユーザー仮登録"""
    template_name = 'registration/signup.html'
    form_class = UserCreateForm

    def form_valid(self, form):
        """仮登録と本登録用メールの発行."""
        # 仮登録と本登録の切り替えは、is_active属性
        # 退会処理も、is_activeをFalseにするだけ
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }
        subject_template = get_template('registration/mail_template/create/subject.txt')
        subject = subject_template.render(context)
        message_template = get_template('registration/mail_template/create/message.txt')
        message = message_template.render(context)

        from_email = 'test@verification-domain.com'
        recipient_list = ['hiroshi4000@gmail.com']
        email = EmailMessage(
            subject,
            message,
            from_email,
            recipient_list
        )
        email.send()
        # user.email_user(subject, message)  # local test用
        return redirect('/user_create/done/')


class UserCreateDone(generic.TemplateView):
    """ユーザー仮登録したよ"""
    template_name = 'registration/user_create_done.html'


class UserCreateComplete(generic.TemplateView):
    """メール内URLアクセス後のユーザー本登録"""
    template_name = 'registration/user_create_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # 問題なければ本登録とする
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()


class PasswordChange(PasswordChangeView):
    """パスワード変更ビュー"""
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('authentications:password_change_done')
    template_name = 'registration/password_change.html'


class PasswordChangeDone(PasswordChangeDoneView):
    """パスワード変更しました"""
    template_name = 'registration/password_change_done.html'


class PasswordReset(PasswordResetView):
    """パスワード変更用URLの送付ページ"""
    subject_template_name = 'registration/mail_template/password_reset/subject.txt'
    email_template_name = 'registration/mail_template/password_reset/message.txt'
    template_name = 'registration/password_reset_form.html'
    form_class = MyPasswordResetForm
    from_email = "test@verification-domain.com"
    success_url = reverse_lazy('authentications:password_reset_done')


class PasswordResetDone(PasswordResetDoneView):
    """パスワード変更用URLを送りましたページ"""
    template_name = 'registration/password_reset_done.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    """新パスワード入力ページ"""
    form_class = MySetPasswordForm

    success_url = reverse_lazy('authentications:password_reset_complete')
    template_name = 'registration/password_reset_confirm.html'


class PasswordResetComplete(PasswordResetCompleteView):
    """新パスワード設定しましたページ"""
    template_name = 'registration/password_reset_complete.html'