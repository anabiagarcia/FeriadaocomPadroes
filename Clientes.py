from __future__ import annotations

"""Módulo com entidades e regras relacionadas a clientes."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from Invoices import Invoice, InvoiceFactory
from Pagamentos import Pagamento, PagamentoFactory


class MetodoPagamento(Enum):
    """Métodos de pagamento suportados pelo sistema."""

    PIX = 1
    TRANSFERENCIA = 2
    TRANSFERENCIA_TERCEIRO = 3
    CREDITO = 4


class StatusCliente(Enum):
    """Situações possíveis de um cliente."""

    OK = 1
    DEVENDO = 2
    CREDITO = 3

class GeradorIdPagamento:
    """Singleton simples para geração sequencial de ids de pagamento."""

    _instance = None

    def __init__(self) -> None:
        if GeradorIdPagamento._instance is not None:
            raise Exception("Use get_instance() ao invés de instanciar diretamente.")
        self._contador = 0

    @classmethod
    def get_instance(cls) -> "GeradorIdPagamento":
        """Retorna a instância única do gerador de ids de pagamento."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def proximo_id(self) -> int:
        """Retorna o próximo id disponível."""
        self._contador += 1
        return self._contador


class GeradorIdInvoice:
    """Singleton simples para geração sequencial de ids de invoice."""

    _instance = None

    def __init__(self) -> None:
        if GeradorIdInvoice._instance is not None:
            raise Exception("Use get_instance() ao invés de instanciar diretamente.")
        self._contador = 0

    @classmethod
    def get_instance(cls) -> "GeradorIdInvoice":
        """Retorna a instância única do gerador de ids de invoice."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def proximo_id(self) -> int:
        """Retorna o próximo id disponível."""
        self._contador += 1
        return self._contador


class Cliente(ABC):
    """Classe base de cliente."""

    def __init__(self, id: int, nome: str, documento: str) -> None:
        """Inicializa um cliente.

        Args:
            id: Identificador único do cliente.
            nome: Nome do cliente.
            documento: Documento do cliente.
        """
        self.id = id
        self.data_contrato = datetime.now()
        self.status = StatusCliente.OK
        self.invoices: list[Invoice] = []
        self.nome = nome
        self.documento = documento
        self._observers: list[Any] = []
        self.bloqueado = False

    def add_observer(self, observer: Any) -> None:
        """Adiciona um observer ao cliente."""
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: Any) -> None:
        """Remove um observer do cliente."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, evento: str, dado: Any) -> None:
        """Notifica todos os observers cadastrados."""
        for observer in self._observers:
            observer.update(evento, dado)

    @abstractmethod
    def tipo_cliente(self) -> str:
        """Retorna o tipo do cliente."""
        pass

    def bloquear_cliente(self) -> None:
        """Bloqueia novas compras do cliente."""
        self.bloqueado = True

    def desbloquear_cliente(self) -> None:
        """Desbloqueia novas compras do cliente."""
        self.bloqueado = False

    def compra(self, valor: float) -> Invoice:
        """Cria uma nova invoice para o cliente.

        Args:
            valor: Valor da compra. Negativo indica crédito.

        Raises:
            ValueError: Se o valor for zero.
        """
        if valor == 0:
            raise ValueError("O valor deve ser diferente de zero.")

        inv_id = GeradorIdInvoice.get_instance().proximo_id()
        credito = valor < 0
        invoice = InvoiceFactory.create(self.tipo_cliente(), inv_id, valor, credito)
        self.invoices.append(invoice)
        self.alterar_status()
        self.notify("invoice_criada", invoice)
        return invoice

    @abstractmethod
    def pagar(self, metodo: MetodoPagamento, valor: float, invoices: list[Invoice], documento_pagador: str | None = None, parcelas: int = 0) -> Pagamento:
        """Cria e realiza um pagamento."""
        pass

    def listar_invoices(self) -> list[int]:
        """Lista ids das invoices do cliente."""
        return [invoice.id for invoice in self.invoices]

    def divida(self) -> float:
        """Retorna o saldo consolidado do cliente."""
        return sum(invoice.consultar_divida() for invoice in self.invoices)

    def alterar_status(self) -> None:
        """Atualiza o status do cliente com base em sua dívida."""
        divida = self.divida()
        if divida > 0:
            self.status = StatusCliente.DEVENDO
        elif divida < 0:
            self.status = StatusCliente.CREDITO
        else:
            self.status = StatusCliente.OK

    def verificar_status(self) -> str:
        """Retorna o nome do status atualizado do cliente."""
        self.alterar_status()
        return self.status.name

    def calcular_valor_pagamento(self, metodo: MetodoPagamento, invoices: list[Invoice], documento_pagador: str | None = None) -> float:
        """Calcula o valor esperado para um pagamento antes de realizá-lo."""
        pagamento = PagamentoFactory.create(metodo.name, id=0, valor=0.0, invoices=invoices, cliente=self, documento_pagador=documento_pagador,)
        return pagamento.calcular_valor_esperado()


