from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum

class StatusCli(Enum):
    OK = 1
    DEVENDO = 2
    CRÉDITO = 3

class Cliente(ABC):
    def __init__(self, Id: int):
        self.ID = Id
        self.DataContrato = datetime.now()
        self.Status = StatusCli.OK
        self.Invoices = []
        self.TotalDivida = 0.0

    