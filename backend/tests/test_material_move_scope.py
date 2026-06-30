from unittest.mock import patch

from extensions import db
from models.material import MaterialVisualAsset
from services.rag_service import RAGService


def test_move_uncategorized_material_to_folder(client, auth_headers, make_folder, make_material, make_visual_asset):
    headers, user = auth_headers()
    target = make_folder(user, name="数据仓库")
    material = make_material(user, folder=None, title="未分类资料", status="ready")
    asset = make_visual_asset(material, status="ready")

    with patch("routes.materials.RAGService") as rag_cls:
        rag_cls.return_value.sync_material_folder_metadata.return_value = True
        response = client.patch(
            f"/api/materials/{material.id}/folder",
            headers=headers,
            json={"folder_id": target.id, "request_id": "move-1"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is True
    assert data["sync_state"] == "synced"
    assert data["material"]["folder_id"] == target.id
    assert data["material"]["folder_name"] == "数据仓库"
    assert {item["folder_id"] for item in data["folder_counts"]} == {target.id, None}

    db.session.refresh(material)
    db.session.refresh(asset)
    assert material.folder_id == target.id
    assert material.sync_state == "synced"
    assert material.index_state == "ready"
    assert asset.folder_id == target.id
    rag_cls.return_value.sync_material_folder_metadata.assert_called_once_with(material)


def test_move_material_to_uncategorized(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, folder=folder, status="ready")

    with patch("routes.materials.RAGService") as rag_cls:
        rag_cls.return_value.sync_material_folder_metadata.return_value = True
        response = client.patch(
            f"/api/materials/{material.id}/folder",
            headers=headers,
            json={"folder_id": None, "request_id": "move-uncategorized"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is True
    assert data["material"]["folder_id"] is None
    assert data["material"]["folder_name"] == ""


def test_move_material_same_target_is_noop(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, folder=folder, status="ready")

    with patch("routes.materials.RAGService") as rag_cls:
        response = client.patch(
            f"/api/materials/{material.id}/folder",
            headers=headers,
            json={"folder_id": folder.id, "request_id": "move-same"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is False
    assert data["sync_state"] == "synced"
    rag_cls.return_value.sync_material_folder_metadata.assert_not_called()


def test_move_material_rejects_cross_user_folder(client, auth_headers, make_user, make_folder, make_material):
    headers, user = auth_headers()
    other = make_user("other-user")
    other_folder = make_folder(other, name="other-folder")
    material = make_material(user, status="ready")

    response = client.patch(
        f"/api/materials/{material.id}/folder",
        headers=headers,
        json={"folder_id": other_folder.id, "request_id": "move-cross-user"},
    )

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"]["code"] == "NOT_FOUND"


def test_move_material_sync_failure_marks_stale_but_keeps_sql_change(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, status="ready")

    with patch("routes.materials.RAGService") as rag_cls:
        rag_cls.return_value.sync_material_folder_metadata.side_effect = RuntimeError("chroma unavailable")
        response = client.patch(
            f"/api/materials/{material.id}/folder",
            headers=headers,
            json={"folder_id": folder.id, "request_id": "move-sync-fail"},
        )

    assert response.status_code == 200
    data = response.get_json()
    assert data["changed"] is True
    assert data["sync_state"] == "sync_failed"
    assert data["error_code"] == "VECTOR_SYNC_FAILED"
    assert data["retryable"] is True
    assert data["material"]["folder_id"] == folder.id
    assert data["material"]["index_state"] == "stale"

    db.session.refresh(material)
    assert material.folder_id == folder.id
    assert material.sync_state == "sync_failed"
    assert material.index_state == "stale"


def test_fallback_search_uses_live_sql_folder_after_move(app, make_user, make_folder, make_material, make_chunk):
    user = make_user()
    old_folder = make_folder(user, name="旧文件夹")
    new_folder = make_folder(user, name="新文件夹")
    material = make_material(user, folder=old_folder, status="ready")
    make_chunk(material, content="事实表围绕业务过程建立")

    material.folder_id = new_folder.id
    db.session.commit()

    rag = RAGService()
    old_refs = rag._fallback_search(user.id, "事实表", folder_id=old_folder.id, top_k=5)
    new_refs = rag._fallback_search(user.id, "事实表", folder_id=new_folder.id, top_k=5)

    assert old_refs == []
    assert len(new_refs) == 1
    assert new_refs[0]["folder_id"] == new_folder.id
    assert new_refs[0]["folder_name"] == "新文件夹"


def test_sync_material_folder_metadata_updates_visual_rows_and_calls_vector_services(app, make_user, make_folder, make_material, make_visual_asset):
    user = make_user()
    folder = make_folder(user)
    material = make_material(user, folder=folder, status="ready")
    asset = make_visual_asset(material, status="ready")

    calls = []

    with patch.object(RAGService, "__init__", lambda self: None):
        rag = RAGService()
        rag.vector_store = type("Store", (), {"update_metadata_where": lambda self, where, metadata: calls.append((where, metadata))})()
        rag.visual_store = type("Store", (), {"update_metadata_where": lambda self, where, metadata: calls.append((where, metadata))})()
        rag.sync_material_folder_metadata(material)

    db.session.refresh(asset)
    assert asset.folder_id == folder.id
    assert len(calls) == 2


def test_delete_folder_moves_materials_uncategorized_and_marks_projection_stale(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user)
    material = make_material(user, folder=folder, status="ready")

    response = client.delete(f"/api/material-folders/{folder.id}", headers=headers)

    assert response.status_code == 200
    db.session.refresh(material)
    assert material.folder_id is None
    assert material.sync_state == "sync_pending"
    assert material.index_state == "stale"
