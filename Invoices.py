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

    def calcular_imposto(self) -> float:
        if self.credito or self.status == StatusInv.LIQUIDADA:
            return 0.0
        return self.valor * self.taxa_imposto()

    def calcular_juros(self) -> float:
        self.atualizar_status()

        if self.credito or self.status == StatusInv.LIQUIDADA:
            return 0.0

        dias_atrasados = (datetime.now() - self.vencimento).days
        if dias_atrasados <= 0:
            return 0.0

        return self.valor * self.taxa_juros_diaria() * dias_atrasados

    def consultar_divida(self) -> float:
        self.atualizar_status()

        if self.status == StatusInv.LIQUIDADA:
            return 0.0

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
            raise ValueError("Tipo inválido de invoice.")
        return classe(id, valor, credito)


class DecoradorInvoice(Invoice, ABC):
    def __init__(self, invoice: Invoice):
        self._invoice = invoice

    @property
    def taxa_juros_diaria(self) -> float:
        return self._invoice.taxa_juros_diaria

    @property
    def taxa_imposto(self) -> float:
        return self._invoice.taxa_imposto

    @property
    def id(self) -> int:
        return self._invoice.id

    @property
    def valor(self) -> float:
        return self._invoice.valor

    @property
    def credito(self) -> bool:
        return self._invoice.credito

    @property
    def status(self) -> StatusInv:
        return self._invoice.status

    @property
    def data_criacao(self):
        return self._invoice.data_criacao

    @property
    def vencimento(self):
        return self._invoice.vencimento

    def atualizar_status(self):
        self._invoice.atualizar_status()

    def liquidar(self):
        self._invoice.liquidar()

    def consultar_status(self) -> str:
        return self._invoice.consultar_status()

    @abstractmethod
    def consultar_divida(self) -> float:
        pass


class AplicarMulta(DecoradorInvoice):
    def consultar_divida(self) -> float:
        divida_base = self._invoice.consultar_divida()

        if self._invoice.credito or self._invoice.status == StatusInv.LIQUIDADA:
            return divida_base

        return divida_base + (self._invoice.valor * 0.2)

#Decorador
class AplicarDesconto(DecoradorInvoice):
    def consultar_divida(self) -> float:
        divida_base = self._invoice.consultar_divida()

        if self._invoice.credito or self._invoice.status == StatusInv.LIQUIDADA:
            return divida_base

        return divida_base - (self._invoice.valor * 0.2)