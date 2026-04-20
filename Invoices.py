from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum

class StatusInv(Enum):
    ABERTA = 1
    LIQUIDADA = 2
    ATRASADA = 3

class Invoice(ABC):

    def __init__(self, Id: int, Valor: float):
        self.Total = Valor
        self.ID = Id
        self.Status  = StatusInv.ABERTA
        self.DataCriacao = datetime.now() 
        self.Vencimento = datetime.now() + timedelta(days=30)

    @abstractmethod
    def CalcularJuros(self)-> float:
        pass

    @abstractmethod
    def CalcularImposto(self)-> float:
        pass

    def UpdateStatus(self, status: StatusInv):
        self.Status = status

    def ConsultarStatus(self) -> str: 
        return self.Status.name

    def ConsultarDivida(self) -> float:
        return self.Total + self.CalcularImposto() + self.CalcularJuros()

class InvoiceInternacional(Invoice):

    def CalcularJuros(self)-> float:
        dias_atrasados = (datetime.now() - self.Vencimento).days
        if dias_atrasados < 0:
            return 0
        else:
            return dias_atrasados * 0.01 * self.Total   

    def CalcularImposto(self)-> float:
        return self.Total * 0.1

class InvoiceNacional(Invoice):

    def CalcularJuros(self)-> float:
        dias_atrasados = (datetime.now() - self.Vencimento).days
        if dias_atrasados < 0:
            return 0
        else:
            return dias_atrasados * 0.005 * self.Total   

    def CalcularImposto(self)-> float:
        return self.Total * 0.18
