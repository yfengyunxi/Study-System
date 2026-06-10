import json
from flask import current_app

from extensions import db
from models.material import Material, MaterialChunk, MaterialFolder, MaterialVisualAsset
from services.ai_service import AIService
from services.vector_store_service import VectorStoreService
from services.visual_service import delete_visual_asset_files


class RAGService:
    def __init__(self):
        self.ai = AIService()
        self.vector_store = VectorStoreService(current_app.config["TEXT_VECTOR_COLLECTION"])
        self.visual_store = VectorStoreService(current_app.config["VISUAL_VECTOR_COLLECTION"])

    def index_material(self, material, chunks, generation=None):
        generation = generation or material.active_index_generation or 1
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        chunk_models = []

        for index, content in enumerate(chunks):
            chroma_id = f"user-{material.user_id}-material-{material.id}-gen-{generation}-chunk-{index}"
            ids.append(chroma_id)
            documents.append(content)
            embeddings.append(self.ai.embed(content))
            metadatas.append(
                {
                    "user_id": material.user_id,
                    "folder_id": material.folder_id or 0,
                    "material_id": material.id,
                    "generation": generation,
                    "chunk_index": index,
                    "title": material.title,
                    "folder_name": material.folder.name if material.folder else "",
                }
            )
            chunk_models.append(
                MaterialChunk(
                    material_id=material.id,
                    chunk_index=index,
                    content=content,
                    chroma_id=chroma_id,
                )
            )

        if ids:
            self.vector_store.upsert(ids, documents, embeddings, metadatas)
            db.session.add_all(chunk_models)

    def reindex_material(self, material, chunks, generation=None):
        generation = generation or (material.active_index_generation or 0) + 1
        self.delete_material_generation_vectors(material.user_id, material.id, generation)
        MaterialChunk.query.filter_by(material_id=material.id).delete()
        db.session.flush()
        self.index_material(material, chunks, generation=generation)

    def index_visual_assets(self, material, asset_payloads, reindex=False, generation=None):
        generation = generation or material.active_index_generation or 1
        if reindex:
            self.delete_material_visual_vectors(material.user_id, material.id)
            MaterialVisualAsset.query.filter_by(material_id=material.id).delete()
            db.session.flush()

        ids = []
        documents = []
        embeddings = []
        metadatas = []
        asset_models = []

        for payload in asset_payloads:
            index = payload["asset_index"]
            chroma_id = f"user-{material.user_id}-material-{material.id}-gen-{generation}-visual-{index}"
            caption = payload.get("caption") or f"{material.title} 视觉资料 {index + 1}"
            asset = MaterialVisualAsset(
                user_id=material.user_id,
                material_id=material.id,
                folder_id=material.folder_id,
                asset_type=payload["asset_type"],
                asset_index=index,
                page_number=payload.get("page_number"),
                caption=caption,
                image_path=payload["image_path"],
                chroma_id=chroma_id,
                status="processing",
            )
            if not self.ai.multimodal_enabled:
                asset.status = "failed"
                asset.error_message = "未配置多模态 embedding API，视觉资料已提取但未入向量库"
                asset_models.append(asset)
                continue

            try:
                embedding = self.ai.embed_multimodal_image(payload["image_path"])
                asset.status = "ready"
                ids.append(chroma_id)
                documents.append(caption)
                embeddings.append(embedding)
                metadatas.append(
                    {
                        "type": "image",
                        "user_id": material.user_id,
                        "folder_id": material.folder_id or 0,
                        "material_id": material.id,
                        "generation": generation,
                        "asset_index": index,
                        "asset_type": payload["asset_type"],
                        "page_number": payload.get("page_number") or 0,
                        "title": material.title,
                        "folder_name": material.folder.name if material.folder else "",
                    }
                )
            except Exception as exc:
                asset.status = "failed"
                asset.error_message = str(exc)
            asset_models.append(asset)

        if ids:
            self.visual_store.upsert(ids, documents, embeddings, metadatas)
        if asset_models:
            db.session.add_all(asset_models)

    def sync_material_folder_metadata(self, material):
        folder_name = material.folder.name if material.folder else ""
        folder_id = material.folder_id or 0
        metadata = {"folder_id": folder_id, "folder_name": folder_name}
        where = {"$and": [{"user_id": material.user_id}, {"material_id": material.id}]}
        self.vector_store.update_metadata_where(where, metadata)
        self.visual_store.update_metadata_where(where, metadata)
        MaterialVisualAsset.query.filter_by(user_id=material.user_id, material_id=material.id).update(
            {"folder_id": material.folder_id}
        )
        return True

    def search(self, user_id, question, material_id=None, folder_id=None, top_k=None):
        top_k = top_k or current_app.config["RAG_TOP_K"]
        where = {"user_id": user_id}
        if material_id:
            where = {"$and": [{"user_id": user_id}, {"material_id": material_id}]}
        elif folder_id:
            where = {"$and": [{"user_id": user_id}, {"folder_id": folder_id}]}

        embedding = self.ai.embed(question)
        try:
            result = self.vector_store.query(embedding, top_k, where)
        except Exception:
            return self._fallback_search(user_id, question, material_id, folder_id, top_k)

        references = []
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for content, metadata, distance in zip(documents, metadatas, distances):
            material = Material.query.filter_by(id=metadata.get("material_id"), user_id=user_id).first()
            if not material:
                continue
            if material_id and material.id != material_id:
                continue
            if folder_id and material.folder_id != folder_id:
                continue
            references.append(
                {
                    "type": "text",
                    "material_id": material.id,
                    "folder_id": material.folder_id,
                    "folder_name": material.folder.name if material.folder else "",
                    "title": material.title,
                    "chunk_index": metadata.get("chunk_index"),
                    "content": content,
                    "score": distance,
                    "generation": metadata.get("generation"),
                }
            )
        return references

    def search_visual(self, user_id, question, material_id=None, folder_id=None, top_k=None):
        if not self.ai.multimodal_enabled:
            return []

        top_k = top_k or current_app.config["MULTIMODAL_TOP_K"]
        where = {"user_id": user_id}
        if material_id:
            where = {"$and": [{"user_id": user_id}, {"material_id": material_id}]}
        elif folder_id:
            where = {"$and": [{"user_id": user_id}, {"folder_id": folder_id}]}

        embedding = self.ai.embed_multimodal_text(question)
        try:
            result = self.visual_store.query(embedding, top_k, where)
        except Exception:
            current_app.logger.warning("Visual RAG search failed", exc_info=True)
            return []

        references = []
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        for content, metadata, distance in zip(documents, metadatas, distances):
            asset = MaterialVisualAsset.query.filter_by(
                user_id=user_id,
                material_id=metadata.get("material_id"),
                asset_index=metadata.get("asset_index"),
                status="ready",
            ).first()
            if not asset:
                continue
            if material_id and asset.material_id != material_id:
                continue
            if folder_id and asset.folder_id != folder_id:
                continue
            references.append(
                {
                    "type": "image",
                    "asset_id": asset.id,
                    "material_id": asset.material_id,
                    "folder_id": asset.folder_id,
                    "folder_name": asset.material.folder.name if asset.material.folder else "",
                    "title": asset.material.title,
                    "asset_type": asset.asset_type,
                    "asset_index": asset.asset_index,
                    "page_number": asset.page_number,
                    "caption": asset.caption or content,
                    "image_url": f"/api/materials/assets/{asset.id}/image",
                    "score": distance,
                    "generation": metadata.get("generation"),
                }
            )
        return references

    def answer(self, user_id, question, scope_type=None, material_id=None, folder_id=None, conversation=None):
        scope_type = scope_type or ("material" if material_id else "folder" if folder_id else "all")
        if scope_type == "material":
            material = Material.query.filter_by(id=material_id, user_id=user_id).first()
            if not material:
                raise ValueError("资料不存在")
            if material.status != "ready" and not material.active_index_generation:
                raise ValueError("该资料尚未处理完成，暂不能用于问答")
        elif scope_type == "folder":
            folder = MaterialFolder.query.filter_by(id=folder_id, user_id=user_id).first()
            if not folder:
                raise ValueError("文件夹不存在")
            ready_count = Material.query.filter_by(user_id=user_id, folder_id=folder_id, status="ready").count()
            if ready_count == 0:
                raise ValueError("该文件夹暂无可问答的资料")
        elif scope_type == "uncategorized":
            ready_count = Material.query.filter_by(user_id=user_id, folder_id=None, status="ready").count()
            if ready_count == 0:
                raise ValueError("未分类暂无可问答的资料")
        elif scope_type == "all":
            ready_count = Material.query.filter_by(user_id=user_id, status="ready").count()
            if ready_count == 0:
                raise ValueError("当前暂无可问答的资料，请先上传并处理资料，或切换为通用问答")
        else:
            raise ValueError("问答范围参数无效")

        scoped_material_id = material_id if scope_type == "material" else None
        scoped_folder_id = folder_id if scope_type == "folder" else None
        text_references = self.search(user_id, question, scoped_material_id, scoped_folder_id)
        visual_references = self.search_visual(user_id, question, scoped_material_id, scoped_folder_id)
        references = text_references + visual_references
        answer = self.ai.answer(question, references, conversation=conversation)
        return answer, references

    def delete_material_vectors(self, user_id, material_id):
        try:
            self.vector_store.delete(where={"$and": [{"user_id": user_id}, {"material_id": material_id}]})
        except Exception:
            current_app.logger.warning(
                "Failed to delete chroma vectors for material %s", material_id, exc_info=True
            )

    def delete_material_visual_vectors(self, user_id, material_id):
        try:
            self.visual_store.delete(where={"$and": [{"user_id": user_id}, {"material_id": material_id}]})
        except Exception:
            current_app.logger.warning(
                "Failed to delete visual chroma vectors for material %s", material_id, exc_info=True
            )

    def delete_material_generation_vectors(self, user_id, material_id, generation):
        try:
            self.vector_store.delete(where={"$and": [{"user_id": user_id}, {"material_id": material_id}, {"generation": generation}]})
        except Exception:
            current_app.logger.warning("Failed to delete generation vectors for material %s", material_id, exc_info=True)

    def delete_old_material_generations(self, user_id, material_id, keep_generation):
        self.delete_material_vectors(user_id, material_id)

    def delete_material_indexes(self, material):
        self.delete_material_vectors(material.user_id, material.id)
        self.delete_material_visual_vectors(material.user_id, material.id)
        delete_visual_asset_files(material)

    def _fallback_search(self, user_id, question, material_id, folder_id, top_k):
        query = MaterialChunk.query.join(Material).filter(Material.user_id == user_id)
        if material_id:
            query = query.filter(MaterialChunk.material_id == material_id)
        elif folder_id:
            query = query.filter(Material.folder_id == folder_id)
        chunks = query.limit(200).all()
        terms = [item for item in question.lower().split() if item]
        scored = []
        for chunk in chunks:
            content_lower = chunk.content.lower()
            score = sum(content_lower.count(term) for term in terms) if terms else 0
            if score or not terms:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        references = []
        for score, chunk in scored[:top_k]:
            references.append(
                {
                    "type": "text",
                    "material_id": chunk.material_id,
                    "folder_id": chunk.material.folder_id,
                    "folder_name": chunk.material.folder.name if chunk.material.folder else "",
                    "title": chunk.material.title,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "score": score,
                    "generation": chunk.material.active_index_generation,
                }
            )
        return references


def references_to_json(references):
    normalized = []
    for item in references or []:
        ref_type = item.get("type") or "text"
        material_title = item.get("material_title") or item.get("title") or ""
        content_preview = (item.get("content_preview") or item.get("content") or item.get("snippet") or "")[:300]
        normalized.append(
            {
                "type": "visual" if ref_type == "image" else ref_type,
                "legacy_type": ref_type,
                "material_id": item.get("material_id"),
                "material_title": material_title,
                "folder_id": item.get("folder_id"),
                "folder_name": item.get("folder_name") or item.get("folder") or "",
                "chunk_id": item.get("chunk_id"),
                "chunk_index": item.get("chunk_index"),
                "asset_id": item.get("asset_id"),
                "asset_index": item.get("asset_index"),
                "page_number": item.get("page_number"),
                "caption": item.get("caption"),
                "content_preview": content_preview,
                "score": item.get("score"),
                "generation": item.get("generation"),
                "title": material_title,
                "content": content_preview,
            }
        )
    return json.dumps(normalized, ensure_ascii=False)
