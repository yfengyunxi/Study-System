from sqlalchemy import inspect, text

from extensions import db


def ensure_schema_compatibility(app):
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        if not inspector.has_table("material"):
            return

        columns = {column["name"] for column in inspector.get_columns("material")}
        dialect = db.engine.dialect.name

        statements = []
        if "folder_id" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN folder_id INT NULL, ADD INDEX ix_material_folder_id (folder_id)")
            else:
                statements.append("ALTER TABLE material ADD COLUMN folder_id INTEGER")

        if "error_message" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN error_message TEXT")
            else:
                statements.append("ALTER TABLE material ADD COLUMN error_message TEXT DEFAULT ''")

        if "updated_at" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN updated_at DATETIME NULL")
            else:
                statements.append("ALTER TABLE material ADD COLUMN updated_at DATETIME")

        if "index_state" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN index_state VARCHAR(20) NOT NULL DEFAULT 'not_indexed'")
            else:
                statements.append("ALTER TABLE material ADD COLUMN index_state VARCHAR(20) DEFAULT 'not_indexed' NOT NULL")
        if "sync_state" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN sync_state VARCHAR(20) NOT NULL DEFAULT 'synced'")
            else:
                statements.append("ALTER TABLE material ADD COLUMN sync_state VARCHAR(20) DEFAULT 'synced' NOT NULL")
        if "active_index_generation" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN active_index_generation INT NOT NULL DEFAULT 0")
            else:
                statements.append("ALTER TABLE material ADD COLUMN active_index_generation INTEGER DEFAULT 0 NOT NULL")
        if "building_index_generation" not in columns:
            if dialect == "mysql":
                statements.append("ALTER TABLE material ADD COLUMN building_index_generation INT NULL")
            else:
                statements.append("ALTER TABLE material ADD COLUMN building_index_generation INTEGER")

        for statement in statements:
            db.session.execute(text(statement))

        if "updated_at" not in columns:
            db.session.execute(text("UPDATE material SET updated_at = created_at WHERE updated_at IS NULL"))
        if "error_message" not in columns:
            db.session.execute(text("UPDATE material SET error_message = '' WHERE error_message IS NULL"))
        db.session.execute(
            text("UPDATE material SET index_state = 'ready', active_index_generation = 1 WHERE status = 'ready' AND active_index_generation = 0")
        )
        db.session.execute(
            text("UPDATE material SET index_state = 'failed' WHERE status = 'failed' AND index_state = 'not_indexed'")
        )
        _reconcile_interrupted_reindex_jobs()

        db.session.commit()


def _reconcile_interrupted_reindex_jobs():
    inspector = inspect(db.engine)
    if not inspector.has_table("reindex_job"):
        return
    db.session.execute(
        text("UPDATE reindex_job SET status = 'stale', phase = 'stale_after_restart', retryable = 1 WHERE status IN ('queued', 'running')")
    )
