from __future__ import annotations

"""Entidades e estratégias relacionadas a pagamentos."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from Invoices import Invoice

if TYPE_CHECKING:
    from Clientes import Cliente
    from Controle import Sistema


class StrategyTaxa(ABC):
    """Estratégia para cálculo de taxa sobre o valor base de pagamento."""

    @abstractmethod
    def aplicar(self, valor_base: float) -> float:
        """Aplica a taxa e retorna o valor final esperado."""
        pass

class TaxaPix(StrategyTaxa):
    """Pagamento sem taxa adicional."""

    def aplicar(self, valor_base: float) -> float:
        """Retorna o próprio valor base."""
        return valor_base


class TaxaTransferencia(StrategyTaxa):
    """Pagamento com taxa de transferência."""

    def aplicar(self, valor_base: float) -> float:
        """Aplica 5% de taxa."""
        return valor_base * 1.05


class TaxaCredito(StrategyTaxa):
    """Pagamento com taxa de crédito."""

    def aplicar(self, valor_base: float) -> float:
        """Aplica 10% de taxa."""
        return valor_base * 1.10


class TaxaTransferenciaTerceiro(StrategyTaxa):
    """Pagamento com taxa para transferência realizada por terceiro."""

    def aplicar(self, valor_base: float) -> float:
        """Aplica 15% de taxa."""
        return valor_base * 1.15


class EstrategiaParcelamento(ABC):
    """Estratégia para aprovar ou rejeitar parcelamento."""

    @abstractmethod
    def aprovar(self, parcelas: int) -> int:
        """Retorna a quantidade de parcelas aprovada."""
        pass

class SemParcelamento(EstrategiaParcelamento):
    """Estratégia usada em meios de pagamento que não parcelam."""

    def aprovar(self, parcelas: int) -> int:
        """Valida que não haja parcelamento.

        Raises:
            ValueError: Se for solicitado parcelamento.
        """
        if parcelas not in (0, 1):
            raise ValueError("Este método de pagamento não permite parcelamento.")
        return 0


class ParcelamentoCredito(EstrategiaParcelamento):
    """Estratégia de parcelamento para pagamento no crédito."""

    def aprovar(self, parcelas: int) -> int:
        """Aprova parcelamento de 1 a 12 vezes.

        Raises:
            ValueError: Se a quantidade de parcelas for inválida.
        """
        if 1 <= parcelas <= 12:
            return parcelas
        raise ValueError("Parcelamento no crédito deve ser entre 1 e 12 parcelas.")


class Pagamento:
    """Representa um pagamento de um conjunto de invoices."""

    def __init__(self, id: int, valor: float, invoices: list[Invoice], cliente: Cliente, estrategia_taxa: StrategyTaxa, estrategia_parcelamento: EstrategiaParcelamento) -> None:
        """Inicializa um pagamento.

        Args:
            id: Identificador do pagamento.
            valor: Valor efetivamente pago.
            invoices: Invoices a serem liquidadas.
            cliente: Cliente titular do pagamento.
            estrategia_taxa: Estratégia de taxa do meio de pagamento.
            estrategia_parcelamento: Estratégia de parcelamento.
        """
        if not invoices:
            raise ValueError("É necessário informar ao menos uma invoice para pagamento.")

        self.id = id
        self.cliente = cliente
        self.invoices = invoices
        self.valor = valor
        self.parcelas = 0
        self.estrategia_taxa = estrategia_taxa
        self.estrategia_parcelamento = estrategia_parcelamento

    def accept(self, visitor: "RelatorioVisitor") -> str:
        """Permite gerar relatório via visitor."""
        return visitor.extrato(self)

    def aplicar_taxa_cliente_internacional(self, valor_base: float) -> float:
        """Aplica taxa extra de 3% para cliente internacional."""
        if self.cliente.tipo_cliente() == "internacional":
            return valor_base * 1.03
        return valor_base

    def calcular_valor_base(self) -> float:
        """Soma a dívida atual das invoices informadas."""
        return sum(invoice.consultar_divida() for invoice in self.invoices)

    def calcular_valor_esperado(self) -> float:
        """Calcula o valor esperado do pagamento considerando regras aplicáveis."""
        valor_base = self.calcular_valor_base()
        valor_base = self.aplicar_taxa_cliente_internacional(valor_base)
        return self.estrategia_taxa.aplicar(valor_base)

    def validar_pagamento(self) -> None:
        """Valida se o valor pago corresponde ao valor esperado.

        Raises:
            ValueError: Se o valor informado não corresponder ao esperado.
        """
        valor_esperado = self.calcular_valor_esperado()
        if abs(valor_esperado - self.valor) > 0.01:
            raise ValueError(
                f"Valor pago não corresponde às invoices indicadas. Esperado: {valor_esperado:.2f}"
            )

    def aprovar_parcelamento(self, parcelas: int) -> None:
        """Valida e registra o parcelamento aprovado."""
        self.parcelas = self.estrategia_parcelamento.aprovar(parcelas)

    def realizar_pagamento(self) -> None:
        """Valida o pagamento e liquida as invoices."""
        self.validar_pagamento()
        for invoice in self.invoices:
            invoice.liquidar()


class TransferenciaViaTerceiro:
    """Integração externa simulada para pagamentos por terceiro."""

    def __init__(self, id: int, valor: float, invoices: list[Invoice], cliente: Cliente, documento_pagador: str) -> None:
        """Inicializa o pagamento por terceiro.

        Args:
            id: Identificador do pagamento.
            valor: Valor pago.
            invoices: Invoices a serem liquidadas.
            cliente: Cliente titular.
            documento_pagador: Documento do terceiro pagador.
        """
        if not documento_pagador:
            raise ValueError("É necessário informar o documento do terceiro pagador.")

        self.id = id
        self.doc_pagador = documento_pagador
        self.cliente = cliente
        self.invoices = invoices
        self.valor = valor
        self.parcelas = 0

    def validar_cliente(self) -> None:
        """Valida se o cliente titular existe no sistema."""
        from Controle import Sistema

        sistema = Sistema.acessar_sistema()
        cliente_encontrado = sistema.consultar_cliente(self.cliente.id)
        if cliente_encontrado is None:
            raise ValueError("Não existe este cliente no sistema.")

    def aplicar_taxa_cliente_internacional(self, valor_base: float) -> float:
        """Aplica taxa extra para clientes internacionais."""
        if self.cliente.tipo_cliente() == "internacional":
            return valor_base * 1.03
        return valor_base

    def calcular_valor_esperado(self) -> float:
        """Calcula o valor esperado para transferência via terceiro."""
        valor_base = sum(invoice.consultar_divida() for invoice in self.invoices)
        valor_base = self.aplicar_taxa_cliente_internacional(valor_base)
        return valor_base * 1.15

    def validar_pagamento_terceiro(self) -> None:
        """Valida o pagamento realizado por terceiro."""
        self.validar_cliente()
        valor_esperado = self.calcular_valor_esperado()
        if abs(valor_esperado - self.valor) > 0.01:
            raise ValueError(f"Valor pago não corresponde às invoices indicadas. Esperado: {valor_esperado:.2f}")

    def realizar_pagamento_terceiro(self) -> None:
        """Valida e liquida as invoices do pagamento por terceiro."""
        self.validar_pagamento_terceiro()
        for invoice in self.invoices:
            invoice.liquidar()


class PagamentoAdapter(Pagamento):
    """Adapter para compatibilizar TransferenciaViaTerceiro com Pagamento."""

    def __init__(self, pagamento_externo: TransferenciaViaTerceiro) -> None:
        super().__init__(
            pagamento_externo.id,
            pagamento_externo.valor,
            pagamento_externo.invoices,
            pagamento_externo.cliente,
            TaxaTransferenciaTerceiro(),
            SemParcelamento(),
        )
        self._pagamento = pagamento_externo

    def validar_pagamento(self) -> None:
        """Delega a validação ao pagamento externo."""
        self._pagamento.validar_pagamento_terceiro()

    def realizar_pagamento(self) -> None:
        """Delega a liquidação ao pagamento externo."""
        self._pagamento.realizar_pagamento_terceiro()


class PagamentoFactory:
    """Factory responsável por instanciar o tipo adequado de pagamento."""

    @staticmethod
    def create( pagamento_type: str, id: int, valor: float, invoices: list[Invoice], cliente: Cliente, documento_pagador: str | None = None) -> Pagamento:
        """Cria um pagamento com base no tipo solicitado.

        Args:
            pagamento_type: Tipo do pagamento.
            id: Identificador do pagamento.
            valor: Valor pago.
            invoices: Invoices associadas.
            cliente: Cliente titular.
            documento_pagador: Documento do terceiro, quando necessário.

        Raises:
            ValueError: Se o tipo for inválido.
        """
        if pagamento_type == "PIX":
            return Pagamento(id, valor, invoices, cliente, TaxaPix(), SemParcelamento())
        if pagamento_type == "TRANSFERENCIA":
            return Pagamento(id, valor, invoices, cliente, TaxaTransferencia(), SemParcelamento())
        if pagamento_type == "CREDITO":
            return Pagamento(id, valor, invoices, cliente, TaxaCredito(), ParcelamentoCredito())
        if pagamento_type == "TRANSFERENCIA_TERCEIRO":
            pagamento_externo = TransferenciaViaTerceiro(
                id, valor, invoices, cliente, documento_pagador or ""
            )
            return PagamentoAdapter(pagamento_externo)
        raise ValueError("Tipo inválido de pagamento.")


class RelatorioVisitor:
    """Visitor simples para gerar extrato textual de pagamento."""

    def extrato(self, pagamento: Pagamento) -> str:
        """Gera um extrato textual do pagamento informado."""
        ids_invoices = [invoice.id for invoice in pagamento.invoices]
        return (
            f"ID: {pagamento.id}\n"
            f"Valor: {pagamento.valor:.2f}\n"
            f"Cliente: {pagamento.cliente.id}\n"
            f"Parcelas: {pagamento.parcelas}\n"
            f"Invoices: {ids_invoices}"
        )
