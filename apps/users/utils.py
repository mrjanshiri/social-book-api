from .models import Account


def would_remove_last_superuser(target_user, new_is_superuser_value):
    """
    Must be called inside an outer transaction.atomic() block.
    Locks superuser rows so two concurrent requests can't both
    think it's safe to remove the last superuser.
    """
    if not target_user.is_superuser or new_is_superuser_value:
        return False
    remaining = Account.objects.select_for_update().filter(is_superuser=True).count()
    return remaining <= 1