from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy.orm import Session
from app.database.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: Any, for_update: bool = False) -> Optional[ModelType]:
        query = self.db.query(self.model).filter(self.model.id == id)
        if for_update:
            query = query.with_for_update()
        return query.first()

    def get_all(self) -> List[ModelType]:
        return self.db.query(self.model).all()

    def create(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, instance: ModelType) -> ModelType:
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: ModelType) -> None:
        self.db.delete(instance)
        self.db.commit()
