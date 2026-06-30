from datetime import date

from extensions import db
from services.time_service import utc_now


class StudyPlan(db.Model):
    __tablename__ = "study_plan"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    tasks = db.relationship(
        "StudyTask",
        backref="plan",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="StudyTask.due_date",
    )

    def _task_summary(self):
        tasks = list(self.tasks)
        done_tasks = [task for task in tasks if task.status == "done"]
        todo_tasks = [task for task in tasks if task.status != "done"]
        overdue_tasks = [task for task in todo_tasks if task.due_date and task.due_date < date.today()]
        next_due = sorted(
            [task for task in todo_tasks if task.due_date],
            key=lambda task: task.due_date,
        )
        if tasks and len(done_tasks) == len(tasks):
            status = "completed"
        elif overdue_tasks:
            status = "overdue"
        elif not tasks:
            status = "empty"
        elif self.start_date and date.today() < self.start_date and not done_tasks:
            status = "not_started"
        else:
            status = "active"
        return {
            "task_count": len(tasks),
            "done_count": len(done_tasks),
            "todo_count": len(todo_tasks),
            "progress_percent": round(len(done_tasks) / len(tasks) * 100) if tasks else 0,
            "next_due_task": next_due[0].to_dict() if next_due else None,
            "status": status,
            "overdue_count": len(overdue_tasks),
        }

    def to_dict(self, include_tasks=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        data.update(self._task_summary())
        if include_tasks:
            data["tasks"] = [task.to_dict() for task in self.tasks]
        return data


class StudyTask(db.Model):
    __tablename__ = "study_task"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("study_plan.id"), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    due_date = db.Column(db.Date, nullable=True, index=True)
    status = db.Column(db.String(20), default="todo", nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        today = date.today()
        is_overdue = self.status != "done" and self.due_date is not None and self.due_date < today
        days_until_due = (self.due_date - today).days if self.due_date else None
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "plan_title": self.plan.title if self.plan else "",
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_overdue": is_overdue,
            "days_until_due": days_until_due,
        }
