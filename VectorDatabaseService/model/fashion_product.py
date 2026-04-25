from typing import Optional
from pydantic import BaseModel, Field


class FashionProductBase(BaseModel):
    """Common scalar fields for all fashion product models."""
    product_name:    str = Field(..., max_length=511, description="Naziv proizvoda")
    gender:          str = Field("", max_length=31,  description="Men | Women | Boys | Girls | Unisex")
    master_category: str = Field("", max_length=63,  description="Apparel | Footwear | Accessories | ...")
    sub_category:    str = Field("", max_length=63,  description="Topwear | Shoes | Bags | ...")
    article_type:    str = Field("", max_length=63,  description="T-Shirts | Jeans | Sneakers | ...")
    base_colour:     str = Field("", max_length=63,  description="Blue | Red | Black | ...")
    season:          str = Field("", max_length=31,  description="Summer | Winter | Fall | Spring")
    year:            int = Field(0,                  description="Godina lansiranja")
    usage:           str = Field("", max_length=63,  description="Casual | Formal | Sports | ...")



class FashionProductCreate(FashionProductBase):
    """Input model for creating a new product."""
    product_id: int = Field(0, description="Originalni ID iz dataseta (0 za ručno unete)")
    image_url:  Optional[str] = Field(None, description="URL slike za enkodovanje (opciono)")



class FashionProductUpdate(BaseModel):
    """Partial update model — all fields are optional. Only provided fields will be updated."""
    product_name:    Optional[str] = Field(None, max_length=511)
    gender:          Optional[str] = None
    master_category: Optional[str] = None
    sub_category:    Optional[str] = None
    article_type:    Optional[str] = None
    base_colour:     Optional[str] = None
    season:          Optional[str] = None
    year:            Optional[int] = None
    usage:           Optional[str] = None
    image_url:       Optional[str] = Field(None, description="Novi URL slike za ponovno enkodovanje")



class FashionProduct(FashionProductBase):
    """Full entity representing a single document in the Milvus collection."""
    id:         int  = Field(..., description="Milvus auto-generisani primarni ključ")
    product_id: int  = Field(0,   description="Originalni ID iz dataseta")
    has_image:  bool = Field(False, description="True ako image_embedding nije nulti vektor")

    class Config:
        from_attributes = True

class SearchResult(BaseModel):
    """
    A single ANN search result — contains the similarity score and all scalar fields.
    Includes an optional fused_score for RRF (Reciprocal Rank Fusion).
    """
    id:              int
    score:           float = Field(..., description="Kosinusna sličnost ∈ [-1, 1]")
    product_name:    str   = ""
    gender:          str   = ""
    master_category: str   = ""
    sub_category:    str   = ""
    article_type:    str   = ""
    base_colour:     str   = ""
    season:          str   = ""
    year:            int   = 0
    usage:           str   = ""
    has_image:       bool  = False
    fused_score:     Optional[float] = Field(None, description="RRF fuziona ocena (samo za multimodalne upite)")


class ImageSearchRequest(BaseModel):
    """Request body for visual similarity search via image URL."""
    url:         str = Field(..., description="Javni URL slike koji se koristi kao upit")
    top_k:       int = Field(5,  ge=1, le=20)
    images_only: bool = Field(False, description="Vraćati samo proizvode koji imaju slike")


class MultimodalRequest(BaseModel):
    """Request body for multimodal fusion of text and image queries."""
    text_query:   str   = Field(..., description="Tekstualni upit za text_embedding pretragu")
    image_base64: str   = Field(..., description="Base64-enkodovana slika za image_embedding pretragu")
    text_weight:  float = Field(0.5, ge=0.0, le=1.0, description="Težina teksta (1 - text_weight = težina slike)")
    top_k:        int   = Field(5,   ge=1, le=100)
    filter_expr:  str   = Field("",  description="Opcioni Milvus filter izraz")


class TwoStageRequest(BaseModel):
    """Request body for two-stage search: visual recall → textual reranking."""
    image_base64: str            = Field(..., description="Base64 slika za fazu 1 (vizuelni recall)")
    text_rerank:  Optional[str]  = Field(None, description="Tekst za rerangiranje u fazi 2 (opciono)")
    recall_k:     int            = Field(50,   ge=10, le=200, description="Broj kandidata iz faze 1")
    final_k:      int            = Field(10,   ge=1,  le=100, description="Krajnji broj rezultata")
    filter_expr:  str            = Field("",   description="Filter za fazu 1")
