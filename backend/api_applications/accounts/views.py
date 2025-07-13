from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from api_applications.shared_models.models import UserProfile, CustomUser
from .serializers import CustomTokenObtainPairSerializer, UserProfileSerializer


class TokenCookieSetter:
    """
    Sets JWT tokens in HttpOnly cookies in the response.
    """

    @staticmethod
    def set_token_cookies(response, validated_data, set_refresh=True):
        response.set_cookie(
            key="access",
            value=validated_data["access"],
            httponly=True,
            secure=True,
        )
        if set_refresh and "refresh" in validated_data:
            response.set_cookie(
                key="refresh",
                value=validated_data["refresh"],
                httponly=True,
                secure=True,
            )
        return response


class BaseTokenCookieView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    set_refresh = True  # Default, can be overridden in subclasses

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        response = Response(data=None, status=status.HTTP_200_OK)
        return TokenCookieSetter.set_token_cookies(
            response, serializer.validated_data, set_refresh=self.set_refresh
        )


class CustomTokenObtainPairView(BaseTokenCookieView):
    set_refresh = True


class CustomRefreshTokenObtainPairView(BaseTokenCookieView):
    set_refresh = False


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.select_related("user")
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Return the profile of the authenticated user
        return self.get_queryset().first()