class ClienteInternacional(Cliente):
    """Cliente com regras de cobrança internacional."""

    def tipo_cliente(self) -> str:
        """Retorna o tipo do cliente."""
        return "internacional"

    def pagar(self, metodo: MetodoPagamento, valor: float, invoices: list[Invoice], documento_pagador: int | None = None, parcelas: int = 0) -> Pagamento:
        """Realiza pagamento respeitando restrições do cliente internacional."""
        if metodo == MetodoPagamento.PIX:
            raise ValueError("Cliente internacional não pode pagar com PIX.")

        pgt_id = GeradorIdPagamento.get_instance().proximo_id()
        pagamento = PagamentoFactory.create(metodo.name, pgt_id, valor, invoices, self, documento_pagador)
        pagamento.aprovar_parcelamento(parcelas)
        pagamento.realizar_pagamento()

        from Controle import Sistema

        self.notify("pagamento_criado", pagamento)
        self.alterar_status()
        return pagamento


class ClienteNacional(Cliente):
    """Cliente com regras de cobrança nacional."""

    def tipo_cliente(self) -> str:
        """Retorna o tipo do cliente."""
        return "nacional"

    def pagar(self, metodo: MetodoPagamento, valor: float, invoices: list[Invoice], documento_pagador: str | None = None, parcelas: int = 0) -> Pagamento:
        """Realiza pagamento de um cliente nacional."""
        pgt_id = GeradorIdPagamento.get_instance().proximo_id()
        pagamento = PagamentoFactory.create(metodo.name, pgt_id, valor, invoices, self, documento_pagador)
        pagamento.aprovar_parcelamento(parcelas)
        pagamento.realizar_pagamento()

        from Controle import Sistema

        self.notify("pagamento_criado", pagamento)
        self.alterar_status()
        return pagamento


class ClienteFactory:
    """Factory responsável pela criação de clientes."""

    _types = {
        "nacional": ClienteNacional,
        "internacional": ClienteInternacional,
    }

    @staticmethod
    def create(cliente_type: str, id: int, nome: str, documento: str) -> Cliente:
        """Cria um cliente, registra observer e sincroniza com o sistema."""
        classe = ClienteFactory._types.get(cliente_type)
        if classe is None:
            raise ValueError("Tipo inválido de cliente.")

        cliente = classe(id, nome, documento)

        from Controle import Sistema

        sistema = Sistema.acessar_sistema()
        cliente.add_observer(sistema)
        cliente.notify("cliente_criado", cliente)
        return cliente


class ClienteProxy:
    """Proxy para controlar compras de um cliente sem duplicar estado."""

    def __init__(self, cliente_real: Cliente) -> None:
        """Inicializa o proxy com referência ao cliente real."""
        self._cliente_real = cliente_real

    @property
    def cliente_real(self) -> Cliente:
        """Retorna o cliente encapsulado."""
        return self._cliente_real

    def tipo_cliente(self) -> str:
        """Delega o tipo do cliente ao objeto real."""
        return self._cliente_real.tipo_cliente()

    def compra(self, valor: float) -> Invoice:
        """Bloqueia compra quando o cliente estiver bloqueado."""
        if self._cliente_real.bloqueado:
            raise ValueError(f"Cliente {self._cliente_real.id} está bloqueado para compras.")
        return self._cliente_real.compra(valor)

    def pagar(self, metodo: MetodoPagamento, valor: float, invoices: list[Invoice], documento_pagador: str | None = None, parcelas: int = 0,) -> Pagamento:
        """Delega pagamento ao cliente real."""
        return self._cliente_real.pagar(metodo, valor, invoices, documento_pagador, parcelas)

    def listar_invoices(self) -> list[int]:
        """Lista as invoices do cliente real."""
        return self._cliente_real.listar_invoices()

    def divida(self) -> float:
        """Consulta a dívida do cliente real."""
        return self._cliente_real.divida()

    def alterar_status(self) -> None:
        """Atualiza o status do cliente real."""
        self._cliente_real.alterar_status()

    def verificar_status(self) -> str:
        """Consulta o status do cliente real."""
        return self._cliente_real.verificar_status()

    def bloquear_cliente(self) -> None:
        """Bloqueia o cliente real."""
        self._cliente_real.bloquear_cliente()

    def desbloquear_cliente(self) -> None:
        """Desbloqueia o cliente real."""
        self._cliente_real.desbloquear_cliente()


class FachadaCliente:
    """Fachada para simplificar o fluxo de compra e pagamento."""

    def pagamento_na_compra(
        self, cliente: ClienteProxy, valor_compra: float, metodo: MetodoPagamento, documento_pagador: str | None = None, parcelas: int = 0) -> Pagamento:
        """Cria a compra e realiza o pagamento com valor calculado automaticamente."""
        invoice = cliente.compra(valor_compra)
        valor_pagamento = cliente.calcular_valor_pagamento(metodo, [invoice], documento_pagador)
        return cliente.pagar(metodo, valor_pagamento, [invoice], documento_pagador, parcelas)
