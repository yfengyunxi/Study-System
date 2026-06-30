import json

from extensions import db
from services.time_service import utc_now


class Material(db.Model):
    __tablename__ = "material"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    folder_id = db.Column(db.Integer, db.ForeignKey("material_folder.id"), nullable=True, index=True)
    title = db.Column(db.String(200), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(20), nullable=False)
    summary = db.Column(db.Text, default="")
    keywords = db.Column(db.String(500), default="")
    status = db.Column(db.String(20), default="processing", nullable=False)
    index_state = db.Column(db.String(20), default="not_indexed", nullable=False)
    sync_state = db.Column(db.String(20), default="synced", nullable=False)
    active_index_generation = db.Column(db.Integer, default=0, nullable=False)
    building_index_generation = db.Column(db.Integer, nullable=True)
    error_message = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=utc_now, nullable=True)

    chunks = db.relationship(
        "MaterialChunk",
        backref="material",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="MaterialChunk.chunk_index",
    )
    visual_assets = db.relationship(
        "MaterialVisualAsset",
        backref="material",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="MaterialVisualAsset.asset_index",
    )

    def to_dict(self, include_chunks=False):
        ready_assets = [asset for asset in self.visual_assets if asset.status == "ready"]
        failed_assets = [asset for asset in self.visual_assets if asset.status == "failed"]
        preview_asset = ready_assets[0] if ready_assets else None
        created_at = self.created_at.isoformat() if self.created_at else None
        updated_value = getattr(self, "updated_at", None) or self.created_at
        updated_at = updated_value.isoformat() if updated_value else created_at
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "folder_id": self.folder_id,
            "folder_name": self.folder.name if self.folder else "",
            "title": self.title,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "summary": self.summary,
            "keywords": [item for item in (self.keywords or "").split(",") if item],
            "status": self.status,
            "index_state": self.index_state,
            "sync_state": self.sync_state,
            "active_index_generation": self.active_index_generation,
            "building_index_generation": self.building_index_generation,
            "error_message": getattr(self, "error_message", "") or "",
            "created_at": created_at,
            "updated_at": updated_at,
            "chunk_count": len(self.chunks),
            "visual_asset_count": len(self.visual_assets),
            "ready_visual_asset_count": len(ready_assets),
            "failed_visual_asset_count": len(failed_assets),
            "preview_asset_id": preview_asset.id if preview_asset else None,
        }
        if include_chunks:
            data["chunks"] = [chunk.to_dict() for chunk in self.chunks]
            data["visual_assets"] = [asset.to_dict() for asset in self.visual_assets]
        return data


class MaterialFolder(db.Model):
    __tablename__ = "material_folder"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    materials = db.relationship("Material", backref="folder", lazy=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "name", name="uq_material_folder_user_name"),
    )

    def to_dict(self, include_count=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_count:
            data["material_count"] = len(self.materials)
            data["ready_count"] = len([item for item in self.materials if item.status == "ready"])
            data["processing_count"] = len([item for item in self.materials if item.status == "processing"])
            data["failed_count"] = len([item for item in self.materials if item.status == "failed"])
        return data


class MaterialChunk(db.Model):
    __tablename__ = "material_chunk"

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    chroma_id = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "material_id": self.material_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "chroma_id": self.chroma_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MaterialVisualAsset(db.Model):
    __tablename__ = "material_visual_asset"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=False, index=True)
    folder_id = db.Column(db.Integer, db.ForeignKey("material_folder.id"), nullable=True, index=True)
    asset_type = db.Column(db.String(30), nullable=False)
    asset_index = db.Column(db.Integer, nullable=False)
    page_number = db.Column(db.Integer, nullable=True)
    caption = db.Column(db.String(500), default="")
    image_path = db.Column(db.String(500), nullable=False)
    chroma_id = db.Column(db.String(160), unique=True, nullable=False)
    status = db.Column(db.String(20), default="processing", nullable=False)
    error_message = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "material_id": self.material_id,
            "folder_id": self.folder_id,
            "asset_type": self.asset_type,
            "asset_index": self.asset_index,
            "page_number": self.page_number,
            "caption": self.caption,
            "image_url": f"/api/materials/assets/{self.id}/image",
            "chroma_id": self.chroma_id,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReindexJob(db.Model):
    __tablename__ = "reindex_job"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=False, index=True)
    generation = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="queued", nullable=False, index=True)
    phase = db.Column(db.String(50), default="queued", nullable=False)
    progress_json = db.Column(db.Text, default="{}", nullable=False)
    last_error = db.Column(db.Text, nullable=True)
    error_code = db.Column(db.String(50), nullable=True)
    retryable = db.Column(db.Boolean, default=False, nullable=False)
    request_id = db.Column(db.String(120), nullable=True, index=True)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=utc_now, nullable=True)

    material = db.relationship("Material", backref=db.backref("reindex_jobs", lazy=True, order_by="ReindexJob.created_at.desc()"))

    def progress(self):
        try:
            return json.loads(self.progress_json or "{}")
        except json.JSONDecodeError:
            return {}

    def set_progress(self, **values):
        progress = self.progress()
        progress.update(values)
        self.progress_json = json.dumps(progress, ensure_ascii=False)

    def to_dict(self):
        return {
            "job_id": self.id,
            "material_id": self.material_id,
            "generation": self.generation,
            "status": self.status,
            "phase": self.phase,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "progress": self.progress(),
            "last_error": self.last_error,
            "error_code": self.error_code,
            "retryable": self.retryable,
            "poll_url": f"/api/materials/{self.material_id}/index-status",
        }
