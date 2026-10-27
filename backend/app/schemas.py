from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    image_key: str = Field(exclude=True)
    created_at: datetime

    @computed_field
    @property
    def image_url(self) -> str:
        # картинки отдаются через API, MinIO наружу не открыт
        return f"/api/media/{self.image_key}"
