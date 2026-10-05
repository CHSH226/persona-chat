"""人格分层管理 API。"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PersonaLayer

router = APIRouter(prefix="/api/persona", tags=["persona"])


class LayerCreate(BaseModel):
    name: str
    type: str = "custom"
    content: str
    weight: float = 1.0
    is_public: bool = True


@router.get("/layers")
def list_layers(db: Session = Depends(get_db)):
    return [
        {
            "id": l.id,
            "name": l.name,
            "type": l.type,
            "weight": l.weight,
            "is_public": l.is_public,
            "is_active": l.is_active,
            "content": l.content,
        }
        for l in db.query(PersonaLayer).order_by(PersonaLayer.id).all()
    ]


@router.post("/layers")
def create_layer(data: LayerCreate, db: Session = Depends(get_db)):
    layer = PersonaLayer(**data.dict())
    db.add(layer)
    db.commit()
    db.refresh(layer)
    return {"id": layer.id}


@router.delete("/layers/{layer_id}")
def delete_layer(layer_id: int, db: Session = Depends(get_db)):
    layer = db.get(PersonaLayer, layer_id)
    if not layer:
        return {"error": "不存在"}
    db.delete(layer)
    db.commit()
    return {"ok": True}
