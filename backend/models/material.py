from datetime import datetime

from extensions import db


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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

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
        return data


class MaterialChunk(db.Model):
    __tablename__ = "material_chunk"

    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey("material.id"), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    chroma_id = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

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
