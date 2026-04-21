from Invoices import Invoice
from Clientes import Cliente
from Pagamentos import Pagamento


class Sistema:
    _instance = None

    def __init__(self):
        if Sistema._instance is not None:
            raise Exception("Use acessar_sistema() ao invés de instanciar diretamente.")
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

    def consultar_cliente(self, id: int):
        return next((cliente for cliente in self.clientes if cliente.id == id), None)

    def consultar_pagamento(self, id: int):
        return next((pagamento for pagamento in self.pagamentos if pagamento.id == id), None)

    def consultar_invoice(self, id: int):
        invoices = self.lista_invoices()
        return next((invoice for invoice in invoices if invoice.id == id), None)

    def todos_cliente(self) -> list[int]:
        return [cliente.id for cliente in self.clientes]

    def todos_pagamento(self) -> list[int]:
        return [pagamento.id for pagamento in self.pagamentos]

    def todos_invoice(self) -> list[int]:
        invoices = self.lista_invoices()
        return [invoice.id for invoice in invoices]

    def adicionar_cliente(self, cliente: Cliente):
        self.clientes.append(cliente)

    def adicionar_pagamento(self, pagamento: Pagamento):
        self.pagamentos.append(pagamento)

    def valor_em_aberto(self):
        invoices = self.lista_invoices() 
        return sum(invoice.consultar_divida() for invoice in invoices)
    
    def update(self, evento: str, dado):
        if evento == "cliente_criado":
            self.adicionar_cliente(dado)
        elif evento == "pagamento_criado":
            self.adicionar_pagamento(dado)
        elif evento == "invoice_criada":
            pass