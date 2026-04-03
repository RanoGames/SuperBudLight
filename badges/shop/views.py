from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import ShopItem, Purchase
from profile_app.models import UserProfile


def check_merch_access(user_profile):
    if not user_profile.is_student():
        return False
    top_100_ids = UserProfile.objects.filter(
        roles__name='student'
    ).order_by('-rating_points').values_list('id', flat=True)[:100]
    if user_profile.id in top_100_ids:
        return True
    if user_profile.artel:
        top_10_artel_ids = UserProfile.objects.filter(
            roles__name='student', artel=user_profile.artel
        ).order_by('-rating_points').values_list('id', flat=True)[:10]
        if user_profile.id in top_10_artel_ids:
            return True
    return False


@login_required
def shop_view(request):
    from django.shortcuts import render
    current_tab = request.GET.get('tab', 'cosmetic')
    items = ShopItem.objects.filter(is_available=True, item_type=current_tab)

    can_buy_merch = False
    if hasattr(request.user, 'profile'):
        can_buy_merch = check_merch_access(request.user.profile)

    my_purchases = Purchase.objects.filter(user=request.user).select_related('item')
    purchased_item_ids = my_purchases.values_list('item_id', flat=True)

    context = {
        'items': items,
        'current_tab': current_tab,
        'can_buy_merch': can_buy_merch,
        'my_purchases': my_purchases,
        'purchased_item_ids': purchased_item_ids,
        'user_balance': request.user.profile.balance if hasattr(request.user, 'profile') else 0,
    }
    return render(request, 'login/shop.html', context)


@login_required
@require_POST
def buy_item_view(request, item_id):
    profile = getattr(request.user, 'profile', None)
    if not profile or not profile.is_student():
        messages.error(request, "Только ученики могут совершать покупки.")
        return redirect('shop:shop')

    with transaction.atomic():
        item = get_object_or_404(ShopItem.objects.select_for_update(), id=item_id, is_available=True)
        profile = UserProfile.objects.select_for_update().get(user=request.user)

        if item.item_type == 'merch' and not check_merch_access(profile):
            messages.error(request, "Ошибка доступа! Мерч доступен только Топ-100 школы или Топ-10 артели.")
            return redirect(f"/shop/?tab={item.item_type}")

        if item.item_type == 'frame' and Purchase.objects.filter(user=request.user, item=item).exists():
            messages.warning(request, "У вас уже есть эта рамка!")
            return redirect(f"/shop/?tab={item.item_type}")

        if item.quantity <= 0:
            messages.error(request, "К сожалению, этот товар закончился.")
            return redirect(f"/shop/?tab={item.item_type}")

        if profile.balance >= item.price:
            profile.balance -= item.price
            profile.save(update_fields=['balance'])
            item.quantity -= 1
            item.save(update_fields=['quantity'])
            Purchase.objects.create(
                user=request.user, item=item, price_at_moment=item.price,
                status='completed' if item.item_type == 'frame' else 'pending'
            )
            messages.success(request, f"Вы купили «{item.name}»!")
        else:
            messages.error(request, "Недостаточно средств.")

    return redirect(f"/shop/?tab={item.item_type}")
