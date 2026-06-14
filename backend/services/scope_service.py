from models.material import Material, MaterialFolder


class InvalidScopeError(ValueError):
    def __init__(self, message, code="INVALID_SCOPE_TYPE", *, details=None):
        super().__init__(message)
        self.code = code
        self.details = details or {}


def _coerce_int(value, label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise InvalidScopeError(f"{label} 必须是数字", "VALIDATION_ERROR", details={label: value})


def normalize_scope(payload):
    payload = payload or {}
    scope_type = (payload.get("scope_type") or "all").strip()
    if scope_type == "general":
        return {"scope_type": "general"}
    if scope_type == "all":
        return {"scope_type": "all"}
    if scope_type == "uncategorized":
        return {"scope_type": "uncategorized", "folder_id": None}
    if scope_type == "folder":
        return {"scope_type": "folder", "folder_id": _coerce_int(payload.get("folder_id"), "folder_id")}
    if scope_type == "material":
        return {"scope_type": "material", "material_id": _coerce_int(payload.get("material_id"), "material_id")}
    raise InvalidScopeError("问答范围参数无效", "INVALID_SCOPE_TYPE", details={"scope_type": scope_type})


def validate_scope_for_user(user_id, payload):
    scope = normalize_scope(payload)
    scope_type = scope["scope_type"]
    if scope_type in {"general", "all", "uncategorized"}:
        return scope
    if scope_type == "folder":
        folder = MaterialFolder.query.filter_by(id=scope["folder_id"], user_id=user_id).first()
        if not folder:
            raise InvalidScopeError("文件夹不存在", "NOT_FOUND", details={"folder_id": scope["folder_id"]})
        return scope
    if scope_type == "material":
        material = Material.query.filter_by(id=scope["material_id"], user_id=user_id).first()
        if not material:
            raise InvalidScopeError("资料不存在", "MATERIAL_NOT_FOUND", details={"material_id": scope["material_id"]})
        if material.status != "ready" and not getattr(material, "active_index_generation", 0):
            raise InvalidScopeError("该资料尚未处理完成，暂不能用于问答", "MATERIAL_NOT_READY", details={"material_id": material.id})
        return scope
    raise InvalidScopeError("问答范围参数无效", "INVALID_SCOPE_TYPE")
