from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from api_applications.scan.models import Scan

User = get_user_model()

class Command(BaseCommand):
    help = "create admin groups and assign permisions"

    def handle(self, *args, **options):
        groups = {
            'super_admin': [],
            'scan_admin' : [
                'add_scan', 'view_scan', 'change_scan', 'delete_scan'
            ],
            'user_admin' : [
                'add_customuser', 'change_customuser', 'delete_customuser', 'view_customuser'
            ],
        }

        for group_name , perms in groups.items():
            group , created = Group.objects.get_or_create(name = group_name) 

            if group_name == 'super_admin':
               group.permissions.set(Permission.objects.all())
            else:
               for codename in perms:
                   if 'scan' in codename:
                       ct = ContentType.objects.get_for_model(Scan)
                   else:
                       ct = ContentType.objects.get_for_model(User)

                       perm = Permission.objects.get(content_type = ct, codename=codename)
                       group.permissions.add(perm)

            self.stdout.write(self.style.SUCCESS(f"{group_name} is ready."))
                       
                       
                   


