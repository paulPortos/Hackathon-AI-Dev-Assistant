import { useState, useEffect } from 'react';
import { api } from '../api';

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [editingEvent, setEditingEvent] = useState(null);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    color: '#3b82f6',
    all_day: true,
    recurrence_rule: '',
  });

  useEffect(() => {
    fetchEvents();
  }, [currentDate]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const year = currentDate.getFullYear();
      const month = currentDate.getMonth();
      const start = new Date(year, month, 1).toISOString();
      const end = new Date(year, month + 1, 0, 23, 59, 59).toISOString();
      
      const data = await api.getCalendar({ start, end });
      setEvents(data);
    } catch (error) {
      console.error('Failed to fetch calendar events:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEvent = async (e) => {
    e.preventDefault();
    try {
      if (editingEvent) {
        await api.updateEvent(editingEvent.id, newEvent);
      } else {
        const payload = {
          ...newEvent,
          start_datetime: new Date(selectedDate.setHours(9, 0, 0)).toISOString(),
          is_standalone: true,
        };
        await api.createEvent(payload);
      }
      closeModal();
      fetchEvents();
    } catch (error) {
      alert('Failed to save event');
    }
  };

  const handleDeleteEvent = async () => {
    if (!editingEvent || !window.confirm('Delete this event?')) return;
    try {
      await api.deleteEvent(editingEvent.id);
      closeModal();
      fetchEvents();
    } catch (error) {
      alert('Failed to delete event');
    }
  };

  const openAddModal = (date) => {
    setSelectedDate(date);
    setEditingEvent(null);
    setNewEvent({ title: '', description: '', color: '#3b82f6', all_day: true, recurrence_rule: '' });
    setShowModal(true);
  };

  const openEditModal = (e, event) => {
    e.stopPropagation();
    if (event.source === 'card') return; // Cards are managed in Kanban board
    setEditingEvent(event);
    setNewEvent({
      title: event.title,
      description: event.description || '',
      color: event.color || '#3b82f6',
      all_day: event.all_day,
      recurrence_rule: event.recurrence_rule || '',
    });
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingEvent(null);
  };

  const nextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  const prevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));

  const daysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
  const firstDayOfMonth = (year, month) => new Date(year, month, 1).getDay();

  const renderDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const totalDays = daysInMonth(year, month);
    const startOffset = firstDayOfMonth(year, month);
    
    const days = [];
    
    for (let i = 0; i < startOffset; i++) {
      days.push(<div key={`empty-${i}`} className="calendar-day empty"></div>);
    }
    
    for (let day = 1; day <= totalDays; day++) {
      const date = new Date(year, month, day);
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const dayEvents = events.filter(e => e.start.startsWith(dateStr));
      const isToday = new Date().toDateString() === date.toDateString();
      
      days.push(
        <div 
          key={day} 
          className={`calendar-day ${isToday ? 'today' : ''}`}
          onClick={() => openAddModal(date)}
        >
          <span className="day-number">{day}</span>
          <div className="day-events">
            {dayEvents.map((event, idx) => (
              <div 
                key={idx} 
                className={`event-tag ${event.source}`}
                style={{ backgroundColor: event.color || (event.source === 'card' ? '#3b82f6' : '#8b5cf6') }}
                onClick={(e) => openEditModal(e, event)}
                title={event.title}
              >
                <span style={{ marginRight: '4px', opacity: 0.8 }}>
                  {event.source === 'card' ? '📋' : '📅'}
                </span>
                {event.title}
              </div>
            ))}
          </div>
        </div>
      );
    }
    
    return days;
  };

  return (
    <div className="calendar-container glass">
      <div className="calendar-header">
        <h2 className="month-title">
          {currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })}
        </h2>
        <div className="calendar-controls">
          <button onClick={prevMonth} className="button ghost">Previous</button>
          <button onClick={() => setCurrentDate(new Date())} className="button secondary">Today</button>
          <button onClick={nextMonth} className="button ghost">Next</button>
        </div>
      </div>
      
      <div className="calendar-grid">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="weekday">{day}</div>
        ))}
        {renderDays()}
      </div>

      {loading && <div className="loading-overlay">Updating Calendar...</div>}

      {showModal && (
        <div className="modal-content glass" style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 1000,
          background: '#f5f2e9',
          color: '#1a1a1a',
          boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
          border: '1px solid rgba(0,0,0,0.05)'
        }}>
          <h3 style={{ marginBottom: '24px', fontWeight: 800 }}>
            {editingEvent ? 'Edit Event' : `Add Event for ${selectedDate?.toLocaleDateString()}`}
          </h3>
          <form onSubmit={handleSaveEvent}>
            <div className="form-group">
              <label style={{ color: '#1a1a1a' }}>Title</label>
              <input 
                autoFocus
                required
                value={newEvent.title}
                onChange={e => setNewEvent({...newEvent, title: e.target.value})}
                placeholder="What's happening?"
                style={{ background: '#fff', border: '1px solid #ddd', color: '#1a1a1a' }}
              />
            </div>
            <div className="form-group">
              <label style={{ color: '#1a1a1a' }}>Description</label>
              <textarea 
                value={newEvent.description}
                onChange={e => setNewEvent({...newEvent, description: e.target.value})}
                placeholder="Add details..."
                style={{ background: '#fff', border: '1px solid #ddd', color: '#1a1a1a' }}
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label style={{ color: '#1a1a1a' }}>Color</label>
                <input 
                  type="color"
                  value={newEvent.color}
                  onChange={e => setNewEvent({...newEvent, color: e.target.value})}
                  style={{ height: '40px', padding: '2px', background: '#fff', border: '1px solid #ddd' }}
                />
              </div>
              <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingTop: '24px' }}>
                <input 
                  type="checkbox"
                  checked={newEvent.all_day}
                  onChange={e => setNewEvent({...newEvent, all_day: e.target.checked})}
                  id="all_day"
                />
                <label htmlFor="all_day" style={{ margin: 0, color: '#1a1a1a' }}>All Day</label>
              </div>
            </div>
            <div className="modal-actions">
              {editingEvent && (
                <button type="button" onClick={handleDeleteEvent} className="button ghost" style={{ color: '#f44336', marginRight: 'auto' }}>Delete</button>
              )}
              <button type="button" onClick={closeModal} className="button ghost" style={{ color: '#666' }}>Cancel</button>
              <button type="submit" className="button primary">
                {editingEvent ? 'Update Event' : 'Create Event'}
              </button>
            </div>
          </form>
        </div>
      )}

      {showModal && <div className="modal-close-trigger" onClick={closeModal} />}

      <style dangerouslySetInnerHTML={{ __html: `
        .calendar-container {
          padding: 24px;
          border-radius: 20px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          min-height: 600px;
          position: relative;
        }
        .calendar-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 32px;
        }
        .month-title {
          font-size: 24px;
          font-weight: 700;
          margin: 0;
        }
        .calendar-grid {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 1px;
          background: rgba(255, 255, 255, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          overflow: hidden;
        }
        .weekday {
          padding: 12px;
          text-align: center;
          font-weight: 700;
          font-size: 13px;
          text-transform: uppercase;
          background: rgba(255, 255, 255, 0.15);
          color: #1a1a1a;
        }
        .calendar-day {
          min-height: 120px;
          padding: 8px;
          background: rgba(255, 255, 255, 0.03);
          transition: background 0.2s;
          cursor: pointer;
        }
        .calendar-day:hover {
          background: rgba(255, 255, 255, 0.06);
        }
        .calendar-day.today {
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.5);
          position: relative;
        }
        .calendar-day.today .day-number {
          color: #3b82f6;
          font-weight: 800;
        }
        .calendar-day.empty {
          background: transparent;
          cursor: default;
        }
        .day-number {
          font-size: 14px;
          font-weight: 600;
          margin-bottom: 8px;
          display: block;
          opacity: 0.8;
        }
        .day-events {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .event-tag {
          font-size: 11px;
          padding: 4px 8px;
          border-radius: 6px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          color: white;
          font-weight: 500;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          transition: transform 0.1s;
        }
        .event-tag:hover {
          transform: translateY(-1px);
          filter: brightness(1.1);
        }
        .event-tag.card {
          border-radius: 4px;
          border-left: 4px solid rgba(0,0,0,0.2);
          font-weight: 600;
          cursor: default;
        }
        .event-tag.event {
          border-radius: 20px;
          border-left: none;
          font-style: italic;
          padding: 4px 12px;
          cursor: pointer;
          background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
          border: 1px solid rgba(255,255,255,0.2);
          box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }
        .event-tag.event:hover {
          box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        
        .modal-close-trigger {
          position: fixed;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(0,0,0,0.1);
          z-index: 999;
        }
        .modal-content {
          width: 100%;
          max-width: 450px;
          padding: 32px;
          border-radius: 24px;
        }
        .form-group {
          margin-bottom: 20px;
        }
        .form-group label {
          display: block;
          font-size: 13px;
          font-weight: 600;
          margin-bottom: 8px;
          opacity: 0.8;
        }
        .form-group input, .form-group textarea {
          width: 100%;
          padding: 12px;
          border-radius: 12px;
          border: 1px solid rgba(255,255,255,0.1);
          background: rgba(255,255,255,0.05);
          color: white;
          font-size: 14px;
        }
        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }
        .modal-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
          margin-top: 32px;
        }
        
        .loading-overlay {
          position: absolute;
          top: 0; left: 0; right: 0; bottom: 0;
          background: rgba(0,0,0,0.1);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          z-index: 10;
          border-radius: 20px;
          backdrop-filter: blur(2px);
        }
      `}} />
    </div>
  );
}
