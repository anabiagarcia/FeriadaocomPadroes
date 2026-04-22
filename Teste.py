from Clientes import ClienteFactory, MetodoPagamento
from Controle import Sistema, CobradorFactory

def linha():
    print("\n" + "="*60 + "\n")

def teste():
    sistema = Sistema.acessar_sistema()
    sistema.resetar()

    print("CRIANDO COBRADORES...")
    cobrador1 = CobradorFactory.create(1)
    cobrador2 = CobradorFactory.create(2)

    print("CRIANDO CLIENTES...")
    cliente1 = ClienteFactory.create("nacional", 1, "Ana", "111")
    cliente2 = ClienteFactory.create("internacional", 2, "Bea", "222")

    print("ASSOCIANDO CLIENTES AOS COBRADORES...")
    cobrador1.adicionar_cliente(cliente1)
    cobrador2.adicionar_cliente(cliente2)

    linha()

    print("CRIANDO INVOICES...")
    inv1_c1 = cliente1.compra(100)
    inv2_c1 = cliente1.compra(200)

    inv1_c2 = cliente2.compra(150)
    inv2_c2 = cliente2.compra(300)

    print("Cliente 1 invoices:", cliente1.listar_invoices())
    print("Cliente 2 invoices:", cliente2.listar_invoices())

    linha()

    print("DÍVIDAS INICIAIS:")
    print("Cliente 1:", cliente1.divida())
    print("Cliente 2:", cliente2.divida())

    linha()

    print("PAGAMENTO 1 - PIX (cliente nacional)")
    valor1 = cliente1.calcular_valor_pagamento(
        MetodoPagamento.PIX, [inv1_c1]
    )
    cliente1.pagar(MetodoPagamento.PIX, valor1, [inv1_c1])

    linha()

    print("PAGAMENTO 2 - TRANSFERÊNCIA (cliente nacional)")
    valor2 = cliente1.calcular_valor_pagamento(
        MetodoPagamento.TRANSFERENCIA, [inv2_c1]
    )
    cliente1.pagar(MetodoPagamento.TRANSFERENCIA, valor2, [inv2_c1])

    linha()

    print("PAGAMENTO 3 - CRÉDITO (cliente internacional)")
    valor3 = cliente2.calcular_valor_pagamento(
        MetodoPagamento.CREDITO, [inv1_c2]
    )
    cliente2.pagar(MetodoPagamento.CREDITO, valor3, [inv1_c2], parcelas=3)

    linha()

    print("PAGAMENTO 4 - TRANSFERÊNCIA TERCEIRO (cliente internacional)")
    valor4 = cliente2.calcular_valor_pagamento(
        MetodoPagamento.TRANSFERENCIA_TERCEIRO, [inv2_c2], documento_pagador="999"
    )
    cliente2.pagar(
        MetodoPagamento.TRANSFERENCIA_TERCEIRO,
        valor4,
        [inv2_c2],
        documento_pagador="999"
    )

    linha()

    print("DÍVIDAS FINAIS:")
    print("Cliente 1:", cliente1.divida())
    print("Cliente 2:", cliente2.divida())

    linha()

    print("RESUMO SISTEMA:")
    print("Clientes:", sistema.todos_clientes())
    print("Cobradores:", sistema.todos_cobradores())
    print("Pagamentos:", sistema.todos_pagamentos())
    print("Invoices:", sistema.todos_invoices())

    linha()

    print("COBRANÇA:")
    print("Cobrador 1:", cobrador1.cobrar())
    print("Cobrador 2:", cobrador2.cobrar())


if __name__ == "__main__":
    teste()