from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from Invoices import InvoiceFactory, Invoice
from Pagamentos import PagamentoFactory
from Controle import Sistema

class PgtMetodo(Enum):
    PIX = 1
    TRANSFERENCIA = 2
    TRANSFERENCIA_TERCEIRO = 3
    CREDITO = 4


class StatusCli(Enum):
    OK = 1
    DEVENDO = 2
    CREDITO = 3


class GeraPgtId:
    _instance = None

    def __init__(self):
        if GeraPgtId._instance is not None:
            raise Exception("Use get_instance() ao invés de instanciar diretamente.")
        self._contador = 0

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def proximo_id(self) -> int:
        self._contador += 1
        return self._contador


class GeraInvId:
    _instance = None

    def __init__(self):
        if GeraInvId._instance is not None:
            raise Exception("Use get_instance() ao invés de instanciar diretamente.")
        self._contador = 0

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def proximo_id(self) -> int:
        self._contador += 1
        return self._contador


class Cliente(ABC):
    def __init__(self, id: int, nome: str, documento: int):
        self.id = id
        self.data_contrato = datetime.now()
        self.status = StatusCli.OK
        self.invoices = []
        self.nome = nome
        self.documento = documento
        self._observer = None

    def add_observer(self, observer):
        self._observer = observer

    def remove_observer(self):
        self._observer = None

    def notify(self, evento: str, dado):
        if self._observer is not None:
            self._observer.update(evento, dado)

    @abstractmethod
    def tipo_cliente(self) -> str:
        pass

    def compra(self, valor: float):
        gera_id = GeraInvId.get_instance()
        inv_id = gera_id.proximo_id()

        if valor == 0:
            raise ValueError("O valor deve ser diferente de zero.")

        credito = valor < 0
        invoice = InvoiceFactory.create(self.tipo_cliente(), inv_id, valor, credito)
        self.invoices.append(invoice)
        self.alterar_status()
        self.notify("invoice_criada", invoice)

    @abstractmethod
    def pagar(self, metodo: PgtMetodo, valor: float, invoices: list[Invoice], pagador=0):
        pass

    def listar_invoices(self) -> list[int]:
        return [invoice.id for invoice in self.invoices]

    def divida(self) -> float:
        return sum(invoice.consultar_divida() for invoice in self.invoices)

    def alterar_status(self):
        divida = self.divida()
        if divida > 0:
            self.status = StatusCli.DEVENDO
        elif divida < 0:
            self.status = StatusCli.CREDITO
        else:
            self.status = StatusCli.OK

    def verificar_status(self) -> str:
        self.alterar_status()
        return self.status.name


class ClienteInternacional(Cliente):
    def tipo_cliente(self) -> str:
        return "internacional"

    def pagar(self, metodo: PgtMetodo, valor: float, invoices: list[Invoice], pagador=0):
        gera_id = GeraPgtId.get_instance()
        pgt_id = gera_id.proximo_id()

        match metodo:
            case PgtMetodo.PIX:
                raise ValueError("Forma de pagamento inválida")
            case PgtMetodo.TRANSFERENCIA_TERCEIRO:
                pagamento = PagamentoFactory.create(metodo.name, pgt_id, valor, invoices, self, pagador)
            case _:
                pagamento = PagamentoFactory.create(metodo.name, pgt_id, valor, invoices, self)

        self.notify("pagamento_criado", pagamento)
        return pagamento


class ClienteNacional(Cliente):
    def tipo_cliente(self) -> str:
        return "nacional"

    def pagar(self, metodo: PgtMetodo, valor: float, invoices: list[Invoice], pagador=0):
        gera_id = GeraPgtId.get_instance()
        pgt_id = gera_id.proximo_id()

        match metodo:
            case PgtMetodo.TRANSFERENCIA_TERCEIRO:
                pagamento = PagamentoFactory.create(metodo.name, pgt_id, valor, invoices, self, pagador)
            case _:
                pagamento = PagamentoFactory.create(metodo.name, pgt_id, valor, invoices, self)

        self.notify("pagamento_criado", pagamento)
        return pagamento


class ClienteFactory:
    _types = {
        "nacional": ClienteNacional,
        "internacional": ClienteInternacional,
    }

    @staticmethod
    def create(cliente_type: str, id: int, nome: str, documento: int) -> Cliente:
        classe = ClienteFactory._types.get(cliente_type)
        if classe is None:
            raise ValueError("Tipo inválido de Cliente")

        cliente = classe(id, nome, documento)

        sistema = Sistema.acessar_sistema()
        cliente.add_observer(sistema)
        cliente.notify("cliente_criado", cliente)

        return cliente