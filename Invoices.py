from __future__ import annotations

"""Entidades e comportamentos relacionados a invoices.

Este módulo contém a abstração base de uma invoice, suas especializações por tipo
cliente e decorators opcionais para ajustar a dívida calculada.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum


class StatusInvoice(Enum):
    """Estados possíveis de uma invoice."""

    ABERTA = 1
    LIQUIDADA = 2
    ATRASADA = 3
    EXPIRADA = 4


class Invoice(ABC):
    """Representa uma cobrança ou crédito associado a um cliente.

    Attributes:
        id: Identificador único da invoice.
        valor: Valor original da invoice.
        credito: Indica se a invoice representa um crédito (valor negativo).
        status: Situação atual da invoice.
        data_criacao: Data e hora de criação.
        vencimento: Data e hora de vencimento.
    """

    def __init__(self, id: int, valor: float, credito: bool) -> None:
        """Inicializa uma invoice válida.

        Args:
            id: Identificador da invoice.
            valor: Valor monetário da invoice.
            credito: Define se a invoice é de crédito.

        Raises:
            ValueError: Se o sinal do valor não for compatível com o tipo.
        """
        if not credito and valor <= 0:
            raise ValueError("Invoices de débito devem ter valor maior que zero.")
        if credito and valor >= 0:
            raise ValueError("Invoices de crédito devem ter valor menor que zero.")

        self.id = id
        self.valor = valor
        self.credito = credito
        self.status = StatusInvoice.ABERTA
        self.data_criacao = datetime.now()
        self.vencimento = self.data_criacao + timedelta(days=30)

    @abstractmethod
    def taxa_juros_diaria(self) -> float:
        """Retorna a taxa de juros diária aplicada a invoices em atraso."""
        pass

    @abstractmethod
    def taxa_imposto(self) -> float:
        """Retorna a taxa de imposto aplicada a invoices de débito."""
        pass
    
    def atualizar_status(self) -> None:
        """Atualiza o status da invoice de acordo com vencimento e liquidação."""
        if self.status == StatusInvoice.LIQUIDADA:
            return

        if datetime.now() > self.vencimento:
            self.status = StatusInvoice.EXPIRADA if self.credito else StatusInvoice.ATRASADA
        else:
            self.status = StatusInvoice.ABERTA

    def liquidar(self) -> None:
        """Liquida a invoice.

        Raises:
            ValueError: Se a invoice já estiver liquidada.
        """
        if self.status == StatusInvoice.LIQUIDADA:
            raise ValueError("A invoice já está liquidada.")
        self.status = StatusInvoice.LIQUIDADA

    def consultar_status(self) -> str:
        """Retorna o status atualizado da invoice."""
        self.atualizar_status()
        return self.status.name

    def calcular_imposto(self) -> float:
        """Calcula o imposto devido.

        Returns:
            O valor do imposto. Créditos e invoices liquidadas não geram imposto.
        """
        if self.credito or self.status == StatusInvoice.LIQUIDADA:
            return 0.0
        return self.valor * self.taxa_imposto()

    def calcular_juros(self) -> float:
        """Calcula juros por atraso.

        Returns:
            O valor de juros acumulado. Créditos e invoices liquidadas não geram juros.
        """
        self.atualizar_status()

        if self.credito or self.status == StatusInvoice.LIQUIDADA:
            return 0.0

        dias_atrasados = (datetime.now() - self.vencimento).days
        if dias_atrasados <= 0:
            return 0.0

        return self.valor * self.taxa_juros_diaria() * dias_atrasados

    def consultar_divida(self) -> float:
        """Retorna o impacto financeiro atual da invoice.

        Regras:
            - invoice liquidada retorna 0;
            - crédito expirado não pode mais ser utilizado, então retorna 0;
            - crédito válido retorna valor negativo;
            - débito retorna valor + imposto + juros.
        """
        self.atualizar_status()

        if self.status == StatusInvoice.LIQUIDADA:
            return 0.0
        if self.credito:
            return 0.0 if self.status == StatusInvoice.EXPIRADA else self.valor
        return self.valor + self.calcular_imposto() + self.calcular_juros()


class InvoiceInternacional(Invoice):
    """Invoice aplicada a clientes internacionais."""

    def taxa_juros_diaria(self) -> float:
        """Retorna a taxa diária de juros do cliente internacional."""
        return 0.01

    def taxa_imposto(self) -> float:
        """Retorna a taxa de imposto do cliente internacional."""
        return 0.10


class InvoiceNacional(Invoice):
    """Invoice aplicada a clientes nacionais."""

    def taxa_juros_diaria(self) -> float:
        """Retorna a taxa diária de juros do cliente nacional."""
        return 0.005

    def taxa_imposto(self) -> float:
        """Retorna a taxa de imposto do cliente nacional."""
        return 0.18


class InvoiceFactory:
    """Factory responsável por criar invoices de acordo com o tipo do cliente."""

    _types = {
        "nacional": InvoiceNacional,
        "internacional": InvoiceInternacional,
    }

    @staticmethod
    def create(invoice_type: str, id: int, valor: float, credito: bool) -> Invoice:
        """Cria uma invoice do tipo solicitado.

        Args:
            invoice_type: Tipo de invoice, como "nacional" ou "internacional".
            id: Identificador da invoice.
            valor: Valor da invoice.
            credito: Indica se é crédito.

        Raises:
            ValueError: Se o tipo for inválido.
        """
        classe = InvoiceFactory._types.get(invoice_type)
        if classe is None:
            raise ValueError("Tipo inválido de invoice.")
        return classe(id, valor, credito)


class DecoradorInvoice(Invoice, ABC):
    """Classe base para decorators de invoice.

    O decorator delega o comportamento à invoice encapsulada e altera somente o
    cálculo final da dívida quando necessário.
    """

    def __init__(self, invoice: Invoice) -> None:
        self._invoice = invoice

    def taxa_juros_diaria(self) -> float:
        """Delega a taxa de juros diária para a invoice encapsulada."""
        return self._invoice.taxa_juros_diaria()

    def taxa_imposto(self) -> float:
        """Delega a taxa de imposto para a invoice encapsulada."""
        return self._invoice.taxa_imposto()

    @property
    def id(self) -> int:
        """Retorna o id da invoice encapsulada."""
        return self._invoice.id

    @property
    def valor(self) -> float:
        """Retorna o valor original da invoice encapsulada."""
        return self._invoice.valor

    @property
    def credito(self) -> bool:
        """Retorna se a invoice encapsulada é de crédito."""
        return self._invoice.credito

    @property
    def status(self) -> StatusInvoice:
        """Retorna o status da invoice encapsulada."""
        return self._invoice.status

    @property
    def data_criacao(self) -> datetime:
        """Retorna a data de criação da invoice encapsulada."""
        return self._invoice.data_criacao

    @property
    def vencimento(self) -> datetime:
        """Retorna o vencimento da invoice encapsulada."""
        return self._invoice.vencimento

    def atualizar_status(self) -> None:
        """Atualiza o status da invoice encapsulada."""
        self._invoice.atualizar_status()

    def liquidar(self) -> None:
        """Liquida a invoice encapsulada."""
        self._invoice.liquidar()

    def consultar_status(self) -> str:
        """Consulta o status da invoice encapsulada."""
        return self._invoice.consultar_status()

    def calcular_imposto(self) -> float:
        """Calcula imposto da invoice encapsulada."""
        return self._invoice.calcular_imposto()

    def calcular_juros(self) -> float:
        """Calcula juros da invoice encapsulada."""
        return self._invoice.calcular_juros()

    @abstractmethod
    def consultar_divida(self) -> float:
        """Retorna a dívida final após a decoração aplicada."""


class AplicarMulta(DecoradorInvoice):
    """Decorator que adiciona multa fixa percentual à dívida."""

    def consultar_divida(self) -> float:
        """Retorna a dívida com multa adicional de 20% sobre o valor base."""
        divida_base = self._invoice.consultar_divida()
        if self._invoice.credito or self._invoice.status == StatusInvoice.LIQUIDADA:
            return divida_base
        return divida_base + (self._invoice.valor * 0.20)

class AplicarDesconto(DecoradorInvoice):
    """Decorator que reduz a dívida em percentual fixo."""

    def consultar_divida(self) -> float:
        """Retorna a dívida com desconto de 20% sobre o valor base."""
        divida_base = self._invoice.consultar_divida()
        if self._invoice.credito or self._invoice.status == StatusInvoice.LIQUIDADA:
            return divida_base
        return divida_base - (self._invoice.valor * 0.20)