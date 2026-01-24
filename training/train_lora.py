#!/usr/bin/env python3
"""
Treina adaptador LoRA para um par concessionaria_uf usando MLX-VLM.

Baseado na documentação oficial do MLX-VLM:
https://github.com/blaizzy/mlx-vlm
"""

import argparse
import sys
import subprocess
from pathlib import Path
import yaml

# Verifica se mlx_vlm está disponível (apenas para validar instalação)
try:
    import mlx_vlm
except ImportError:
    print("ERRO: mlx-vlm não está instalado!")
    print("Instale com: pip install mlx-vlm")
    sys.exit(1)


def load_config(config_path: Path) -> dict:
    """Carrega configurações do arquivo YAML."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Treina adaptador LoRA para concessionária/UF")
    
    # Argumentos obrigatórios
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Caminho para o dataset HuggingFace preparado"
    )
    parser.add_argument(
        "--concessionaria",
        type=str,
        required=True,
        help="Nome da concessionária (ex: EQUATORIAL)"
    )
    parser.add_argument(
        "--uf",
        type=str,
        required=True,
        help="UF (ex: GO)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Diretório onde salvar o adapter treinado"
    )
    
    # Argumentos opcionais (podem sobrescrever config.yaml)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "config.yaml",
        help="Caminho para arquivo de configuração YAML"
    )
    parser.add_argument(
        "--base-model",
        type=str,
        help="Modelo base (sobrescreve config.yaml)"
    )
    parser.add_argument(
        "--lora-layers",
        type=int,
        help="Número de camadas LoRA (sobrescreve config.yaml)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Batch size (sobrescreve config.yaml)"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        help="Learning rate (sobrescreve config.yaml)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        help="Número de épocas (sobrescreve config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Carrega configurações
    if args.config.exists():
        config = load_config(args.config)
        print(f"Configurações carregadas de: {args.config}")
    else:
        print(f"Aviso: Arquivo de configuração não encontrado: {args.config}")
        print("Usando valores padrão...")
        config = {}
    
    # Sobrescreve com argumentos da linha de comando
    base_model = args.base_model or config.get("base_model", "mlx-community/Qwen2.5-VL-7B-Instruct-4bit")
    lora_layers = args.lora_layers or config.get("lora_layers", 16)
    batch_size = args.batch_size or config.get("batch_size", 4)
    learning_rate = args.learning_rate or config.get("learning_rate", 1e-5)
    num_epochs = args.epochs or config.get("num_epochs", 3)
    
    # Validações
    if not args.dataset.exists():
        print(f"ERRO: Dataset não encontrado: {args.dataset}")
        sys.exit(1)
    
    # Cria diretório de saída
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("TREINAMENTO LoRA - MLX-VLM")
    print("=" * 60)
    print(f"Concessionária: {args.concessionaria}")
    print(f"UF: {args.uf}")
    print(f"Dataset: {args.dataset}")
    print(f"Modelo base: {base_model}")
    print(f"LoRA layers: {lora_layers}")
    print(f"Batch size: {batch_size}")
    print(f"Learning rate: {learning_rate}")
    print(f"Épocas: {num_epochs}")
    print(f"Output: {args.output_dir}")
    print("=" * 60)
    
    # Prepara comando de treinamento
    # MLX-VLM usa CLI: python -m mlx_vlm.train
    # Não há API Python direta, apenas CLI
    
    try:
        # Usa subprocess para chamar o CLI do MLX-VLM
        cmd = [
            sys.executable, "-m", "mlx_vlm.train",
            "--model", base_model,
            "--dataset", str(args.dataset),
            "--lora-layers", str(lora_layers),
            "--batch-size", str(batch_size),
            "--learning-rate", str(learning_rate),
            "--num-epochs", str(num_epochs),
            "--output-dir", str(args.output_dir),
        ]
        
        print(f"\nExecutando: {' '.join(cmd)}\n")
        
        result = subprocess.run(cmd, check=True)
        
        print("\n" + "=" * 60)
        print("TREINAMENTO CONCLUÍDO COM SUCESSO!")
        print(f"Adapter salvo em: {args.output_dir}")
        print("=" * 60)
        
    except subprocess.CalledProcessError as e:
        print(f"\nERRO durante treinamento: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nERRO inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
