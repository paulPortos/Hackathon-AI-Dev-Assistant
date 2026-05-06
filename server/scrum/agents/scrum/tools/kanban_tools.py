from channels.db import database_sync_to_async
from scrum.models import Board, Column, Card, Label
from django.db.models import Prefetch
from django.db import transaction


@database_sync_to_async
def kanban_list_boards():
    """Returns list of all boards with id and name."""
    boards = Board.objects.all().values('id', 'name', 'description')
    return {
        'ok': True,
        'boards': list(boards)
    }

@database_sync_to_async
def kanban_get_board_detail(board_id: int):
    """Returns full board state: columns (ordered) with their cards (ordered)."""
    try:
        board = Board.objects.get(id=board_id)
        columns = Column.objects.filter(board=board).order_by('position').prefetch_related(
            Prefetch('cards', queryset=Card.objects.all().order_by('position').prefetch_related('labels'))
        )
        
        result = {
            'id': board.id,
            'name': board.name,
            'columns': []
        }
        
        for col in columns:
            col_data = {
                'id': col.id,
                'name': col.name,
                'position': col.position,
                'cards': []
            }
            for card in col.cards.all():
                col_data['cards'].append({
                    'id': card.id,
                    'title': card.title,
                    'description': card.description,
                    'priority': card.priority,
                    'due_date': card.start_datetime.isoformat() if card.start_datetime else None,
                    'labels': [{'id': l.id, 'name': l.name, 'color': l.color} for l in card.labels.all()],
                })
            result['columns'].append(col_data)
            
        return {'ok': True, 'board': result}
    except Board.DoesNotExist:
        return {'ok': False, 'error': f'Board with ID {board_id} not found.'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

@database_sync_to_async
def kanban_add_card(column_id: int, title: str, priority: str = "medium", description: str = "", due_date: str = None):
    """Creates a new card in the specified column."""
    try:
        column = Column.objects.get(id=column_id)
        # Get next position
        last_card = Card.objects.filter(column=column).order_by('-position').first()
        position = (last_card.position + 1) if last_card else 1
        
        card = Card.objects.create(
            column=column,
            title=title,
            priority=priority,
            description=description,
            position=position,
            start_datetime=due_date
        )
        return {
            'ok': True, 
            'card': {
                'id': card.id,
                'title': card.title,
                'column_id': column.id,
                'position': card.position
            }
        }
    except Column.DoesNotExist:
        return {'ok': False, 'error': f'Column with ID {column_id} not found.'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

@database_sync_to_async
def kanban_move_card(card_id: int, target_column_id: int):
    """Moves a card to a different column."""
    try:
        card = Card.objects.get(id=card_id)
        column = Column.objects.get(id=target_column_id)
        
        # Get next position in target column
        last_card = Card.objects.filter(column=column).order_by('-position').first()
        position = (last_card.position + 1) if last_card else 1
        
        card.column = column
        card.position = position
        card.save()
        
        return {'ok': True, 'card_id': card.id, 'new_column_id': column.id}
    except Card.DoesNotExist:
        return {'ok': False, 'error': f'Card with ID {card_id} not found.'}
    except Column.DoesNotExist:
        return {'ok': False, 'error': f'Column with ID {target_column_id} not found.'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

@database_sync_to_async
def kanban_update_card(card_id: int, title: str = None, description: str = None, priority: str = None, due_date: str = None):
    """Updates card fields."""
    try:
        card = Card.objects.get(id=card_id)
        if title is not None:
            card.title = title
        if description is not None:
            card.description = description
        if priority is not None:
            card.priority = priority
        if due_date is not None:
            card.start_datetime = due_date
        card.save()
        return {'ok': True, 'card_id': card.id}
    except Card.DoesNotExist:
        return {'ok': False, 'error': f'Card with ID {card_id} not found.'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

@database_sync_to_async
def kanban_delete_card(card_id: int):
    """Deletes a card."""
    try:
        card = Card.objects.get(id=card_id)
        card.delete()
        return {'ok': True, 'card_id': card_id}
    except Card.DoesNotExist:
        return {'ok': False, 'error': f'Card with ID {card_id} not found.'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
@database_sync_to_async
def kanban_bulk_move_cards(card_ids: list[int], target_column_id: int):
    """Moves multiple cards to a different column."""
    try:
        column = Column.objects.get(id=target_column_id)
        
        with transaction.atomic():
            results = []
            for card_id in card_ids:
                try:
                    card = Card.objects.get(id=card_id)
                    # Get next position in target column
                    last_card = Card.objects.filter(column=column).order_by('-position').first()
                    position = (last_card.position + 1) if last_card else 1
                    
                    card.column = column
                    card.position = position
                    card.save()
                    results.append({'id': card_id, 'ok': True})
                except Card.DoesNotExist:
                    results.append({'id': card_id, 'ok': False, 'error': 'Not found'})
            
        return {'ok': True, 'results': results, 'new_column_id': column.id}
    except Column.DoesNotExist:
        return {'ok': False, 'error': f'Column with ID {target_column_id} not found.'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

@database_sync_to_async
def kanban_bulk_update_cards(card_ids: list[int], priority: str = None, due_date: str = None):
    """Updates multiple cards at once (e.g., bulk set due date or priority)."""
    try:
        with transaction.atomic():
            results = []
            for card_id in card_ids:
                try:
                    card = Card.objects.get(id=card_id)
                    if priority is not None:
                        card.priority = priority
                    if due_date is not None:
                        card.start_datetime = due_date
                    card.save()
                    results.append({'id': card_id, 'ok': True})
                except Card.DoesNotExist:
                    results.append({'id': card_id, 'ok': False, 'error': 'Not found'})
            
        return {'ok': True, 'results': results}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
