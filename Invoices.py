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

    @property
    @abstractmethod
    def taxa_juros_diaria(self) -> float:
        pass

    @property
    @abstractmethod
    def taxa_imposto(self) -> float:
        pass

    def calcular_juros(self) -> float:
        if self.status == StatusInv.LIQUIDADA or self.credito:
            return 0.0
        dias_atrasados = (datetime.now() - self.vencimento).days
        if dias_atrasados <= 0:
            return 0.0
        return dias_atrasados * self.taxa_juros_diaria * self.valor

    def calcular_imposto(self) -> float:
        if self.credito:
            return 0.0
        return self.valor * self.taxa_imposto

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
    @property
    def taxa_juros_diaria(self) -> float:
        return 0.01

    @property
    def taxa_imposto(self) -> float:
        return 0.10


class InvoiceNacional(Invoice):
    @property
    def taxa_juros_diaria(self) -> float:
        return 0.005

    @property
    def taxa_imposto(self) -> float:
        return 0.18


class InvoiceFactory:
    _types = {
        "nacional": InvoiceNacional,
        "internacional": InvoiceInternacional,
    }

    @staticmethod
    def create(invoice_type: str, id: int, valor: float, credito: bool) -> Invoice:
        classe = InvoiceFactory._types.get(invoice_type)
        if classe is None:
            raise ValueError("Tipo inválido de invoice")
        return classe(id, valor, credito)