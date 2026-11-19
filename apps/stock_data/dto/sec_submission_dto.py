from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(kw_only=True)
class SecDTO(ABC):
    ticker: str
    cik: str
    filing_date: str
    filepath: str | None = None
    llm_response: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @abstractmethod
    def create_filepath(self) -> str:
        """This method must be implemented by all subclasses."""
        pass


@dataclass(kw_only=True)
class SecSubmissionDTO(SecDTO):
    """DTO for SEC submission data."""

    form_type: str
    accession_number: str
    acceptance_date_time: str
    primary_document: str
    document_endpoint: str = ""

    def create_filepath(self):
        return f"{self.ticker}_{self.form_type}_{self.cik}_{self.filing_date}.htm"

    def __post_init__(self):
        acc_no = "".join(c for c in self.accession_number if c.isdigit())
        self.document_endpoint = f"/Archives/edgar/data/{int(self.cik)}/{acc_no}/{self.primary_document}"
