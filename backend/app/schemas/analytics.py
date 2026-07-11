from pydantic import BaseModel


class SankeyNode(BaseModel):
    id: str
    name: str


class SankeyLink(BaseModel):
    source: str
    target: str
    value: int


class SankeyData(BaseModel):
    nodes: list[SankeyNode]
    links: list[SankeyLink]


class FunnelStage(BaseModel):
    name: str
    count: int


class FunnelData(BaseModel):
    stages: list[FunnelStage]


class StatusEventRead(BaseModel):
    id: int
    application_id: int
    from_status: str | None
    to_status: str
    timestamp: str
    note: str | None

    model_config = {"from_attributes": True}
