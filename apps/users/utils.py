from django.db.models import Q

from .models import Account


def would_remove_last_superuser(target_user, new_is_superuser_value):
    """
    Must be called inside an outer transaction.atomic() block.

    Locks the target row and every superuser row with ONE query, ordered by
    pk. Two concurrent requests therefore lock rows in the same order (no
    deadlock) and cannot both conclude that it is safe to remove the last
    superuser.

    The ids are actually read (values_list) on purpose: a .count() query
    does not carry the row locks, so it can't be used for this.
    """
    rows = list(
        Account.objects.select_for_update()
        .filter(Q(is_superuser=True) | Q(pk=target_user.pk))
        .order_by('pk')
        .values_list('pk', 'is_superuser')
    )
    target_is_superuser = any(
        pk == target_user.pk and is_superuser for pk, is_superuser in rows
    )
    if not target_is_superuser or new_is_superuser_value:
        return False
    superuser_count = sum(1 for _, is_superuser in rows if is_superuser)
    return superuser_count <= 1