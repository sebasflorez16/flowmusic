"""Serializers de autenticación y registro de usuarios.

Definen la validación y serialización de las credenciales del dueño. El login
devuelve el JWT (access/refresh) junto con el tenant asociado; el registro crea
el usuario, su tenant (con esquema propio) y el perfil de dueño.
"""

import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import Domain, Tenant
from apps.users.models import UserProfile

User = get_user_model()


def issue_tokens_for_user(user):
    """Genera un nuevo par de tokens JWT y rota el ``session_id`` del usuario.

    Cada login emite una sesión nueva (un ``session_id`` aleatorio guardado en
    el perfil y embebido en ambos tokens). El token emitido antes deja de ser
    válido, así la cuenta no puede usarse en dos equipos a la vez.
    """
    session_id = secrets.token_hex(32)
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.session_id = session_id
    profile.save(update_fields=["session_id"])

    refresh = RefreshToken.for_user(user)
    refresh["sid"] = session_id
    access = refresh.access_token
    access["sid"] = session_id
    return str(access), str(refresh)


class TenantSerializer(serializers.ModelSerializer):
    """Serializa los datos del tenant (bar) que se envían al frontend."""

    monthly_total = serializers.SerializerMethodField()
    extra_tables = serializers.SerializerMethodField()

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
            "included_tables",
            "requests_per_hour_limit",
            "crossfade_enabled",
            "autodj_enabled",
            "genre",
            "monthly_total",
            "extra_tables",
        )

    def get_monthly_total(self, obj):
        """Precio mensual total (base + mesas extra)."""
        return str(obj.monthly_total)

    def get_extra_tables(self, obj):
        """Mesas adicionales por encima de las incluidas."""
        return obj.extra_tables


class TenantSettingsSerializer(serializers.ModelSerializer):
    """Serializa los campos editables de la configuración del bar.

    Solo permite editar datos del negocio y de reproducción. El plan, el número
    máximo de mesas y el estado de suscripción se gestionan desde el superadmin.
    """

    class Meta:
        model = Tenant
        fields = (
            "name",
            "phone",
            "address",
            "logo_url",
            "requests_per_hour_limit",
            "crossfade_enabled",
            "autodj_enabled",
            "genre",
        )

    def validate_requests_per_hour_limit(self, value):
        if value < 1:
            raise serializers.ValidationError("Debe ser al menos 1.")
        return value


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

        # El tenant y el rol se obtienen del perfil del usuario (esquema compartido).
        try:
            profile = user.profile
            tenant = profile.tenant
            role = profile.role
        except ObjectDoesNotExist:
            tenant = None
            role = None

        access, refresh = issue_tokens_for_user(user)
        attrs["access"] = access
        attrs["refresh"] = refresh
        attrs["tenant"] = tenant
        attrs["role"] = role
        attrs["email"] = user.email
        return attrs


class RegisterSerializer(serializers.Serializer):
    """Crea un usuario dueño junto con su tenant, dominio y perfil."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    business_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=30)
    slug = serializers.CharField(required=False, allow_blank=True)
    plan = serializers.ChoiceField(choices=Tenant.Plan.choices, required=False, default=Tenant.Plan.PRO)
    genre = serializers.ChoiceField(choices=Tenant.Genre.choices, required=False, default=Tenant.Genre.CROSSOVER)

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
            phone=validated_data.get("phone", ""),
            plan=validated_data.get("plan", Tenant.Plan.PRO),
            subscription_status=Tenant.SubscriptionStatus.TRIALING,
            genre=validated_data.get("genre", Tenant.Genre.CROSSOVER),
        )

        # 2b. Aplica las migraciones al esquema recién creado. django-tenants
        # solo crea el esquema vacío al guardar el tenant; sin este paso el bar
        # nuevo no tendría tablas y no podría operar.
        call_command("migrate_schemas", schema_name=tenant.schema_name, interactive=False, verbosity=0)

        # 3. Dominio/subdominio del tenant (placeholder en desarrollo).
        Domain.objects.create(domain=f"{slug}.musicflow.com", tenant=tenant, is_primary=True)

        # 4. Perfil que vincula al usuario con su tenant y rol de dueño.
        UserProfile.objects.create(user=user, tenant=tenant, role=UserProfile.Role.OWNER)

        return {"user": user, "tenant": tenant}
