from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum

class StatusInv(Enum):
    ABERTA = 1
    LIQUIDADA = 2
    ATRASADA = 3
    EXPIRADA = 4

class Invoice(ABC):
    def __init__(self, id: int, valor: float, credito: bool):
        if id <= 0:
            raise ValueError("O id deve ser maior que zero.")

        if not credito and valor <= 0:
            raise ValueError("Invoices de débito devem ter valor maior que zero.")

        if credito and valor >= 0:
            raise ValueError("Invoices de crédito devem ter valor menor que zero.")

        self.id = id
        self.valor = valor
        self.credito = credito
        self.status = StatusInv.ABERTA
        self.data_criacao = datetime.now()
        self.vencimento = self.data_criacao + timedelta(days=30)

    @abstractmethod
    def calcular_juros(self) -> float:
        pass

    @abstractmethod
    def calcular_imposto(self) -> float:
        pass

    def atualizar_status(self):
        if self.status == StatusInv.LIQUIDADA:
            return

        if datetime.now() > self.vencimento:
            if self.credito:
                self.status = StatusInv.EXPIRADA
            else:
                self.status = StatusInv.ATRASADA
        else:
            self.status = StatusInv.ABERTA

    def liquidar(self):
        if self.status == StatusInv.LIQUIDADA:
            raise ValueError("A invoice já está liquidada.")

        self.status = StatusInv.LIQUIDADA

    def consultar_status(self) -> str:
        self.atualizar_status()
        return self.status.name

    def consultar_divida(self) -> float:
        self.atualizar_status()

        if self.credito:
            return self.valor

        return self.valor + self.calcular_imposto() + self.calcular_juros()


class InvoiceInternacional(Invoice):
    def calcular_juros(self) -> float:
        if self.status == StatusInv.LIQUIDADA or self.credito:
            return 0.0

        dias_atrasados = (datetime.now() - self.vencimento).days
        if dias_atrasados <= 0:
            return 0.0

        return dias_atrasados * 0.01 * self.valor

    def calcular_imposto(self) -> float:
        if self.status == StatusInv.LIQUIDADA or self.credito:
            return 0.0

        return self.valor * 0.10


class InvoiceNacional(Invoice):
    def calcular_juros(self) -> float:
        if self.status == StatusInv.LIQUIDADA or self.credito:
            return 0.0

        dias_atrasados = (datetime.now() - self.vencimento).days
        if dias_atrasados <= 0:
            return 0.0

        return dias_atrasados * 0.005 * self.valor

    def calcular_imposto(self) -> float:
        if self.status == StatusInv.LIQUIDADA or self.credito:
            return 0.0

        return self.valor * 0.18