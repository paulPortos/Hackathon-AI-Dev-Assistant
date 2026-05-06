import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from scrum.models import Board, Column, Card

print("--- BOARDS ---")
for board in Board.objects.all():
    print(f"ID: {board.id}, Name: {board.name}")

print("\n--- COLUMNS ---")
for col in Column.objects.all():
    print(f"ID: {col.id}, Name: {col.name}, Board: {col.board.name}")

print("\n--- CARDS ---")
for card in Card.objects.all():
    print(f"ID: {card.id}, Title: {card.title}, Column: {card.column.name}, Board: {card.column.board.name}")
