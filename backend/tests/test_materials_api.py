from datetime import datetime
from unittest.mock import patch

import pytest
from sqlalchemy import inspect

from extensions import db
from models.material import Material, MaterialFolder


def test_material_to_dict_includes_phase2_fields_and_counts(app, make_user, make_folder, make_material, make_chunk, make_visual_asset):
    user = make_user()
    folder = make_folder(user)
    material = make_material(user, folder=folder, title="数据库讲义", status="ready")
    make_chunk(material, index=0)
    make_chunk(material, index=1)
    ready_asset = make_visual_asset(material, index=0, status="ready")
    make_visual_asset(material, index=1, status="failed")

    data = material.to_dict()

    assert data["updated_at"] == data["created_at"]
    assert data["error_message"] == ""
    assert data["chunk_count"] == 2
    assert data["visual_asset_count"] == 2
    assert data["ready_visual_asset_count"] == 1
    assert data["failed_visual_asset_count"] == 1
    assert data["preview_asset_id"] == ready_asset.id


def test_folder_to_dict_includes_status_counts(app, make_user, make_folder, make_material):
    user = make_user()
    folder = make_folder(user)
    make_material(user, folder=folder, status="ready")
    make_material(user, folder=folder, status="processing")
    make_material(user, folder=folder, status="failed")

    data = folder.to_dict(include_count=True)

    assert data["material_count"] == 3
    assert data["ready_count"] == 1
    assert data["processing_count"] == 1
    assert data["failed_count"] == 1


def test_schema_compatibility_adds_material_updated_at_and_error_message(app):
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("material")}

    assert "updated_at" in columns
    assert "error_message" in columns


def test_material_folders_return_status_counts(client, auth_headers, make_folder, make_material):
    headers, user = auth_headers()
    folder = make_folder(user, name="数据库")
    make_material(user, folder=folder, status="ready")
    make_material(user, folder=folder, status="failed")
    make_material(user, folder=folder, status="processing")

    response = client.get("/api/material-folders", headers=headers)

    assert response.status_code == 200
    row = response.get_json()[0]
    assert row["material_count"] == 3
    assert row["ready_count"] == 1
    assert row["failed_count"] == 1
    assert row["processing_count"] == 1


def test_material_list_filters_and_sorts(client, auth_headers, make_folder, make_material, make_chunk, make_visual_asset):
    headers, user = auth_headers()
    folder = make_folder(user, name="数据库")
    ready = make_material(user, folder=folder, title="索引讲义", status="ready", file_type="pdf", keywords="索引,事务")
    failed = make_material(user, folder=None, title="失败资料", status="failed", file_type="txt", keywords="失败")
    make_chunk(ready, index=0)
    make_visual_asset(ready, index=0, status="ready")

    response = client.get("/api/materials?q=索引&status=ready&file_type=pdf&has_visual_assets=true&sort=richness_desc", headers=headers)

    assert response.status_code == 200
    rows = response.get_json()
    assert [row["id"] for row in rows] == [ready.id]
    assert rows[0]["visual_asset_count"] == 1
    assert rows[0]["chunk_count"] == 1
    assert failed.id not in [row["id"] for row in rows]


@pytest.mark.parametrize("query", ["status=done", "has_visual_assets=maybe"])
def test_material_list_invalid_filters_return_400(client, auth_headers, query):
    headers, _user = auth_headers()

    response = client.get(f"/api/materials?{query}", headers=headers)

    assert response.status_code == 400


def test_material_list_cross_user_folder_returns_404(client, auth_headers, make_user, make_folder):
    headers, _user = auth_headers()
    other = make_user("other-user")
    other_folder = make_folder(other, name="别人的文件夹")

    response = client.get(f"/api/materials?folder_id={other_folder.id}", headers=headers)

    assert response.status_code == 404


def test_material_processing_failure_uses_error_message(client, auth_headers, tmp_path):
    headers, _user = auth_headers()
    file_path = tmp_path / "bad.txt"
    file_path.write_text("bad", encoding="utf-8")

    with patch("routes.materials.extract_text", side_effect=RuntimeError("解析失败")):
        with file_path.open("rb") as handle:
            response = client.post(
                "/api/materials/upload",
                headers=headers,
                data={"file": (handle, "bad.txt")},
                content_type="multipart/form-data",
            )

    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "failed"
    assert "解析失败" in data["error_message"]
    assert data["summary"] == ""
