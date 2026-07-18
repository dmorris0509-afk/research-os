from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from research_os.domain.errors import NotFoundError

ModelT = TypeVar("ModelT")


class Repository(Generic[ModelT]):
    def __init__(self, session: Session, model: type[ModelT]):
        self.session = session
        self.model = model

    def add(self, **values: Any) -> ModelT:
        entity = self.model(**values)
        self.session.add(entity)
        self.session.flush()
        return entity

    def get(self, entity_id: int) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def require(self, entity_id: int) -> ModelT:
        entity = self.get(entity_id)
        if entity is None:
            raise NotFoundError(f"{self.model.__name__} {entity_id} not found")
        return entity

    def list(self, *, project_id: int | None = None, limit: int = 100, offset: int = 0) -> Sequence[ModelT]:
        statement: Select = select(self.model)
        if project_id is not None:
            statement = statement.where(self.model.project_id == project_id)
        statement = statement.order_by(self.model.id.desc()).offset(offset).limit(limit)
        return tuple(self.session.scalars(statement))

    def delete(self, entity_id: int) -> None:
        self.session.delete(self.require(entity_id))
        self.session.flush()
