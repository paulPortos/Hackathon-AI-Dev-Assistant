from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from scrum.models import Board, Column, Card, Label, Comment, CardLabel

def broadcast_board_update(board_id):
    if not board_id:
        return
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"kanban_board_{board_id}",
        {
            "type": "kanban_message",
            "event": "board_updated",
            "board_id": board_id
        }
    )

@receiver([post_save, post_delete], sender=Board)
def board_changed(sender, instance, **kwargs):
    broadcast_board_update(instance.id)

@receiver([post_save, post_delete], sender=Column)
def column_changed(sender, instance, **kwargs):
    broadcast_board_update(instance.board_id)

@receiver([post_save, post_delete], sender=Card)
def card_changed(sender, instance, **kwargs):
    broadcast_board_update(instance.column.board_id)

@receiver([post_save, post_delete], sender=Label)
def label_changed(sender, instance, **kwargs):
    broadcast_board_update(instance.board_id)

@receiver([post_save, post_delete], sender=Comment)
def comment_changed(sender, instance, **kwargs):
    broadcast_board_update(instance.card.column.board_id)

@receiver([post_save, post_delete], sender=CardLabel)
def card_label_changed(sender, instance, **kwargs):
    broadcast_board_update(instance.card.column.board_id)
