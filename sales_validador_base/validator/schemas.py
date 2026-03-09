"""
Schema definitions for BNPL data validation.
Extracted from the original validator script.
"""

EXPECTED_SCHEMA: dict[str, str] = {
    "emitente_cnpj": "str",
    "cliente_cnpj": "str",
    "id_cliente": "str",
    "id_pedido": "str",
    "id_parcela": "str",
    "forma_pagamento": "str",
    "data_pedido": "date",
    "data_vencimento": "date",
    "data_pagamento": "date",
    "valor_parcela": "float",
    "valor_pago": "float",
    "forma_pagamento": "str",
}

POST_PROCESS_SCHEMA: dict[str, str] = {
    "emitente_cnpj": "str",
    "cliente_cnpj": "str",
    "id_cliente": "str",
    "id_pedido": "str",
    "id_parcela": "str",
    "forma_pagamento": "str",
    "data_pedido": "date",
    "data_vencimento": "date",
    "data_pagamento": "date",
    "valor_parcela": "float",
    "valor_pago": "float",
    "forma_pagamento": "str",
}

NULL_LIMITS: dict[str, int] = {
    "cliente_cnpj": 0,
    "id_pedido": 0,
    "data_pedido": 0,
    "data_vencimento": 0,
    "valor_parcela": 0,
    "forma_pagamento": 0,
}

PANDAS_TYPE_MAP: dict[str, list[str]] = {
    "str": ["object", "string"],
    "date": ["datetime64[ns]", "datetime64[us]", "datetime64[ms]", "object"],
    "float": ["float64", "float32", "int64", "int32"],
}
