from Clientes import ClienteFactory, PgtMetodo
from Controle import Sistema, CobradorFactory


def ler_int(mensagem: str) -> int:
    while True:
        try:
            return int(input(mensagem))
        except ValueError:
            print("Digite um número inteiro válido.")


def ler_float(mensagem: str) -> float:
    while True:
        try:
            return float(input(mensagem).replace(",", "."))
        except ValueError:
            print("Digite um número válido.")


def pausar():
    input("\nPressione Enter para continuar...")


def exibir_menu_acesso():
    print("\n" + "=" * 50)
    print("SISTEMA DE COBRANÇA")
    print("=" * 50)
    print("Quem está acessando?")
    print("1 - Cliente")
    print("2 - Cobrador")
    print("0 - Sair")


def exibir_menu_cliente():
    print("\n--- MENU DO CLIENTE ---")
    print("1 - Comprar / criar invoice")
    print("2 - Pagar invoices")
    print("3 - Consultar minhas invoices")
    print("4 - Consultar minha dívida")
    print("5 - Consultar meu status")
    print("0 - Sair")


def exibir_menu_cobrador():
    print("\n--- MENU DO COBRADOR ---")
    print("1 - Cadastrar cliente")
    print("2 - Cadastrar cobrador")
    print("3 - Vincular cliente a cobrador")
    print("4 - Listar meus clientes")
    print("5 - Ver clientes devedores")
    print("6 - Ver clientes em crédito")
    print("7 - Ver dívida total da carteira")
    print("8 - Cobrar clientes")
    print("9 - Ver resumo do sistema")
    print("0 - Sair")


def cadastrar_cliente():
    sistema = Sistema.acessar_sistema()

    print("\nCadastro de cliente")
    id_cliente = ler_int("ID do cliente: ")
    if sistema.consultar_cliente(id_cliente):
        print("Já existe cliente com esse ID.")
        return

    nome = input("Nome: ").strip()
    documento = ler_int("Documento: ")

    print("Tipo de cliente:")
    print("1 - Nacional")
    print("2 - Internacional")
    tipo_opcao = input("Escolha: ").strip()

    if tipo_opcao == "1":
        tipo = "nacional"
    elif tipo_opcao == "2":
        tipo = "internacional"
    else:
        print("Tipo inválido.")
        return

    try:
        cliente = ClienteFactory.create(tipo, id_cliente, nome, documento)
        print(f"Cliente {cliente.nome} cadastrado com sucesso.")
    except Exception as e:
        print(f"Erro ao cadastrar cliente: {e}")


def cadastrar_cobrador():
    sistema = Sistema.acessar_sistema()

    print("\nCadastro de cobrador")
    id_cobrador = ler_int("ID do cobrador: ")
    if sistema.consultar_cobrador(id_cobrador):
        print("Já existe cobrador com esse ID.")
        return

    try:
        cobrador = CobradorFactory.create(id_cobrador)
        print(f"Cobrador {cobrador.id} cadastrado com sucesso.")
    except Exception as e:
        print(f"Erro ao cadastrar cobrador: {e}")


def vincular_cliente_cobrador(cobrador_logado):
    sistema = Sistema.acessar_sistema()

    print("\nVincular cliente ao cobrador logado")
    id_cliente = ler_int("ID do cliente: ")
    cliente = sistema.consultar_cliente(id_cliente)

    if not cliente:
        print("Cliente não encontrado.")
        return

    if cliente in cobrador_logado.clientes:
        print("Esse cliente já está vinculado a este cobrador.")
        return

    cobrador_logado.adicionar_cliente(cliente)
    print(f"Cliente {cliente.nome} vinculado ao cobrador {cobrador_logado.id}.")


def escolher_invoices_do_cliente(cliente):
    if not cliente.invoices:
        print("Cliente não possui invoices.")
        return []

    print("\nInvoices disponíveis:")
    for invoice in cliente.invoices:
        print(
            f"ID: {invoice.id} | "
            f"Valor base: {invoice.valor:.2f} | "
            f"Status: {invoice.consultar_status()} | "
            f"Dívida atual: {invoice.consultar_divida():.2f}"
        )

    entrada = input("Digite os IDs das invoices separados por vírgula: ").strip()
    if not entrada:
        return []

    try:
        ids = [int(x.strip()) for x in entrada.split(",")]
    except ValueError:
        print("Lista de IDs inválida.")
        return []

    selecionadas = [invoice for invoice in cliente.invoices if invoice.id in ids]

    if not selecionadas:
        print("Nenhuma invoice válida foi selecionada.")
        return []

    return selecionadas


