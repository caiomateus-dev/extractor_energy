# Integração de LoRA no Sistema

## Como Funciona

O sistema agora suporta adaptadores LoRA treinados para cada par `concessionaria_uf`. Quando um adapter está disponível, ele é automaticamente carregado e usado nas inferências, reduzindo a dependência de prompts longos.

## Fluxo

1. **Treinamento**: Treine um adapter LoRA usando `training/train_lora.py`
2. **Armazenamento**: O adapter é salvo em `adapters/{concessionaria}_{uf}/`
3. **Carregamento Automático**: O `main.py` detecta automaticamente adapters disponíveis
4. **Uso**: Se um adapter existir, ele é usado em todas as inferências para aquela concessionária/UF

## Estrutura de Diretórios

```
extractor_energy/
├── adapters/              # Adaptadores LoRA treinados
│   ├── equatorial_go/
│   │   ├── adapter_config.json
│   │   └── adapter_model.safetensors
│   └── ...
├── training/              # Scripts de treinamento
│   ├── train_lora.py
│   ├── prepare_dataset.py
│   └── config.yaml
└── main.py                # Carrega adapters automaticamente
```

## Preparação de Dados

Para treinar um adapter, você precisa de:

1. **Imagens**: Faturas de energia da concessionária/UF
2. **Anotações**: JSON com os dados extraídos esperados

Formato do `annotations.jsonl`:
```json
{"image": "fatura1.jpg", "json": {"cod_cliente": "123", "valor_fatura": 100.0, ...}}
{"image": "fatura2.jpg", "json": {"cod_cliente": "456", "valor_fatura": 200.0, ...}}
```

## Exemplo Completo

```bash
# 1. Preparar dataset
python training/prepare_dataset.py \
  --data-dir /caminho/para/dados \
  --concessionaria EQUATORIAL \
  --uf GO \
  --output-dir training/datasets/equatorial_go

# 2. Treinar adapter
python training/train_lora.py \
  --dataset training/datasets/equatorial_go \
  --concessionaria EQUATORIAL \
  --uf GO \
  --output-dir adapters/equatorial_go \
  --epochs 3

# 3. O adapter será automaticamente usado nas próximas requisições!
```

## Dependências de Treinamento

Para usar os scripts de treinamento, instale:

```bash
pip install pyyaml datasets
```

Ou adicione ao `pyproject.toml` como dependências opcionais.

## Benefícios

- **Menos dependência de prompts**: O modelo aprende padrões específicos da concessionária
- **Melhor precisão**: Adaptação específica para cada formato de fatura
- **Prompts mais curtos**: Reduz o tamanho do prompt necessário
- **Inferência mais rápida**: Menos tokens para processar

## Notas

- Os adapters são opcionais: se não existir um adapter, o sistema usa o modelo base normalmente
- Múltiplos adapters podem coexistir: cada par `concessionaria_uf` pode ter seu próprio adapter
- O adapter é carregado dinamicamente: não precisa reiniciar o servidor para usar um novo adapter
