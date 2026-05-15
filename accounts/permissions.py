from .models import Profile


def is_support_or_admin(user):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role in {Profile.ROLE_SUPPORT, Profile.ROLE_ADMIN})


def is_admin_role(user):
    if not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == Profile.ROLE_ADMIN)
