from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Product, InventoryItem, Sale

class Command(BaseCommand):
    help = "Create default roles and assign permissions"

    def handle(self, *args, **kwargs):
        product_ct = ContentType.objects.get_for_model(Product)
        inventory_ct = ContentType.objects.get_for_model(InventoryItem)
        sale_ct = ContentType.objects.get_for_model(Sale)

        # Manager: all on Product & Inventory, view Sales
        manager, _ = Group.objects.get_or_create(name="Manager")
        manager_perms = list(Permission.objects.filter(content_type=product_ct)) + \
                        list(Permission.objects.filter(content_type=inventory_ct)) + \
                        list(Permission.objects.filter(content_type=sale_ct, codename__startswith="view_"))
        manager.permissions.set(manager_perms)

        # Cashier: add/change/view Sales
        cashier, _ = Group.objects.get_or_create(name="Cashier")
        cashier_perms = list(Permission.objects.filter(content_type=sale_ct).filter(
            codename__startswith=("add_", "change_", "view_")
        ))
        cashier.permissions.set(cashier_perms)

        self.stdout.write(self.style.SUCCESS("Roles seeded: Manager, Cashier"))
