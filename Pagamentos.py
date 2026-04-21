from abc import ABC, abstractmethod
from Invoices import Invoice
from Clientes import Cliente
from Controle import Sistema


class Pagamento(ABC):
    def __init__(self, id: int, valor: float, invoices: list[Invoice], pagador: Cliente):
        self.id = id
        self.cliente = pagador
        self.invoices = invoices
        self.valor = valor
        self.parcelas = 0

    def cliente_internacional(self):
        if self.cliente.tipo_cliente() == "internacional":
            self.valor = self.valor * 0.03

    def validar_pagamento(self):
        self.cliente_internacional()
        self.taxas()
        valor_final = sum(invoice.consultar_divida() for invoice in self.invoices)
        if valor_final != self.valor:
            raise ValueError("Valor pago não corresponde às invoices indicadas.")

    def realizar_pagamento(self):
        self.validar_pagamento()
        for invoice in self.invoices:
            invoice.liquidar()

    @abstractmethod
    def taxas(self):
        pass

    @abstractmethod
    def aprovar_parcelamento(self, parcelas: int):
        pass


class PagamentoPix(Pagamento):
    def taxas(self):
        pass

    def aprovar_parcelamento(self, parcelas: int):
        self.parcelas = 0


class PagamentoTransferencia(Pagamento):
    def taxas(self):
        self.valor = self.valor * 1.05

    def aprovar_parcelamento(self, parcelas: int):
        self.parcelas = 0


class PagamentoCredito(Pagamento):
    def taxas(self):
        self.valor = self.valor * 1.1

    def aprovar_parcelamento(self, parcelas: int):
        if parcelas < 12:
            self.parcelas = parcelas
        else:
            self.parcelas = 0


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

    def validar_pagamento_terceiro(self):
        self.validar_cliente()
        self.taxas()
        valor_final = sum(invoice.consultar_divida() for invoice in self.invoices)
        if valor_final != self.valor:
            raise ValueError("Valor pago não corresponde às invoices indicadas.")

    def realizar_pagamento_terceiro(self):
        self.validar_pagamento_terceiro()
        for invoice in self.invoices:
            invoice.liquidar()

    def taxas(self):
        self.valor = self.valor * 1.15

#Adptador
class PagamentoAdapter(Pagamento):
    def __init__(self, pagamento_externo: TransferenciaViaTerceiro):
        super().__init__(
            pagamento_externo.id,
            pagamento_externo.valor,
            pagamento_externo.invoices,
            pagamento_externo.cliente
        )
        self._pagamento = pagamento_externo

    def taxas(self):
        self._pagamento.taxas()
        self.valor = self._pagamento.valor

    def aprovar_parcelamento(self, parcelas: int):
        self.parcelas = 0

    def validar_pagamento(self):
        self._pagamento.validar_pagamento_terceiro()
        self.valor = self._pagamento.valor

    def realizar_pagamento(self):
        self._pagamento.realizar_pagamento_terceiro()

class PagamentoFactory:
    _types = {
        "PIX": PagamentoPix,
        "TRANSFERENCIA": PagamentoTransferencia,
        "TRANSFERENCIA_TERCEIRO": PagamentoAdapter,
        "CREDITO": PagamentoCredito
    }

    @staticmethod
    def create(pagamento_type: str, id: int, valor: float, invoices: list[Invoice], cliente: Cliente, pagador = 0) -> Pagamento:
        classe = PagamentoFactory._types.get(pagamento_type)
        if classe is None:
            raise ValueError("Tipo inválido de pagamento")
        if pagamento_type == "TRANSFERENCIA_TERCEIRO":
            pagamento_externo = TransferenciaViaTerceiro(id, valor, invoices, cliente, pagador)
            return classe(pagamento_externo)
        else:
            return classe(id, valor, invoices, cliente)