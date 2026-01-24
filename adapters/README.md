# Adaptadores LoRA

Este diretório armazena os adaptadores LoRA treinados para cada par `concessionaria_uf`.

## Estrutura

```
adapters/
  ├── equatorial_go/
  │   ├── adapter_config.json
  │   ├── adapter_model.safetensors
  │   └── ...
  ├── cemig_mg/
  │   └── ...
  └── ...
```

## Como Usar

Os adaptadores são automaticamente carregados pelo `main.py` quando disponíveis.

O sistema procura por adaptadores em: `adapters/{concessionaria}_{uf}/`

Se um adapter existir, ele será usado automaticamente na inferência, reduzindo a dependência de prompts longos.

## Treinamento

Veja `training/README.md` para instruções de como treinar novos adaptadores.
