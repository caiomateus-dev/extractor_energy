#!/usr/bin/env python3
"""
Prepara dataset no formato HuggingFace para treinamento LoRA com MLX-VLM.

Formato esperado:
- Dataset HuggingFace com colunas 'images' e 'messages'
- 'messages': Lista de dicts com 'role' ('user' ou 'assistant') e 'content'
- 'content' do user deve incluir o token de imagem e o prompt
- 'content' do assistant deve ser a resposta esperada (JSON)
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image
import datasets
from datasets import Dataset, DatasetDict


def load_prompt(concessionaria: str, uf: str, prompts_dir: Path) -> str:
    """Carrega o prompt base para a concessionária/UF."""
    prompt_file = prompts_dir / f"{concessionaria.lower()}_{uf.lower()}.md"
    if not prompt_file.exists():
        # Fallback para prompt base
        prompt_file = prompts_dir / "base.md"
    
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read()


def create_conversation(image_path: str, prompt_text: str, expected_json: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Cria uma conversa no formato esperado pelo MLX-VLM.
    
    Formato:
    [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": <caminho_imagem>},
                {"type": "text", "text": <prompt>}
            ]
        },
        {
            "role": "assistant",
            "content": <resposta_json_esperada>
        }
    ]
    """
    # MLX-VLM usa formato específico para imagens no prompt
    # O token de imagem é inserido automaticamente pelo apply_chat_template
    # Mas para treinamento, precisamos do formato de mensagem completo
    
    user_content = f"<image>\n{prompt_text}"
    assistant_content = json.dumps(expected_json, ensure_ascii=False, indent=2)
    
    return [
        {
            "role": "user",
            "content": user_content
        },
        {
            "role": "assistant",
            "content": assistant_content
        }
    ]


def prepare_dataset(
    data_dir: Path,
    concessionaria: str,
    uf: str,
    prompts_dir: Path,
    output_dir: Path,
    val_split: float = 0.1
) -> None:
    """
    Prepara dataset a partir de um diretório de imagens e anotações JSON.
    
    Estrutura esperada:
    data_dir/
        images/
            image1.jpg
            image2.jpg
            ...
        annotations.jsonl  # Uma linha por imagem: {"image": "image1.jpg", "json": {...}}
    """
    images_dir = data_dir / "images"
    annotations_file = data_dir / "annotations.jsonl"
    
    if not images_dir.exists():
        raise ValueError(f"Diretório de imagens não encontrado: {images_dir}")
    if not annotations_file.exists():
        raise ValueError(f"Arquivo de anotações não encontrado: {annotations_file}")
    
    # Carrega prompt
    prompt_text = load_prompt(concessionaria, uf, prompts_dir)
    
    # Carrega anotações
    examples = []
    with open(annotations_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ann = json.loads(line)
            image_path = images_dir / ann["image"]
            if not image_path.exists():
                print(f"Aviso: Imagem não encontrada: {image_path}")
                continue
            
            # Cria conversa
            messages = create_conversation(str(image_path), prompt_text, ann["json"])
            
            examples.append({
                "image": str(image_path),
                "messages": messages
            })
    
    if not examples:
        raise ValueError("Nenhum exemplo válido encontrado!")
    
    print(f"Preparados {len(examples)} exemplos")
    
    # Cria dataset HuggingFace
    dataset = Dataset.from_list(examples)
    
    # Divide em train/val se necessário
    if val_split > 0:
        dataset_dict = dataset.train_test_split(test_size=val_split, seed=42)
        dataset_dict = DatasetDict({
            "train": dataset_dict["train"],
            "validation": dataset_dict["test"]
        })
    else:
        dataset_dict = DatasetDict({"train": dataset})
    
    # Salva dataset
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_dict.save_to_disk(str(output_dir))
    print(f"Dataset salvo em: {output_dir}")
    
    # Salva info adicional
    info = {
        "concessionaria": concessionaria,
        "uf": uf,
        "num_examples": len(examples),
        "num_train": len(dataset_dict["train"]),
        "num_val": len(dataset_dict.get("validation", [])) if val_split > 0 else 0
    }
    with open(output_dir / "dataset_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Prepara dataset para treinamento LoRA")
    parser.add_argument("--data-dir", type=Path, required=True, help="Diretório com imagens e annotations.jsonl")
    parser.add_argument("--concessionaria", type=str, required=True, help="Nome da concessionária (ex: EQUATORIAL)")
    parser.add_argument("--uf", type=str, required=True, help="UF (ex: GO)")
    parser.add_argument("--prompts-dir", type=Path, default=Path("prompts"), help="Diretório de prompts")
    parser.add_argument("--output-dir", type=Path, required=True, help="Diretório de saída do dataset")
    parser.add_argument("--val-split", type=float, default=0.1, help="Proporção de validação (0.0-1.0)")
    
    args = parser.parse_args()
    
    prepare_dataset(
        data_dir=args.data_dir,
        concessionaria=args.concessionaria,
        uf=args.uf,
        prompts_dir=args.prompts_dir,
        output_dir=args.output_dir,
        val_split=args.val_split
    )


if __name__ == "__main__":
    main()
