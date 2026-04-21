from abc import ABC, abstractmethod
from Invoices import Invoice
from Clientes import Cliente
from Controle import Sistema


class StrategyTaxa(ABC):
    @abstractmethod
    def aplicar(self, valor_base: float) -> float:
        pass

class TaxaPix(StrategyTaxa):
    def aplicar(self, valor_base: float) -> float:
        return valor_base

class TaxaTransferencia(StrategyTaxa):
    def aplicar(self, valor_base: float) -> float:
        return valor_base * 1.05

class TaxaCredito(StrategyTaxa):
    def aplicar(self, valor_base: float) -> float:
        return valor_base * 1.10

class TaxaTransferenciaTerceiro(StrategyTaxa):
    def aplicar(self, valor_base: float) -> float:
        return valor_base * 1.15


class EstrategiaParcelamento(ABC):
    @abstractmethod
    def aprovar(self, parcelas: int) -> int:
        pass

class SemParcelamento(EstrategiaParcelamento):
    def aprovar(self, parcelas: int) -> int:
        return 0

class ParcelamentoCredito(EstrategiaParcelamento):
    def aprovar(self, parcelas: int) -> int:
        if 1 <= parcelas <= 12:
            return parcelas
        return 0



class Pagamento:
    def __init__(self,id: int,valor: float, invoices: list[Invoice], pagador: Cliente, estrategia_taxa: StrategyTaxa, estrategia_parcelamento: EstrategiaParcelamento):
        self.id = id
        self.cliente = pagador
        self.invoices = invoices
        self.valor = valor
        self.parcelas = 0
        self.estrategia_taxa = estrategia_taxa
        self.estrategia_parcelamento = estrategia_parcelamento

    def accept(self, visitor):
        return visitor.extrato(self)

    def aplicar_taxa_cliente_internacional(self, valor_base: float) -> float:
        if self.cliente.tipo_cliente() == "internacional":
            return valor_base * 1.03
        return valor_base

    def calcular_valor_esperado(self) -> float:
        valor_base = sum(invoice.consultar_divida() for invoice in self.invoices)
        valor_base = self.aplicar_taxa_cliente_internacional(valor_base)
        return self.estrategia_taxa.aplicar(valor_base)

    def validar_pagamento(self):
        valor_esperado = self.calcular_valor_esperado()
        if abs(valor_esperado - self.valor) > 0.01:
            raise ValueError("Valor pago não corresponde às invoices indicadas.")

    def aprovar_parcelamento(self, parcelas: int):
        self.parcelas = self.estrategia_parcelamento.aprovar(parcelas)

    def realizar_pagamento(self):
        self.validar_pagamento()
        for invoice in self.invoices:
            invoice.liquidar()

class TransferenciaViaTerceiro:
    def __init__(self, id: int, valor: float, invoices: list[Invoice], cliente: Cliente, pagador: int):
        self.id = id
        self.doc_pagador = pagador
        self.cliente = cliente
        self.invoices = invoices
        self.valor = valor
        self.parcelas = 0

    def validar_cliente(self):
        sistema = Sistema.acessar_sistema()
        cliente_encontrado = sistema.consultar_cliente(self.cliente.id)
        if cliente_encontrado is None:
            raise ValueError("Não existe este cliente.")

    def aplicar_taxa_cliente_internacional(self, valor_base: float) -> float:
        if self.cliente.tipo_cliente() == "internacional":
            return valor_base * 1.03
        return valor_base

    def calcular_valor_esperado(self) -> float:
        valor_base = sum(invoice.consultar_divida() for invoice in self.invoices)
        valor_base = self.aplicar_taxa_cliente_internacional(valor_base)
        return valor_base * 1.15

    def validar_pagamento_terceiro(self):
        self.validar_cliente()
        valor_esperado = self.calcular_valor_esperado()
        if abs(valor_esperado - self.valor) > 0.01:
            raise ValueError("Valor pago não corresponde às invoices indicadas.")

    def realizar_pagamento_terceiro(self):
        self.validar_pagamento_terceiro()
        for invoice in self.invoices:
            invoice.liquidar()

class PagamentoAdapter(Pagamento):
    def __init__(self, pagamento_externo: TransferenciaViaTerceiro):
        super().__init__(
            pagamento_externo.id,
            pagamento_externo.valor,
            pagamento_externo.invoices,
            pagamento_externo.cliente,
            TaxaTransferenciaTerceiro(),
            SemParcelamento()
        )
        self._pagamento = pagamento_externo

    def validar_pagamento(self):
        self._pagamento.validar_pagamento_terceiro()

    def realizar_pagamento(self):
        self._pagamento.realizar_pagamento_terceiro()

class PagamentoFactory:
    @staticmethod
    def create( pagamento_type: str, id: int, valor: float, invoices: list[Invoice], cliente: Cliente, pagador: int = 0) -> Pagamento:

        if pagamento_type == "PIX":
            return Pagamento(id, valor, invoices, cliente, TaxaPix(), SemParcelamento())

        if pagamento_type == "TRANSFERENCIA":
            return Pagamento(id,valor, invoices, cliente, TaxaTransferencia(), SemParcelamento())

        if pagamento_type == "CREDITO":
            return Pagamento(id, valor, invoices, cliente, TaxaCredito(), ParcelamentoCredito())

        if pagamento_type == "TRANSFERENCIA_TERCEIRO":
            pagamento_externo = TransferenciaViaTerceiro(id, valor, invoices, cliente, pagador)
            return PagamentoAdapter(pagamento_externo)

        raise ValueError("Tipo inválido de pagamento")


class RelatorioVisitor:
    def extrato(self, pagamento) -> str:
        ids_invoices = [invoice.id for invoice in pagamento.invoices]
        return (
            f"ID: {pagamento.id}\n"
            f"Valor: {pagamento.valor:.2f}\n"
            f"Cliente: {pagamento.cliente.id}\n"
            f"Parcelas: {pagamento.parcelas}\n"
            f"Invoices: {ids_invoices}"
        )