#!/usr/bin/env python3
"""
SQLite Database Manager for TASKFINISHER AI
Provides persistence layer for task states, results, and execution history
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def _mirror_to_firebase(task_state: Dict[str, Any]) -> None:
    """Best-effort Firebase mirror; SQLite remains the local fallback."""
    try:
        from database.firebase_service import firebase_service

        firebase_service.save_task(task_state)
    except Exception:
        logger.warning("Failed to mirror task state to Firebase.", exc_info=True)


class TaskDatabase:
    """SQLite database manager for TASKFINISHER AI persistence"""
    
    def __init__(self, db_path: str = "taskfinisher_ai.db"):
        if not Path(db_path).is_absolute() and Path(db_path).parent == Path("."):
            base_dir = Path(__file__).resolve().parent.parent
            self.db_path = base_dir / db_path
        else:
            self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tasks table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        user_request TEXT NOT NULL,
                        status TEXT NOT NULL,
                        verdict TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_steps INTEGER DEFAULT 0,
                        total_steps INTEGER DEFAULT 0,
                        evidence_trail TEXT,  -- JSON stored as text
                        requires_human_approval BOOLEAN DEFAULT 0,
                        human_decision_point TEXT,
                        final_report TEXT,
                        artifacts TEXT,
                        completion_percentage REAL DEFAULT 0,
                        adk_trace TEXT,
                        scenario TEXT,
                        human_options TEXT,
                        final_summary TEXT
                    )
                ''')
                
                # Auto-migrate missing columns for existing SQLite tables
                cursor.execute("PRAGMA table_info(tasks)")
                existing_cols = {row[1] for row in cursor.fetchall()}
                new_columns = [
                    ("final_report", "TEXT"),
                    ("artifacts", "TEXT"),
                    ("completion_percentage", "REAL DEFAULT 0"),
                    ("adk_trace", "TEXT"),
                    ("scenario", "TEXT"),
                    ("human_options", "TEXT"),
                    ("final_summary", "TEXT"),
                ]
                for col_name, col_type in new_columns:
                    if col_name not in existing_cols:
                        cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
                
                # Create task steps table for detailed tracking
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_steps (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        step_id TEXT NOT NULL,
                        description TEXT NOT NULL,
                        status TEXT NOT NULL,
                        verified BOOLEAN DEFAULT 0,
                        retry_count INTEGER DEFAULT 0,
                        error_message TEXT,
                        evidence TEXT,  -- JSON stored as text
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                    )
                ''')
                
                # Create execution history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS execution_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        action TEXT NOT NULL,  -- started, completed, failed, etc.
                        details TEXT,  -- JSON stored as text
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                    )
                ''')

                # Create app settings table for durable backend configuration.
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_task_steps_task_id ON task_steps(task_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_execution_history_task_id ON execution_history(task_id)
                ''')
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def save_task(self, task_state: Dict[str, Any]) -> bool:
        """Save or update a task in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare evidence trail as JSON
                evidence_json = json.dumps(task_state.get('evidence_trail', []))
                user_req = task_state.get('user_request') or task_state.get('description') or task_state.get('title') or ''
                status_val = task_state.get('status') or 'PENDING'
                artifacts_json = json.dumps(task_state.get('artifacts', {}))
                adk_trace_json = json.dumps(task_state.get('adk_trace', []))
                human_options_json = json.dumps(task_state.get('human_options', []))
                final_rep = task_state.get('final_report') or task_state.get('final_summary') or ''
                
                # Insert or update task
                cursor.execute('''
                    INSERT OR REPLACE INTO tasks (
                        task_id, user_request, status, verdict, 
                        completed_steps, total_steps, evidence_trail,
                        requires_human_approval, human_decision_point,
                        final_report, artifacts, completion_percentage,
                        adk_trace, scenario, human_options, final_summary,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    task_state['task_id'],
                    user_req,
                    status_val,
                    task_state.get('verdict', ''),
                    task_state.get('completed_steps', 0),
                    task_state.get('total_steps', 0),
                    evidence_json,
                    task_state.get('requires_human_approval', False),
                    task_state.get('human_decision_point', ''),
                    final_rep,
                    artifacts_json,
                    task_state.get('completion_percentage', 0.0),
                    adk_trace_json,
                    task_state.get('scenario', 'success'),
                    human_options_json,
                    final_rep,
                ))
                
                # Save individual steps
                self._save_task_steps(cursor, task_state['task_id'], task_state.get('steps', {}))
                
                # Replace event history with the latest real orchestrator events.
                cursor.execute('DELETE FROM execution_history WHERE task_id = ?', (task_state['task_id'],))
                events = task_state.get('events') or []
                if events:
                    for event in events:
                        cursor.execute('''
                            INSERT INTO execution_history (task_id, action, details, timestamp)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            task_state['task_id'],
                            event.get('event') or event.get('type') or 'event',
                            json.dumps(event),
                            event.get('timestamp') or datetime.utcnow().isoformat(),
                        ))
                else:
                    cursor.execute('''
                        INSERT INTO execution_history (task_id, action, details)
                        VALUES (?, ?, ?)
                    ''', (
                        task_state['task_id'],
                        'task_saved',
                        json.dumps({
                            'status': task_state['status'],
                            'verdict': task_state.get('verdict', ''),
                            'completed_steps': task_state.get('completed_steps', 0)
                        })
                    ))
                
                conn.commit()
                logger.info(f"Task {task_state['task_id']} saved to database")
                _mirror_to_firebase(task_state)
                return True
                
        except Exception as e:
            logger.error(f"Failed to save task {task_state.get('task_id', 'unknown')}: {e}")
            return False
    
    def _save_task_steps(self, cursor, task_id: str, steps: Dict[str, Any]):
        """Save individual task steps to the database"""
        # Clear existing steps for this task
        cursor.execute('DELETE FROM task_steps WHERE task_id = ?', (task_id,))
        
        # Insert new steps
        for step_id, step_data in steps.items():
            evidence_json = json.dumps(step_data.get('evidence', []))
            cursor.execute('''
                INSERT INTO task_steps (
                    task_id, step_id, description, status, verified,
                    retry_count, error_message, evidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                step_id,
                step_data.get('description', ''),
                step_data.get('status', ''),
                step_data.get('verification_status') == 'PASS',
                step_data.get('attempts', step_data.get('retry_count', 0)),
                step_data.get('error') or step_data.get('error_message', ''),
                evidence_json
            ))
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a task from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # Convert row to dictionary
                task = dict(row)
                
                # Parse JSON fields
                task['evidence_trail'] = json.loads(task['evidence_trail']) if task.get('evidence_trail') else []
                task['artifacts'] = json.loads(task['artifacts']) if task.get('artifacts') else {}
                task['adk_trace'] = json.loads(task['adk_trace']) if task.get('adk_trace') else []
                task['human_options'] = json.loads(task['human_options']) if task.get('human_options') else []
                task['final_report'] = task.get('final_report') or task.get('final_summary') or ''
                task['completion_percentage'] = float(task.get('completion_percentage') or 0.0)
                
                # Get steps and events for this task
                task['steps'] = self.get_task_steps(task_id)
                task['events'] = self.get_execution_history(task_id)
                task['evidence'] = [item for step in task['steps'].values() for item in step.get('evidence', [])]
                
                return task
                
        except Exception as e:
            logger.error(f"Failed to retrieve task {task_id}: {e}")
            return None
    
    def get_task_steps(self, task_id: str) -> Dict[str, Any]:
        """Retrieve steps for a specific task"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM task_steps 
                    WHERE task_id = ? 
                    ORDER BY step_id
                ''', (task_id,))
                
                rows = cursor.fetchall()
                steps = {}
                
                for row in rows:
                    step = dict(row)
                    step['evidence'] = json.loads(step['evidence']) if step['evidence'] else []
                    steps[step['step_id']] = step
                
                return steps
                
        except Exception as e:
            logger.error(f"Failed to retrieve steps for task {task_id}: {e}")
            return {}
    
    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tasks from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM tasks 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                tasks = []
                
                for row in rows:
                    task = dict(row)
                    task['evidence_trail'] = json.loads(task['evidence_trail']) if task.get('evidence_trail') else []
                    task['artifacts'] = json.loads(task['artifacts']) if task.get('artifacts') else {}
                    task['adk_trace'] = json.loads(task['adk_trace']) if task.get('adk_trace') else []
                    task['human_options'] = json.loads(task['human_options']) if task.get('human_options') else []
                    task['final_report'] = task.get('final_report') or task.get('final_summary') or ''
                    task['completion_percentage'] = float(task.get('completion_percentage') or 0.0)
                    tasks.append(task)
                
                return tasks
                
        except Exception as e:
            logger.error(f"Failed to retrieve recent tasks: {e}")
            return []

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks ordered from newest to oldest."""
        return self.get_recent_tasks(limit=1000)

    def get_execution_history(self, task_id: str) -> List[Dict[str, Any]]:
        """Retrieve execution history/events for a task."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT action, details, timestamp FROM execution_history WHERE task_id = ? ORDER BY id',
                    (task_id,)
                )
                events = []
                for row in cursor.fetchall():
                    item = dict(row)
                    try:
                        item['details'] = json.loads(item['details']) if item['details'] else {}
                    except json.JSONDecodeError:
                        pass
                    if isinstance(item.get('details'), dict):
                        merged = dict(item['details'])
                        merged.setdefault('event', item['action'])
                        merged.setdefault('timestamp', item['timestamp'])
                        events.append(merged)
                        continue
                    events.append(item)
                return events
        except Exception as e:
            logger.error(f"Failed to retrieve execution history for task {task_id}: {e}")
            return []

    def get_all_steps(self) -> List[Dict[str, Any]]:
        """Retrieve all persisted steps for aggregate analytics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM task_steps ORDER BY task_id, step_id')
                steps = []
                for row in cursor.fetchall():
                    step = dict(row)
                    step['evidence'] = json.loads(step['evidence']) if step['evidence'] else []
                    steps.append(step)
                return steps
        except Exception as e:
            logger.error(f"Failed to retrieve all steps: {e}")
            return []

    def save_setting(self, key: str, value: Dict[str, Any]) -> bool:
        """Save a named JSON settings blob."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, json.dumps(value)))
                conn.commit()
                logger.info(f"Setting {key} saved to database")
                return True
        except Exception as e:
            logger.error(f"Failed to save setting {key}: {e}")
            return False

    def get_setting(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a named JSON settings blob."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT value, updated_at FROM app_settings WHERE key = ?', (key,))
                row = cursor.fetchone()
                if not row:
                    return None
                value = json.loads(row['value'])
                if isinstance(value, dict):
                    value.setdefault('updated_at', row['updated_at'])
                return value
        except Exception as e:
            logger.error(f"Failed to retrieve setting {key}: {e}")
            return None
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete related records first
                cursor.execute('DELETE FROM task_steps WHERE task_id = ?', (task_id,))
                cursor.execute('DELETE FROM execution_history WHERE task_id = ?', (task_id,))
                cursor.execute('DELETE FROM tasks WHERE task_id = ?', (task_id,))
                
                conn.commit()
                logger.info(f"Task {task_id} deleted from database")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get task counts by status
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM tasks 
                    GROUP BY status
                ''')
                status_counts = dict(cursor.fetchall())
                
                # Get total counts
                cursor.execute('SELECT COUNT(*) FROM tasks')
                total_tasks = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM task_steps')
                total_steps = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM execution_history')
                total_history = cursor.fetchone()[0]
                
                return {
                    'total_tasks': total_tasks,
                    'total_steps': total_steps,
                    'total_history_entries': total_history,
                    'status_distribution': status_counts,
                    'database_path': str(self.db_path),
                    'database_size_bytes': self.db_path.stat().st_size if self.db_path.exists() else 0
                }
                
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


# Global database instance
db_manager = TaskDatabase()
