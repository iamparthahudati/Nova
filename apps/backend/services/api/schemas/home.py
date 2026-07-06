from typing import Any, Optional

from pydantic import BaseModel, Field


class HomeCard(BaseModel):
    id: str
    label: str
    value: str
    icon: Optional[str] = None


class HomePanelItem(BaseModel):
    id: str
    primary: str
    secondary: Optional[str] = None
    meta: dict[str, Any] = Field(default_factory=dict)


class HomePanel(BaseModel):
    id: str
    title: str
    items: list[HomePanelItem] = Field(default_factory=list)


class HomeResponse(BaseModel):
    cards: list[HomeCard] = Field(default_factory=list)
    panels: list[HomePanel] = Field(default_factory=list)
