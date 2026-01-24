# Treinamento LoRA para Concessionárias

Este diretório contém scripts e configurações para treinar adaptadores LoRA específicos para cada par `concessionaria_uf` usando MLX-VLM.

## Estrutura

- `train_lora.py`: Script principal de treinamento LoRA
- `prepare_dataset.py`: Script para preparar dataset no formato HuggingFace
- `config.yaml`: Configurações de treinamento
- `adapters/`: Diretório onde os adapters treinados serão salvos (criado automaticamente)

## Formato do Dataset

O MLX-VLM espera um dataset HuggingFace com as seguintes colunas:
- `images`: Lista de caminhos para imagens ou objetos PIL.Image
- `messages`: Lista de mensagens no formato de conversa (com role: "user" ou "assistant")

## Como Usar

### 1. Preparar Dataset

```bash
python training/prepare_dataset.py \
  --data-dir /caminho/para/imagens \
  --concessionaria EQUATORIAL \
  --uf GO \
  --output-dir training/datasets/equatorial_go
```

### 2. Treinar LoRA

```bash
python training/train_lora.py \
  --dataset training/datasets/equatorial_go \
  --concessionaria EQUATORIAL \
  --uf GO \
  --output-dir adapters/equatorial_go \
  --epochs 3 \
  --batch-size 4 \
  --learning-rate 1e-5
```

### 3. Usar Adapter Treinado

O adapter será automaticamente carregado pelo `main.py` se existir em `adapters/{concessionaria}_{uf}/`.

## Configurações

Edite `config.yaml` para ajustar hiperparâmetros de treinamento.
