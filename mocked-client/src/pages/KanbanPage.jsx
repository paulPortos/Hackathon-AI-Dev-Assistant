import { useEffect, useState } from 'react';
import { api } from '../api';
import { normalizeList } from '../api/client';
import SectionCard from '../components/SectionCard';
import Modal from '../components/Modal';

export default function KanbanPage() {
  const [boards, setBoards] = useState([]);
  const [selectedBoard, setSelectedBoard] = useState(null);
  const [columns, setColumns] = useState([]);
  const [cardsByColumn, setCardsByColumn] = useState({});
  const [boardLabels, setBoardLabels] = useState([]);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');

  // Card Editing State
  const [editingCard, setEditingCard] = useState(null);
  const [editDraft, setEditDraft] = useState(null);
  const [editModalOpen, setEditModalOpen] = useState(false);

  const loadBoards = async () => {
    setStatus('loading');
    try {
      const payload = await api.listBoards();
      const boardList = normalizeList(payload);
      setBoards(boardList);
      if (boardList.length > 0) {
        setSelectedBoard(boardList[0]);
      } else {
        setStatus('ready');
      }
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  const loadBoardData = async (boardId) => {
    setStatus('loading');
    try {
      const [colPayload, labelPayload] = await Promise.all([
        api.listColumns(boardId),
        api.listBoardLabels(boardId)
      ]);
      
      const colList = normalizeList(colPayload);
      setColumns(colList);
      setBoardLabels(normalizeList(labelPayload));

      const cardsMap = {};
      await Promise.all(
        colList.map(async (col) => {
          const cardPayload = await api.listCards(col.id);
          cardsMap[col.id] = normalizeList(cardPayload);
        })
      );
      setCardsByColumn(cardsMap);
      setStatus('ready');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  const handleCreateBoard = async () => {
    const name = prompt('Enter board name:');
    if (!name) return;
    try {
      const newBoard = await api.createBoard({ name });
      setBoards(prev => [...prev, newBoard]);
      setSelectedBoard(newBoard);
    } catch (err) {
      alert('Failed to create board: ' + err.message);
    }
  };

  const handleCreateColumn = async () => {
    if (!selectedBoard) return;
    const name = prompt('Enter column name:');
    if (!name) return;
    try {
      const newCol = await api.createColumn(selectedBoard.id, { 
        name, 
        position: columns.length + 1 
      });
      setColumns(prev => [...prev, newCol]);
      setCardsByColumn(prev => ({ ...prev, [newCol.id]: [] }));
    } catch (err) {
      alert('Failed to create column: ' + err.message);
    }
  };

  const handleCreateCard = async (columnId) => {
    const title = prompt('Enter card title:');
    if (!title) return;
    try {
      const newCard = await api.createCard(columnId, { 
        title, 
        position: (cardsByColumn[columnId] || []).length + 1,
        priority: 'medium'
      });
      setCardsByColumn(prev => ({
        ...prev,
        [columnId]: [...(prev[columnId] || []), newCard]
      }));
    } catch (err) {
      alert('Failed to create card: ' + err.message);
    }
  };

  const openEditModal = (card) => {
    setEditingCard(card);
    setEditDraft({
      title: card.title,
      description: card.description || '',
      due_date: card.due_date ? card.due_date.substring(0, 16) : '',
      priority: card.priority,
      label_ids: card.labels?.map(l => l.id) || []
    });
    setEditModalOpen(true);
  };

  const handleUpdateCard = async () => {
    // Check if anything actually changed
    const originalLabels = editingCard.labels?.map(l => l.id) || [];
    const hasChanged = 
      editDraft.title !== editingCard.title ||
      editDraft.description !== (editingCard.description || '') ||
      editDraft.due_date !== (editingCard.due_date ? editingCard.due_date.substring(0, 16) : '') ||
      editDraft.priority !== editingCard.priority ||
      JSON.stringify([...editDraft.label_ids].sort()) !== JSON.stringify([...originalLabels].sort());

    if (!hasChanged) {
      setEditModalOpen(false);
      return;
    }

    try {
      const data = { ...editDraft };
      if (!data.due_date) data.due_date = null;
      
      const updatedCard = await api.updateCard(editingCard.id, data);
      setCardsByColumn(prev => {
        const colId = updatedCard.column;
        return {
          ...prev,
          [colId]: prev[colId].map(c => c.id === updatedCard.id ? updatedCard : c)
        };
      });
      setEditModalOpen(false);
    } catch (err) {
      alert('Failed to update card: ' + err.message);
    }
  };

  const handleAddLabel = async () => {
    const name = prompt('Enter label name:');
    if (!name) return;
    const color = prompt('Enter label color (hex):', '#c57b3f');
    if (!color) return;
    try {
      const newLabel = await api.createBoardLabel(selectedBoard.id, { name, color });
      setBoardLabels(prev => [...prev, newLabel]);
    } catch (err) {
      alert('Failed to create label: ' + err.message);
    }
  };

  const toggleLabel = (labelId) => {
    setEditDraft(prev => {
      const ids = prev.label_ids.includes(labelId)
        ? prev.label_ids.filter(id => id !== labelId)
        : [...prev.label_ids, labelId];
      return { ...prev, label_ids: ids };
    });
  };

  useEffect(() => {
    loadBoards();
  }, []);

  useEffect(() => {
    if (selectedBoard) {
      loadBoardData(selectedBoard.id);
    }
  }, [selectedBoard]);

  if (status === 'loading' && boards.length === 0) {
    return <div className="page">Loading Kanban...</div>;
  }

  return (
    <div className="page" style={{ maxWidth: '1400px' }}>
      <header style={{ marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontFamily: 'Fraunces', fontSize: '32px', margin: '0 0 8px' }}>Kanban Board</h1>
          <p className="subtle">Manage your project tasks and workflow stages.</p>
        </div>
        <div className="inline-actions">
          <select 
            className="select" 
            value={selectedBoard?.id || ''} 
            onChange={(e) => setSelectedBoard(boards.find(b => b.id === Number(e.target.value)))}
            style={{ minWidth: '200px' }}
          >
            {boards.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
            {boards.length === 0 && <option value="">No boards found</option>}
          </select>
          <button className="button" onClick={handleCreateBoard}>New Board</button>
        </div>
      </header>

      {error && <p className="pill" style={{ background: 'var(--accent-100)', color: 'var(--accent-700)', marginBottom: '20px' }}>{error}</p>}

      <div className="kanban-container" style={{ 
        display: 'flex', 
        gap: '24px', 
        overflowX: 'auto', 
        paddingBottom: '24px',
        minHeight: '70vh'
      }}>
        {columns.map(column => (
          <div key={column.id} className="kanban-column" style={{ 
            flex: '0 0 320px', 
            background: 'rgba(255, 255, 255, 0.4)', 
            borderRadius: '20px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            border: '1px solid rgba(135, 120, 89, 0.15)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', padding: '0 8px' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>{column.name}</h3>
              <span className="pill" style={{ fontSize: '11px', padding: '2px 8px' }}>
                {(cardsByColumn[column.id] || []).length}
              </span>
            </div>

            <div className="cards-list" style={{ display: 'grid', gap: '12px' }}>
              {(cardsByColumn[column.id] || []).map(card => (
                <div key={card.id} className="section-card" onClick={() => openEditModal(card)} style={{ 
                  padding: '14px', 
                  cursor: 'pointer',
                  transition: 'transform 0.2s ease',
                  boxShadow: '0 4px 12px rgba(44, 38, 23, 0.08)'
                }}>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '8px' }}>
                    {card.labels?.map(label => (
                      <span key={label.id} className="tag" style={{ 
                        background: label.color,
                        color: '#fff',
                        fontSize: '9px',
                        padding: '2px 6px'
                      }}>
                        {label.name}
                      </span>
                    ))}
                  </div>
                  <h4 style={{ margin: '0 0 6px', fontSize: '14px' }}>{card.title}</h4>
                  {card.description && (
                    <p className="subtle" style={{ fontSize: '12px', margin: '0 0 12px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                      {card.description}
                    </p>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className={`tag ${card.priority}`} style={{ 
                      fontSize: '10px', 
                      background: card.priority === 'high' ? 'rgba(215, 58, 74, 0.1)' : 'rgba(94, 106, 75, 0.1)' 
                    }}>
                      {card.priority}
                    </span>
                    {card.due_date && (
                      <span className="subtle" style={{ fontSize: '10px' }}>
                        {new Date(card.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
              ))}
              <button 
                className="button ghost" 
                style={{ width: '100%', padding: '8px', fontSize: '12px', borderStyle: 'dashed' }}
                onClick={(e) => { e.stopPropagation(); handleCreateCard(column.id); }}
              >
                + Add Card
              </button>
            </div>
          </div>
        ))}
        
        <button 
          className="button ghost" 
          onClick={handleCreateColumn}
          style={{ 
            flex: '0 0 320px', 
            height: '100px', 
            borderRadius: '20px', 
            borderStyle: 'dashed',
            background: 'rgba(255, 255, 255, 0.2)'
          }}
        >
          + Add Column
        </button>
      </div>

      <Modal
        isOpen={editModalOpen}
        title="Edit Card"
        onClose={() => setEditModalOpen(false)}
      >
        {editDraft && (
          <div className="grid">
            <div className="field">
              <label className="label">Title</label>
              <input 
                className="input" 
                value={editDraft.title} 
                onChange={e => setEditDraft(prev => ({ ...prev, title: e.target.value }))} 
              />
            </div>
            <div className="field">
              <label className="label">Description</label>
              <textarea 
                className="textarea" 
                value={editDraft.description} 
                onChange={e => setEditDraft(prev => ({ ...prev, description: e.target.value }))} 
              />
            </div>
            <div className="grid two">
              <div className="field">
                <label className="label">Due Date</label>
                <input 
                  className="input" 
                  type="datetime-local" 
                  value={editDraft.due_date} 
                  onChange={e => setEditDraft(prev => ({ ...prev, due_date: e.target.value }))} 
                />
              </div>
              <div className="field">
                <label className="label">Priority</label>
                <select 
                  className="select" 
                  value={editDraft.priority} 
                  onChange={e => setEditDraft(prev => ({ ...prev, priority: e.target.value }))}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>
            
            <div className="field">
              <label className="label">Labels</label>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
                {boardLabels.map(label => (
                  <button 
                    key={label.id}
                    onClick={() => toggleLabel(label.id)}
                    className="tag"
                    style={{ 
                      background: editDraft.label_ids.includes(label.id) ? label.color : 'rgba(0,0,0,0.05)',
                      color: editDraft.label_ids.includes(label.id) ? '#fff' : 'inherit',
                      cursor: 'pointer',
                      border: '1px solid rgba(0,0,0,0.1)',
                      borderRadius: '999px',
                      padding: '4px 12px'
                    }}
                  >
                    {label.name}
                  </button>
                ))}
                <button className="button ghost" style={{ padding: '2px 10px', fontSize: '11px' }} onClick={handleAddLabel}>
                  + New Label
                </button>
              </div>
            </div>

            <button className="button" onClick={handleUpdateCard} style={{ width: '100%', marginTop: '12px' }}>
              Save Changes
            </button>
          </div>
        )}
      </Modal>
    </div>
  );
}
