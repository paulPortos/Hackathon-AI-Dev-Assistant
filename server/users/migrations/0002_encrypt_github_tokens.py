from django.db import migrations, models

import users.models.encrypted_token_field


def encrypt_existing_access_tokens(apps, schema_editor):
    user_model = apps.get_model('users', 'User')
    for user in user_model.objects.exclude(access_token=''):
        user.save(update_fields=['access_token'])


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='access_token',
            field=users.models.encrypted_token_field.EncryptedTokenField(blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='github_access_token_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='github_refresh_token',
            field=users.models.encrypted_token_field.EncryptedTokenField(blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='github_refresh_token_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(encrypt_existing_access_tokens, migrations.RunPython.noop),
    ]