def comprar(cliente):
    print("\nNova compra")
    print("Use valor positivo para débito.")
    print("Use valor negativo para utilizar seu crédito.")
    valor = ler_float("Valor: ")

    try:
        cliente.compra(valor)
        print("Invoice criada com sucesso.")
    except Exception as e:
        print(f"Erro ao criar invoice: {e}")


def pagar(cliente):
    print("\nPagamento")
    invoices = escolher_invoices_do_cliente(cliente)
    if not invoices:
        return

    print("\nMétodo de pagamento:")
    print("1 - PIX")
    print("2 - Transferência")
    print("3 - Transferência por terceiro")
    print("4 - Crédito")

    opcao = input("Escolha: ").strip()

    mapa = {
        "1": PgtMetodo.PIX,
        "2": PgtMetodo.TRANSFERENCIA,
        "3": PgtMetodo.TRANSFERENCIA_TERCEIRO,
        "4": PgtMetodo.CREDITO,
    }

    metodo = mapa.get(opcao)
    if metodo is None:
        print("Método inválido.")
        return

    valor_sugerido = sum(inv.consultar_divida() for inv in invoices)
    print(f"Valor atual das invoices selecionadas: {valor_sugerido:.2f}")

    valor = ler_float("Valor a pagar: ")

    pagador_doc = 0
    if metodo == PgtMetodo.TRANSFERENCIA_TERCEIRO:
        pagador_doc = ler_int("Documento do pagador terceiro: ")

    try:
        pagamento = cliente.pagar(metodo, valor, invoices, pagador_doc)

        if metodo == PgtMetodo.CREDITO:
            parcelas = ler_int("Número de parcelas: ")
            pagamento.aprovar_parcelamento(parcelas)

        pagamento.realizar_pagamento()
        cliente.alterar_status()

        print(f"Pagamento {pagamento.id} realizado com sucesso.")
        print(f"Parcelas aprovadas: {pagamento.parcelas}")
    except Exception as e:
        print(f"Erro ao realizar pagamento: {e}")


def consultar_invoices(cliente):
    print("\nMinhas invoices")
    if not cliente.invoices:
        print("Nenhuma invoice encontrada.")
        return

    for invoice in cliente.invoices:
        print("-" * 40)
        print(f"ID: {invoice.id}")
        print(f"Valor base: {invoice.valor:.2f}")
        print(f"Crédito: {'Sim' if invoice.credito else 'Não'}")
        print(f"Status: {invoice.consultar_status()}")
        print(f"Vencimento: {invoice.vencimento.strftime('%d/%m/%Y %H:%M')}")
        print(f"Imposto: {invoice.calcular_imposto():.2f}")
        print(f"Juros: {invoice.calcular_juros():.2f}")
        print(f"Dívida atual: {invoice.consultar_divida():.2f}")


def consultar_divida(cliente):
    print(f"\nDívida total atual: {cliente.divida():.2f}")


def consultar_status(cliente):
    print(f"\nStatus do cliente: {cliente.verificar_status()}")


def listar_clientes_cobrador(cobrador):
    if not cobrador.clientes:
        print("Esse cobrador não possui clientes.")
        return

    print("\nClientes do cobrador:")
    for cliente in cobrador.clientes:
        print(
            f"ID: {cliente.id} | "
            f"Nome: {cliente.nome} | "
            f"Status: {cliente.verificar_status()} | "
            f"Dívida: {cliente.divida():.2f}"
        )


def ver_clientes_devedores(cobrador):
    devedores = cobrador.clientes_devedores()
    if not devedores:
        print("Nenhum cliente devedor.")
        return

    print("\nClientes devedores:")
    for cliente in devedores:
        print(f"ID: {cliente.id} | Nome: {cliente.nome} | Dívida: {cliente.divida():.2f}")


