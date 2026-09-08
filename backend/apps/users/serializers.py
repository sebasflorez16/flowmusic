"""Serializers de autenticación y registro de usuarios.

Definen la validación y serialización de las credenciales del dueño. El login
devuelve el JWT (access/refresh) junto con el tenant asociado; el registro crea
el usuario, su tenant (con esquema propio) y el perfil de dueño.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import Domain, Tenant
from apps.users.models import UserProfile

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    """Serializa los datos del tenant (bar) que se envían al frontend."""

    class Meta:
        model = Tenant
        fields = (
            "id",
            "name",
            "slug",
            "owner_email",
            "phone",
            "address",
            "logo_url",
            "plan",
            "subscription_status",
            "max_tables",
            "requests_per_hour_limit",
            "crossfade_enabled",
            "autodj_enabled",
        )


class LoginSerializer(serializers.Serializer):
    """Valida email/contraseña y genera el par de tokens JWT."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        """Autentica al usuario y adjunta tokens + tenant al resultado.

        Raises:
            serializers.ValidationError: si las credenciales son inválidas o la
                cuenta está deshabilitada.
        """
        email = attrs["email"].lower().strip()
        password = attrs["password"]

        user = User.objects.filter(email__iexact=email).first()
        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Credenciales inválidas.")
        if not user.is_active:
            raise serializers.ValidationError("La cuenta está deshabilitada.")

        # El tenant se obtiene del perfil del usuario (esquema compartido).
        try:
            tenant = user.profile.tenant
        except ObjectDoesNotExist:
            tenant = None

        refresh = RefreshToken.for_user(user)
        attrs["access"] = str(refresh.access_token)
        attrs["refresh"] = str(refresh)
        attrs["tenant"] = tenant
        return attrs


class RegisterSerializer(serializers.Serializer):
    """Crea un usuario dueño junto con su tenant, dominio y perfil."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    business_name = serializers.CharField(max_length=120)
    slug = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        """Garantiza que el email no esté registrado previamente."""
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Ya existe un usuario con ese email.")
        return email

    def create(self, validated_data):
        """Crea usuario, tenant, dominio y perfil de forma atómica.

        El tenant se crea con estado ``trialing``; la activación real depende
        del pago en Wompi (fase posterior).
        """
        email = validated_data["email"]
        password = validated_data["password"]
        business_name = validated_data["business_name"]

        # Genera un slug único a partir del nombre del negocio.
        slug = validated_data.get("slug") or slugify(business_name)[:63]
        base_slug = slug
        counter = 1
        while Tenant.objects.filter(slug=slug).exists():
            suffix = f"-{counter}"
            slug = f"{base_slug[: 63 - len(suffix)]}{suffix}"
            counter += 1

        # 1. Usuario del sistema (esquema público).
        user = User.objects.create_user(username=email, email=email, password=password)

        # 2. Tenant (crea automáticamente su esquema de base de datos).
        tenant = Tenant.objects.create(
            schema_name=slug,
            name=business_name,
            slug=slug,
            owner_email=email,
            plan=Tenant.Plan.BASIC,
            subscription_status=Tenant.SubscriptionStatus.TRIALING,
        )

        # 3. Dominio/subdominio del tenant (placeholder en desarrollo).
        Domain.objects.create(domain=f"{slug}.musicflow.com", tenant=tenant, is_primary=True)

        # 4. Perfil que vincula al usuario con su tenant y rol de dueño.
        UserProfile.objects.create(user=user, tenant=tenant, role=UserProfile.Role.OWNER)

        return {"user": user, "tenant": tenant}
