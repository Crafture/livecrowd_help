from pydantic import BaseModel
from pydantic import field_validator


class FAQCSVRow(BaseModel):
    question: str
    answer: str
    event: str  # event slug
    tags: list[str]  # will be split into a list

    @field_validator("tags", mode="before")
    @classmethod
    def split_tags(cls, v):
        # Accept either a list or a comma-separated string
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(",") if tag.strip()]
        return v


class TagCSVRow(BaseModel):
    tag: str
