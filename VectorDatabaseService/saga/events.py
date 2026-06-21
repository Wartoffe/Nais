"""
Pydantic modeli za koreografisanu SAGA -- moraju strukturno odgovarati
Java klasama iz rs.ac.uns.acs.nais.TimeseriesDatabaseService.saga.choreography.event
paketa (TimeseriesDatabaseService), jer oba servisa razmenjuju iste JSON poruke
preko RabbitMQ-a (saga.choreography.exchange).

NAPOMENA o vremenu:
Java strana koristi java.time.LocalDateTime, koji Jackson (preko JavaTimeModule,
automatski ukljucenog u Spring Boot 3 / spring-boot-starter-web) serijalizuje kao
ISO-8601 string bez vremenske zone, npr. "2026-06-21T14:30:00.123456".
Pydantic-ov `datetime` to parsira nativno, pa nije potrebna posebna konverzija.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

# Status koji TimeseriesDatabaseService koristi kao "prethodni" kada za datu
# narudzbinu/predlog jos ne postoji nijedan upisan event. Mora biti identicno
# stringu NEMA_PRETHODNOG_STATUSA iz SagaChoreographyService.java.
NEMA_PRETHODNOG_STATUSA = "NONE"


class KnjigaDTO(BaseModel):
    """
    Mirror Java klase dto.KnjigaDTO -- jedna knjiga iz liste knjiga koja stize
    unutar ChangeOfOrderStatusCreatedEvent-a. Polja su 1:1 sa model.book.BookCreate,
    sto omogucava direktno mapiranje u insert zapis bez rucnog modifikovanja.
    """

    model_config = ConfigDict(populate_by_name=True)

    goodreads_id: int = Field(..., ge=1, validation_alias=AliasChoices("goodreads_id", "goodreadsId"))
    isbn: str
    title: str
    author: str
    description: str
    language: str = "en"
    publisher: str = ""
    pages: int = 0
    cover_img: str | None = Field(default=None, alias="coverImg")
    has_image: bool = False


class ChangeOfOrderStatusCreatedEvent(BaseModel):
    """Mirror Java ChangeOfOrderStatusCreatedEvent -- okidac koraka 2 (insert u Milvus)."""

    model_config = ConfigDict(populate_by_name=True)

    saga_id: str = Field(..., alias="sagaId")
    narudzbinaid: str
    prethodni_status: str = Field(..., alias="prethodniStatus")
    knjige: list[KnjigaDTO] = Field(default_factory=list)
    timestamp: datetime


class BookCreatedEvent(BaseModel):
    """Mirror Java BookCreatedEvent -- objavljuje se kada SVE knjige uspesno upisane u Milvus."""

    model_config = ConfigDict(populate_by_name=True)

    saga_id: str = Field(..., alias="sagaId")
    narudzbinaid: str
    timestamp: datetime


class BookCreationFailedEvent(BaseModel):
    """Mirror Java BookCreationFailedEvent -- objavljuje se kada upis u Milvus ne uspe."""

    model_config = ConfigDict(populate_by_name=True)

    saga_id: str = Field(..., alias="sagaId")
    narudzbinaid: str
    prethodni_status: str = Field(..., alias="prethodniStatus")
    razlog: str
    timestamp: datetime


class OrderStatusCompensatedEvent(BaseModel):
    """Mirror Java OrderStatusCompensatedEvent -- audit/notifikacija nakon kompenzacije (samo primamo, ne objavljujemo)."""

    model_config = ConfigDict(populate_by_name=True)

    saga_id: str = Field(..., alias="sagaId")
    narudzbinaid: str
    vracen_na_status: str = Field(..., alias="vracenNaStatus")
    timestamp: datetime