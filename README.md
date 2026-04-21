# Sistema de Cobrança em Python

Projeto orientado a objetos para gerenciamento de clientes, invoices, pagamentos e cobradores, com uso de padrões de projeto e organização modular.

## Estrutura dos arquivos

```text
sistema_cobranca/
├── clients.py
├── control.py
├── invoices.py
├── payments.py
└── README.md
```

## Padrões de projeto utilizados

### Factory
Usado para criar objetos sem expor diretamente as classes concretas:

- `InvoiceFactory`
- `PagamentoFactory`
- `ClienteFactory`
- `CobradorFactory`

### Strategy
Usado para variar o cálculo de taxa e o parcelamento:

- `StrategyTaxa`
    - `TaxaPix`, `TaxaTransferencia`, `TaxaCredito`, `TaxaTransferenciaTerceiro`
- `EstrategiaParcelamento`
    - `SemParcelamento`, `ParcelamentoCredito`

### Adapter
Usado para adaptar a classe `TransferenciaViaTerceiro` ao contrato esperado de `Pagamento`:

- `PagamentoAdapter`

### Proxy
Usado para intermediar o acesso ao cliente e impedir compra quando bloqueado:

- `ClienteProxy`

### Facade
Usado para simplificar o fluxo “comprar e pagar”:

- `FachadaCliente`

### Observer
Usado para notificar o sistema quando um cliente é criado ou quando há eventos relevantes:

- `Cliente.notify`
- `Sistema.update`

### Decorator
Usado para alterar o valor final de uma invoice sem modificar a classe base:

- `AplicarMulta`
- `AplicarDesconto`

### Visitor
Usado para geração de extrato textual do pagamento:

- `RelatorioVisitor`

## Regras de negócio principais

### Clientes
- podem ser nacionais ou internacionais;
- possuem invoices, status, documento e bloqueio de compras;
- cliente internacional não pode pagar com PIX;
- cliente bloqueado não pode realizar compra.

### Invoices
- débito deve ter valor positivo;
- crédito deve ter valor negativo (Bônus recebido pela empresa);
- invoice liquidada zera o impacto na dívida;
- crédito expirado deixa de abater saldo;
- invoice vencida de débito gera juros e imposto conforme o tipo do cliente.

### Pagamentos
- o valor pago precisa bater com o valor esperado;
- cada método de pagamento pode ter taxa específica;
- clientes internacionais possuem acréscimo adicional de 3% sobre a base;
- crédito permite parcelamento de 1 a 12 vezes;
- demais meios não aceitam parcelamento.
