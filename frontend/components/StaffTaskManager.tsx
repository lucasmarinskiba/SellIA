/**
 * StaffTaskManager — Real-time task assignment + mobile-friendly task queue
 */

import React, { useEffect, useState } from 'react';

interface StaffTask {
  task_id: string;
  title: string;
  task_type: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'assigned' | 'acknowledged' | 'in_progress' | 'completed' | 'cancelled' | 'overdue';
  due_date: string;
  description?: string;
  estimated_duration_minutes: number;
  assigned_at: string;
  started_at?: string;
  completed_at?: string;
}

interface ShiftReport {
  report_id: string;
  staff_id: string;
  shift_start: string;
  shift_end: string;
  total_tasks: number;
  completed: number;
  completion_rate: number;
  on_time: number;
  overdue: number;
}

type TaskView = 'queue' | 'active' | 'completed';

export const StaffTaskManager: React.FC<{ staffId: string; locationId: string }> = ({
  staffId,
  locationId,
}) => {
  const [tasks, setTasks] = useState<StaffTask[]>([]);
  const [view, setView] = useState<TaskView>('queue');
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<StaffTask | null>(null);
  const [shiftReport, setShiftReport] = useState<ShiftReport | null>(null);

  useEffect(() => {
    loadTasks();
  }, [staffId, view]);

  const loadTasks = async () => {
    try {
      let status = null;
      if (view === 'active') status = 'in_progress';
      if (view === 'completed') status = 'completed';

      let url = `/api/v1/staff/${staffId}/tasks`;
      if (status) url += `?status=${status}`;

      const res = await fetch(url);
      const data = await res.json();
      setTasks(data.tasks || []);
    } catch (e) {
      console.error('Failed to load tasks:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (taskId: string) => {
    try {
      const res = await fetch(`/api/v1/tasks/${taskId}/acknowledge`, {
        method: 'POST',
      });

      if (res.ok) {
        loadTasks();
      }
    } catch (e) {
      console.error('Failed to acknowledge task:', e);
    }
  };

  const handleStart = async (taskId: string) => {
    try {
      const res = await fetch(`/api/v1/tasks/${taskId}/start`, {
        method: 'POST',
      });

      if (res.ok) {
        loadTasks();
      }
    } catch (e) {
      console.error('Failed to start task:', e);
    }
  };

  const handleComplete = async (taskId: string, notes: string = '') => {
    try {
      const res = await fetch(`/api/v1/tasks/${taskId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_id: taskId,
          completion_notes: notes,
        }),
      });

      if (res.ok) {
        loadTasks();
        setSelectedTask(null);
      }
    } catch (e) {
      console.error('Failed to complete task:', e);
    }
  };

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'urgent':
        return '#dc2626';
      case 'high':
        return '#f97316';
      case 'medium':
        return '#f59e0b';
      case 'low':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'in_progress':
        return '⏱';
      case 'acknowledged':
        return '👁';
      case 'assigned':
        return '📌';
      case 'overdue':
        return '⚠';
      case 'cancelled':
        return '✕';
      default:
        return '•';
    }
  };

  const getTaskList = (): StaffTask[] => {
    if (view === 'queue') {
      return tasks.filter((t) => ['assigned', 'acknowledged'].includes(t.status));
    }
    if (view === 'active') {
      return tasks.filter((t) => t.status === 'in_progress');
    }
    return tasks.filter((t) => t.status === 'completed');
  };

  const taskList = getTaskList();
  const timeUntilDue = (dueDate: string): string => {
    const due = new Date(dueDate);
    const now = new Date();
    const minutes = Math.round((due.getTime() - now.getTime()) / 60000);

    if (minutes < 0) return 'Overdue';
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `${hours}h`;
    const days = Math.round(hours / 24);
    return `${days}d`;
  };

  if (loading) {
    return <div>Loading tasks...</div>;
  }

  return (
    <div className="task-manager">
      <header className="task-header">
        <h1>Task Manager</h1>
        <div className="task-stats">
          <div className="stat">
            <span className="stat-label">Queue</span>
            <span className="stat-value">{tasks.filter((t) => ['assigned', 'acknowledged'].includes(t.status)).length}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Active</span>
            <span className="stat-value active">{tasks.filter((t) => t.status === 'in_progress').length}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Done</span>
            <span className="stat-value done">{tasks.filter((t) => t.status === 'completed').length}</span>
          </div>
        </div>
      </header>

      <nav className="task-tabs">
        <button className={view === 'queue' ? 'active' : ''} onClick={() => setView('queue')}>
          📋 Queue
        </button>
        <button className={view === 'active' ? 'active' : ''} onClick={() => setView('active')}>
          ⏱ Active
        </button>
        <button className={view === 'completed' ? 'active' : ''} onClick={() => setView('completed')}>
          ✓ Completed
        </button>
      </nav>

      <section className="task-list">
        {taskList.length === 0 ? (
          <div className="empty-state">
            {view === 'queue' && 'No tasks in queue'}
            {view === 'active' && 'No active tasks'}
            {view === 'completed' && 'No completed tasks'}
          </div>
        ) : (
          taskList.map((task) => (
            <div
              key={task.task_id}
              className={`task-card priority-${task.priority} status-${task.status}`}
              onClick={() => setSelectedTask(task)}
            >
              <div className="task-header-row">
                <div className="task-title-block">
                  <span className="task-icon">{getStatusIcon(task.status)}</span>
                  <div>
                    <h3>{task.title}</h3>
                    <span className="task-type">{task.task_type.replace(/_/g, ' ')}</span>
                  </div>
                </div>
                <div className="task-priority-badge" style={{ backgroundColor: getPriorityColor(task.priority) }}>
                  {task.priority}
                </div>
              </div>

              {task.description && <p className="task-description">{task.description}</p>}

              <div className="task-meta">
                <div className="meta-item">
                  <span className="meta-label">Estimated:</span>
                  <span className="meta-value">{task.estimated_duration_minutes}m</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Due in:</span>
                  <span className={`meta-value ${task.status === 'overdue' ? 'overdue' : ''}`}>
                    {timeUntilDue(task.due_date)}
                  </span>
                </div>
              </div>

              {(view === 'queue' || view === 'active') && (
                <div className="task-actions">
                  {task.status === 'assigned' && (
                    <button className="btn-primary btn-sm" onClick={() => handleAcknowledge(task.task_id)}>
                      Acknowledge
                    </button>
                  )}
                  {task.status === 'acknowledged' && (
                    <button className="btn-primary btn-sm" onClick={() => handleStart(task.task_id)}>
                      Start Task
                    </button>
                  )}
                  {task.status === 'in_progress' && (
                    <button className="btn-success btn-sm" onClick={() => handleComplete(task.task_id)}>
                      Mark Done
                    </button>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </section>

      {selectedTask && (
        <div className="task-detail-modal" onClick={() => setSelectedTask(null)}>
          <div className="task-detail-card" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setSelectedTask(null)}>✕</button>

            <h2>{selectedTask.title}</h2>
            <div className="detail-badge" style={{ backgroundColor: getPriorityColor(selectedTask.priority) }}>
              {selectedTask.priority.toUpperCase()} • {selectedTask.task_type}
            </div>

            {selectedTask.description && (
              <div className="detail-section">
                <h4>Description</h4>
                <p>{selectedTask.description}</p>
              </div>
            )}

            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Status</span>
                <span className="detail-value">{selectedTask.status}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Due</span>
                <span className="detail-value">{new Date(selectedTask.due_date).toLocaleString()}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Duration</span>
                <span className="detail-value">{selectedTask.estimated_duration_minutes} minutes</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Assigned</span>
                <span className="detail-value">{new Date(selectedTask.assigned_at).toLocaleDateString()}</span>
              </div>
            </div>

            {selectedTask.status === 'in_progress' && (
              <div className="detail-section">
                <textarea placeholder="Notes (optional)" className="task-notes"></textarea>
                <button className="btn-success" onClick={() => handleComplete(selectedTask.task_id)}>
                  Complete Task
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        .task-manager {
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .task-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
          border-bottom: 2px solid #f0f0f0;
          padding-bottom: 15px;
        }

        .task-header h1 {
          margin: 0;
          font-size: 24px;
        }

        .task-stats {
          display: flex;
          gap: 20px;
        }

        .stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .stat-label {
          font-size: 11px;
          color: #6b7280;
          margin-bottom: 4px;
          text-transform: uppercase;
          font-weight: 600;
        }

        .stat-value {
          font-size: 20px;
          font-weight: 700;
          color: #1f2937;
        }

        .stat-value.active {
          color: #3b82f6;
        }

        .stat-value.done {
          color: #10b981;
        }

        .task-tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 20px;
        }

        .task-tabs button {
          padding: 10px 16px;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          background: white;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          color: #6b7280;
          transition: all 0.2s;
        }

        .task-tabs button.active {
          background: #2563eb;
          color: white;
          border-color: #2563eb;
        }

        .task-list {
          display: grid;
          gap: 12px;
        }

        .task-card {
          padding: 16px;
          border: 2px solid #e5e7eb;
          border-left: 4px solid;
          border-radius: 8px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
        }

        .task-card:hover {
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .task-card.priority-urgent {
          border-left-color: #dc2626;
        }

        .task-card.priority-high {
          border-left-color: #f97316;
        }

        .task-card.priority-medium {
          border-left-color: #f59e0b;
        }

        .task-card.priority-low {
          border-left-color: #10b981;
        }

        .task-card.status-overdue {
          background: #fffbf0;
          border-color: #fecaca;
        }

        .task-header-row {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
          gap: 12px;
        }

        .task-title-block {
          display: flex;
          gap: 12px;
          flex: 1;
        }

        .task-icon {
          font-size: 20px;
          min-width: 24px;
        }

        .task-title-block h3 {
          margin: 0 0 4px 0;
          font-size: 16px;
          color: #1f2937;
        }

        .task-type {
          font-size: 12px;
          color: #6b7280;
          text-transform: capitalize;
        }

        .task-priority-badge {
          padding: 4px 10px;
          border-radius: 4px;
          font-size: 11px;
          font-weight: 600;
          color: white;
          text-transform: uppercase;
          white-space: nowrap;
        }

        .task-description {
          margin: 0 0 12px 0;
          font-size: 13px;
          color: #4b5563;
        }

        .task-meta {
          display: flex;
          gap: 20px;
          margin-bottom: 12px;
          font-size: 13px;
        }

        .meta-item {
          display: flex;
          gap: 6px;
        }

        .meta-label {
          color: #6b7280;
          font-weight: 500;
        }

        .meta-value {
          color: #1f2937;
          font-weight: 600;
        }

        .meta-value.overdue {
          color: #dc2626;
        }

        .task-actions {
          display: flex;
          gap: 8px;
        }

        .btn-sm {
          padding: 8px 12px;
          border: none;
          border-radius: 4px;
          background: #f3f4f6;
          cursor: pointer;
          font-size: 12px;
          font-weight: 600;
          transition: all 0.2s;
        }

        .btn-primary {
          background: #3b82f6;
          color: white;
        }

        .btn-primary:hover {
          background: #2563eb;
        }

        .btn-success {
          background: #10b981;
          color: white;
          padding: 8px 12px;
        }

        .btn-success:hover {
          background: #059669;
        }

        .empty-state {
          padding: 40px 20px;
          text-align: center;
          color: #9ca3af;
          font-size: 14px;
        }

        .task-detail-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .task-detail-card {
          background: white;
          border-radius: 12px;
          padding: 24px;
          max-width: 500px;
          max-height: 80vh;
          overflow-y: auto;
          position: relative;
        }

        .close-btn {
          position: absolute;
          top: 16px;
          right: 16px;
          background: none;
          border: none;
          font-size: 20px;
          cursor: pointer;
          color: #6b7280;
        }

        .task-detail-card h2 {
          margin: 0 0 12px 0;
          font-size: 20px;
        }

        .detail-badge {
          display: inline-block;
          padding: 6px 12px;
          border-radius: 4px;
          color: white;
          font-size: 12px;
          font-weight: 600;
          margin-bottom: 20px;
        }

        .detail-section {
          margin-bottom: 20px;
        }

        .detail-section h4 {
          margin: 0 0 8px 0;
          font-size: 13px;
          color: #6b7280;
          text-transform: uppercase;
          font-weight: 600;
        }

        .detail-section p {
          margin: 0;
          color: #1f2937;
          line-height: 1.5;
        }

        .detail-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 16px;
          margin-bottom: 20px;
        }

        .detail-item {
          display: flex;
          flex-direction: column;
        }

        .detail-label {
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 4px;
          text-transform: uppercase;
          font-weight: 600;
        }

        .detail-value {
          font-size: 14px;
          color: #1f2937;
          font-weight: 500;
        }

        .task-notes {
          width: 100%;
          padding: 12px;
          border: 1px solid #e5e7eb;
          border-radius: 4px;
          margin-bottom: 12px;
          font-family: inherit;
          font-size: 13px;
          resize: vertical;
        }

        @media (max-width: 768px) {
          .task-manager {
            padding: 12px;
          }

          .task-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
          }

          .task-meta {
            flex-direction: column;
            gap: 12px;
          }

          .detail-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};
