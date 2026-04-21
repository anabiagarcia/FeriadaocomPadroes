from Invoices import Invoice
from Clientes import Cliente
from Pagamentos import Pagamento


class Sistema:
    _instance = None

    def __init__(self):
        if Sistema._instance is not None:
            raise Exception("Use acessar_sistema() ao invés de instanciar diretamente.")
        self.cobradores = []
        self.clientes = []
        self.pagamentos = []

    @classmethod
    def acessar_sistema(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def lista_invoices(self) -> list[Invoice]:
        invoices = []
        for cliente in self.clientes:
            invoices.extend(cliente.invoices)
        return invoices

    def consultar_cobrador(self, id: int):
        return next((cobrador for cobrador in self.cobradores if cobrador.id == id), None)

    def consultar_cliente(self, id: int):
        return next((cliente for cliente in self.clientes if cliente.id == id), None)

    def consultar_pagamento(self, id: int):
        return next((pagamento for pagamento in self.pagamentos if pagamento.id == id), None)

    def consultar_invoice(self, id: int):
        invoices = self.lista_invoices()
        return next((invoice for invoice in invoices if invoice.id == id), None)

    def todos_cobrador(self) -> list[int]:
        return [cobrador.id for cobrador in self.cobradores]

    def todos_cliente(self) -> list[int]:
        return [cliente.id for cliente in self.clientes]

    def todos_pagamento(self) -> list[int]:
        return [pagamento.id for pagamento in self.pagamentos]

    def todos_invoice(self) -> list[int]:
        invoices = self.lista_invoices()
        return [invoice.id for invoice in invoices]

    def adicionar_cobrador(self, cobrador):
        self.cobradores.append(cobrador)

    def adicionar_cliente(self, cliente: Cliente):
        self.clientes.append(cliente)

    def adicionar_pagamento(self, pagamento: Pagamento):
        self.pagamentos.append(pagamento)

    def valor_em_aberto(self):
        invoices = self.lista_invoices()
        return sum(invoice.consultar_divida() for invoice in invoices)
    
    def update(self, evento: str, dado):
        if evento == "cobrador_criado":
            self.adicionar_cobrador(dado)
        elif evento == "cliente_criado":
            self.adicionar_cliente(dado)
        elif evento == "pagamento_criado":
            self.adicionar_pagamento(dado)
        elif evento == "invoice_criada":
            pass

class Cobrador:
    def __init__(self, id: int):
        self.id = id
        self.clientes = []

    def adicionar_cliente(self, cliente):
        self.clientes.append(cliente)

    def listar_clientes(self):
        return [cliente.id for cliente in self.clientes]
    
    def consultar_cliente(self, id: int):
        return next((cliente for cliente in self.clientes if cliente.id == id), None)

    def total_divida(self) -> float:
        return sum(cliente.divida() for cliente in self.clientes)

    def clientes_devedores(self):
        return [c for c in self.clientes if c.divida() > 0]

    def clientes_em_credito(self):
        return [c for c in self.clientes if c.divida() < 0]
    
    def bloquear_cliente(self, id: int):
        cliente = self.consultar_cliente(id)
        if cliente == None:
            raise ValueError("Cliente não encontrado em sua base")
        cliente.bloquear_cliente()

    def desbloquear_cliente(self, id: int):
        cliente = self.consultar_cliente(id)
        if cliente == None:
            raise ValueError("Cliente não encontrado em sua base")
        cliente.desbloquear_cliente()

    def cobrar(self):
        for cliente in self.clientes:
            if cliente.divida() > 0:
                print(f"Cobrar cliente {cliente.nome}: dívida = {cliente.divida()}\n")
    

class CobradorFactory:
    @staticmethod
    def create(id: int) -> Cobrador:
        cobrador = Cobrador(id)

        sistema = Sistema.acessar_sistema()
        sistema.update("cobrador_criado", cobrador)

        return cobrador
    

