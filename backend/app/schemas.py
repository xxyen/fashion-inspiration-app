from pydantic import BaseModel, Field


class LocationContext(BaseModel):
    continent: str | None = None
    country: str | None = None
    city: str | None = None
    scene: str | None = None


class GarmentAttributes(BaseModel):
    garment_type: list[str] = Field(default_factory=list)
    style: list[str] = Field(default_factory=list)
    material: list[str] = Field(default_factory=list)
    color_palette: list[str] = Field(default_factory=list)
    pattern: list[str] = Field(default_factory=list)
    season: str | None = None
    occasion: list[str] = Field(default_factory=list)
    consumer_profile: list[str] = Field(default_factory=list)
    trend_notes: list[str] = Field(default_factory=list)
    location_context: LocationContext = Field(default_factory=LocationContext)


class ClassificationResult(BaseModel):
    description: str
    attributes: GarmentAttributes

