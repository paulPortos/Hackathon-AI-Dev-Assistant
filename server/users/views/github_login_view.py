import secrets

from django.http import HttpResponseRedirect
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from users.github import build_github_authorization_url
from users.views.constants import GITHUB_OAUTH_STATE_SESSION_KEY


class GitHubLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        state = secrets.token_urlsafe(32)
        request.session[GITHUB_OAUTH_STATE_SESSION_KEY] = state
        request.session.save()
        request.session.modified = True
        return HttpResponseRedirect(build_github_authorization_url(state=state))
