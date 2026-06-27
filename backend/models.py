"""
Pydantic response models for Project Shikhara API.
These define the exact shape of data returned by each endpoint.
"""

from typing import Optional
from pydantic import BaseModel


# ── Contact & Hours ───────────────────────────────────────────────────────────

class TempleContact(BaseModel):
    phone:      list[str]
    email:      list[str]
    website:    list[str]
    facebook:   list[str]
    instagram:  list[str]


class TempleHours(BaseModel):
    Monday:     Optional[str] = None
    Tuesday:    Optional[str] = None
    Wednesday:  Optional[str] = None
    Thursday:   Optional[str] = None
    Friday:     Optional[str] = None
    Saturday:   Optional[str] = None
    Sunday:     Optional[str] = None


# ── Temple models ─────────────────────────────────────────────────────────────

class Temple(BaseModel):
    """Full temple data — used for both the table and the sidebar."""
    id:                 int
    name:               str
    street:             Optional[str] = None
    city:               Optional[str] = None
    postal_code:        Optional[str] = None
    state:              Optional[str] = None
    location_latitude:  Optional[float] = None
    location_longitude: Optional[float] = None
    google_maps_url:    Optional[str] = None
    note:               Optional[str] = None
    contact:            TempleContact
    opening_hours:      TempleHours


# ── Paginated response ────────────────────────────────────────────────────────

class PaginatedTemples(BaseModel):
    """Wraps a list of temples with pagination metadata."""
    total:      int
    page:       int
    page_size:  int
    pages:      int
    data:       list[Temple]


# ── City & State models ───────────────────────────────────────────────────────

class CityItem(BaseModel):
    city:           str
    temple_count:   int


class StateItem(BaseModel):
    state:          str
    temple_count:   int