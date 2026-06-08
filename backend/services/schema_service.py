from sqlalchemy import inspect, text

from extensions import db


def ensure_schema_compatibility(app):
    with app.app_context():
        db.create_all()
        inspector = inspect(db.engine)
        if not inspector.has_table("material"):
            return

        columns = {column["name"] for column in inspector.get_columns("material")}
        if "folder_id" in columns:
            return

        dialect = db.engine.dialect.name
        if dialect == "mysql":
            statement = "ALTER TABLE material ADD COLUMN folder_id INT NULL, ADD INDEX ix_material_folder_id (folder_id)"
        else:
            statement = "ALTER TABLE material ADD COLUMN folder_id INTEGER"

        db.session.execute(text(statement))
        db.session.commit()
