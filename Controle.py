from __future__ import annotations

"""Módulo com o sistema central e entidades administrativas."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from Clientes import Cliente
    from Invoices import Invoice
    from Pagamentos import Pagamento


class Sistema:
    """Singleton que centraliza o estado do sistema."""

    _instance = None

    def __init__(self) -> None:
        """Inicializa as coleções internas do sistema.

        Raises:
            Exception: Se houver tentativa de instância direta duplicada.
        """
        if Sistema._instance is not None:
            raise Exception("Use acessar_sistema() ao invés de instanciar diretamente.")
        self.cobradores: list[Cobrador] = []
        self.clientes: list[Cliente] = []
        self.pagamentos: list[Pagamento] = []

    @classmethod
    def acessar_sistema(cls) -> "Sistema":
        """Retorna a instância única do sistema."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def resetar(self) -> None:
        """Limpa os dados do sistema.

        Útil para testes e demonstrações.
        """
        self.cobradores.clear()
        self.clientes.clear()
        self.pagamentos.clear()

    def lista_invoices(self) -> list[Invoice]:
        """Retorna todas as invoices dos clientes cadastrados."""
        invoices: list[Invoice] = []
        for cliente in self.clientes:
            invoices.extend(cliente.invoices)
        return invoices

    def consultar_cobrador(self, id: int) -> "Cobrador | None":
        """Busca um cobrador por id."""
        return next((cobrador for cobrador in self.cobradores if cobrador.id == id), None)

    def consultar_cliente(self, id: int) -> Cliente | None:
        """Busca um cliente por id."""
        return next((cliente for cliente in self.clientes if cliente.id == id), None)

    def consultar_pagamento(self, id: int) -> Pagamento | None:
        """Busca um pagamento por id."""
        return next((pagamento for pagamento in self.pagamentos if pagamento.id == id), None)

    def consultar_invoice(self, id: int) -> Invoice | None:
        """Busca uma invoice por id."""
        return next((invoice for invoice in self.lista_invoices() if invoice.id == id), None)

    def todos_cobradores(self) -> list[int]:
        """Lista os ids de todos os cobradores."""
        return [cobrador.id for cobrador in self.cobradores]

    def todos_clientes(self) -> list[int]:
        """Lista os ids de todos os clientes."""
        return [cliente.id for cliente in self.clientes]

    def todos_pagamentos(self) -> list[int]:
        """Lista os ids de todos os pagamentos."""
        return [pagamento.id for pagamento in self.pagamentos]

    def todos_invoices(self) -> list[int]:
        """Lista os ids de todas as invoices."""
        return [invoice.id for invoice in self.lista_invoices()]

    def adicionar_cobrador(self, cobrador: "Cobrador") -> None:
        """Adiciona um cobrador ao sistema.

        Raises:
            ValueError: Se já existir cobrador com o mesmo id.
        """
        if self.consultar_cobrador(cobrador.id) is not None:
            raise ValueError(f"Já existe cobrador com id {cobrador.id}.")
        self.cobradores.append(cobrador)

    def adicionar_cliente(self, cliente: Cliente) -> None:
        """Adiciona um cliente ao sistema.

        Raises:
            ValueError: Se já existir cliente com o mesmo id.
        """
        if self.consultar_cliente(cliente.id) is not None:
            raise ValueError(f"Já existe cliente com id {cliente.id}.")
        self.clientes.append(cliente)

    def adicionar_pagamento(self, pagamento: Pagamento) -> None:
        """Adiciona um pagamento validado ao sistema.

        Raises:
            ValueError: Se já existir pagamento com o mesmo id.
        """
        if self.consultar_pagamento(pagamento.id) is not None:
            raise ValueError(f"Já existe pagamento com id {pagamento.id}.")
        self.pagamentos.append(pagamento)

    def valor_em_aberto(self) -> float:
        """Retorna a soma das dívidas atuais de todas as invoices."""
        return sum(invoice.consultar_divida() for invoice in self.lista_invoices())

    def update(self, evento: str, dado: Any) -> None:
        """Recebe eventos do observer e sincroniza o sistema."""
        if evento == "cobrador_criado":
            self.adicionar_cobrador(dado)
        elif evento == "cliente_criado":
            self.adicionar_cliente(dado)
        elif evento == "pagamento_criado":
            self.adicionar_pagamento(dado)


class Cobrador:
    """Representa um cobrador responsável por uma carteira de clientes."""

    def __init__(self, id: int) -> None:
        """Inicializa um cobrador com lista vazia de clientes."""
        self.id = id
        self.clientes: list[Cliente] = []

    def adicionar_cliente(self, cliente: Cliente) -> None:
        """Adiciona cliente à carteira do cobrador.

        Raises:
            ValueError: Se o cliente já estiver vinculado ao cobrador.
        """
        if self.consultar_cliente(cliente.id) is not None:
            raise ValueError(f"Cliente {cliente.id} já está na carteira deste cobrador.")
        self.clientes.append(cliente)

    def listar_clientes(self) -> list[int]:
        """Lista os ids dos clientes da carteira."""
        return [cliente.id for cliente in self.clientes]

    def consultar_cliente(self, id: int) -> Cliente | None:
        """Busca um cliente da carteira por id."""
        return next((cliente for cliente in self.clientes if cliente.id == id), None)

    def total_divida(self) -> float:
        """Retorna a dívida agregada da carteira do cobrador."""
        return sum(cliente.divida() for cliente in self.clientes)

    def clientes_devedores(self) -> list[Cliente]:
        """Retorna clientes com dívida positiva."""
        return [c for c in self.clientes if c.divida() > 0]

    def clientes_em_credito(self) -> list[Cliente]:
        """Retorna clientes com saldo credor."""
        return [c for c in self.clientes if c.divida() < 0]

    def bloquear_cliente(self, id: int) -> None:
        """Bloqueia compras de um cliente da carteira."""
        cliente = self.consultar_cliente(id)
        if cliente is None:
            raise ValueError("Cliente não encontrado em sua base.")
        cliente.bloquear_cliente()

    def desbloquear_cliente(self, id: int) -> None:
        """Desbloqueia compras de um cliente da carteira."""
        cliente = self.consultar_cliente(id)
        if cliente is None:
            raise ValueError("Cliente não encontrado em sua base.")
        cliente.desbloquear_cliente()

    def cobrar(self) -> list[str]:
        """Gera mensagens de cobrança para clientes devedores."""
        mensagens = []
        for cliente in self.clientes:
            if cliente.divida() > 0:
                mensagens.append(f"Cobrar cliente {cliente.nome}: dívida = {cliente.divida():.2f}")
        return mensagens


class CobradorFactory:
    """Factory de cobradores."""

    @staticmethod
    def create(id: int) -> Cobrador:
        """Cria um cobrador e o registra no sistema."""
        cobrador = Cobrador(id)
        sistema = Sistema.acessar_sistema()
        sistema.update("cobrador_criado", cobrador)
        return cobrador
