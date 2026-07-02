from django.contrib.auth import get_user_model


User = get_user_model()


class UserService:
    @staticmethod
    def find_by_identifier(identifier):
        lookups = (
            [{"email__iexact": identifier}, {"username__iexact": identifier}]
            if "@" in identifier
            else [{"username__iexact": identifier}, {"email__iexact": identifier}]
        )
        for lookup in lookups:
            try:
                return User.objects.get(**lookup)
            except User.DoesNotExist:
                continue
        return None

    @staticmethod
    def generate_unique_username(email):
        base_username = email.split("@")[0][:140] or "google_user"
        username = base_username
        suffix = 1
        while User.objects.filter(username__iexact=username).exists():
            suffix_text = f"_{suffix}"
            username = f"{base_username[:150 - len(suffix_text)]}{suffix_text}"
            suffix += 1
        return username