def ver_clientes_credito(cobrador):
    creditos = cobrador.clientes_em_credito()
    if not creditos:
        print("Nenhum cliente em crédito.")
        return

    print("\nClientes em crédito:")
    for cliente in creditos:
        print(f"ID: {cliente.id} | Nome: {cliente.nome} | Crédito: {cliente.divida():.2f}")


def ver_divida_total(cobrador):
    print(f"\nDívida total da carteira: {cobrador.total_divida():.2f}")


def resumo_sistema():
    sistema = Sistema.acessar_sistema()

    print("\n--- RESUMO DO SISTEMA ---")
    print(f"Cobradores cadastrados: {sistema.todos_cobrador()}")
    print(f"Clientes cadastrados: {sistema.todos_cliente()}")
    print(f"Pagamentos cadastrados: {sistema.todos_pagamento()}")
    print(f"Invoices cadastradas: {sistema.todos_invoice()}")
    print(f"Valor total em aberto: {sistema.valor_em_aberto():.2f}")


def menu_cliente(cliente):
    while True:
        print(f"\nCliente logado: {cliente.nome} (ID {cliente.id})")
        exibir_menu_cliente()
        opcao = input("Escolha: ").strip()

        if opcao == "1":
            comprar(cliente)
            pausar()
        elif opcao == "2":
            pagar(cliente)
            pausar()
        elif opcao == "3":
            consultar_invoices(cliente)
            pausar()
        elif opcao == "4":
            consultar_divida(cliente)
            pausar()
        elif opcao == "5":
            consultar_status(cliente)
            pausar()
        elif opcao == "0":
            break
        else:
            print("Opção inválida.")


def menu_cobrador(cobrador):
    while True:
        print(f"\nCobrador logado: ID {cobrador.id}")
        exibir_menu_cobrador()
        opcao = input("Escolha: ").strip()

        if opcao == "1":
            cadastrar_cliente()
            pausar()
        elif opcao == "2":
            cadastrar_cobrador()
            pausar()
        elif opcao == "3":
            vincular_cliente_cobrador(cobrador)
            pausar()
        elif opcao == "4":
            listar_clientes_cobrador(cobrador)
            pausar()
        elif opcao == "5":
            ver_clientes_devedores(cobrador)
            pausar()
        elif opcao == "6":
            ver_clientes_credito(cobrador)
            pausar()
        elif opcao == "7":
            ver_divida_total(cobrador)
            pausar()
        elif opcao == "8":
            cobrador.cobrar()
            pausar()
        elif opcao == "9":
            resumo_sistema()
            pausar()
        elif opcao == "0":
            break
        else:
            print("Opção inválida.")


def entrar_como_cliente():
    sistema = Sistema.acessar_sistema()
    id_cliente = ler_int("Digite seu ID de cliente: ")
    cliente = sistema.consultar_cliente(id_cliente)

    if not cliente:
        print("Cliente não encontrado.")
        return

    menu_cliente(cliente)


def entrar_como_cobrador():
    sistema = Sistema.acessar_sistema()
    id_cobrador = ler_int("Digite seu ID de cobrador: ")
    cobrador = sistema.consultar_cobrador(id_cobrador)

    if not cobrador:
        print("Cobrador não encontrado.")
        return

    menu_cobrador(cobrador)


def popular_dados_teste():
    sistema = Sistema.acessar_sistema()

    if sistema.clientes or sistema.cobradores:
        return

    c1 = ClienteFactory.create("nacional", 1, "Ana", 11111111111)
    c2 = ClienteFactory.create("internacional", 2, "Bruno", 22222222222)
    cob = CobradorFactory.create(10)

    cob.adicionar_cliente(c1)
    cob.adicionar_cliente(c2)

    c1.compra(100)
    c1.compra(200)
    c2.compra(300)


def main():
    popular_dados_teste()

    while True:
        exibir_menu_acesso()
        opcao = input("Escolha: ").strip()

        if opcao == "1":
            entrar_como_cliente()
        elif opcao == "2":
            entrar_como_cobrador()
        elif opcao == "0":
            print("Encerrando sistema...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()