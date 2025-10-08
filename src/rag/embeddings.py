"""
Gerenciamento de embeddings com suporte a fine-tuning.
"""
import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from loguru import logger

from config.settings import settings


class EmbeddingManager:
    """Gerenciador de embeddings."""
    
    def __init__(self):
        """Inicializa o gerenciador de embeddings."""
        self.use_finetuned = settings.use_finetuned_embeddings
        
        if self.use_finetuned:
            # Carrega modelo fine-tuned
            logger.info(f"Carregando modelo fine-tuned: {settings.finetuned_model_path}")
            self.model = SentenceTransformer(settings.finetuned_model_path)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.provider = "finetuned"
        else:
            # Usa OpenAI embeddings
            logger.info(f"Usando OpenAI embeddings: {settings.openai_embedding_model}")
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model_name = settings.openai_embedding_model
            self.embedding_dim = 3072  # text-embedding-3-large
            self.provider = "openai"
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Gera embedding para um texto.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Embedding como numpy array
        """
        if self.provider == "finetuned":
            return self.model.encode(text, convert_to_numpy=True)
        else:
            response = self.client.embeddings.create(
                input=text,
                model=self.model_name
            )
            return np.array(response.data[0].embedding)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Gera embeddings para um lote de textos.
        
        Args:
            texts: Lista de textos
            batch_size: Tamanho do lote para processamento
            
        Returns:
            Lista de embeddings
        """
        if self.provider == "finetuned":
            return self.model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=True
            )
        else:
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model_name
                )
                batch_embeddings = [np.array(item.embedding) for item in response.data]
                embeddings.extend(batch_embeddings)
                
                if (i + batch_size) % 100 == 0:
                    logger.info(f"Processados {i + batch_size}/{len(texts)} textos")
            
            return embeddings
    
    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calcula similaridade de cosseno entre dois embeddings.
        
        Args:
            emb1: Primeiro embedding
            emb2: Segundo embedding
            
        Returns:
            Similaridade de cosseno (0 a 1)
        """
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    @staticmethod
    def prepare_training_data(
        queries: List[str],
        positive_docs: List[str],
        negative_docs: List[List[str]]
    ) -> List[dict]:
        """
        Prepara dados para fine-tuning de embeddings.
        
        Args:
            queries: Lista de queries
            positive_docs: Documentos relevantes para cada query
            negative_docs: Lista de documentos não relevantes para cada query
            
        Returns:
            Dados formatados para treinamento
        """
        training_data = []
        
        for query, pos_doc, neg_docs in zip(queries, positive_docs, negative_docs):
            training_data.append({
                "query": query,
                "positive": pos_doc,
                "negatives": neg_docs
            })
        
        return training_data


class FineTuner:
    """Fine-tuning de modelos de embedding."""
    
    def __init__(self, base_model: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Inicializa o fine-tuner.
        
        Args:
            base_model: Modelo base para fine-tuning
        """
        self.base_model = base_model
        self.model = SentenceTransformer(base_model)
        logger.info(f"Modelo base carregado: {base_model}")
    
    def train(
        self,
        training_data: List[dict],
        output_path: str,
        epochs: int = 3,
        batch_size: int = 16,
        warmup_steps: int = 100
    ):
        """
        Treina o modelo com dados de domínio específico.
        
        Args:
            training_data: Dados de treinamento (query, positive, negatives)
            output_path: Caminho para salvar o modelo treinado
            epochs: Número de épocas
            batch_size: Tamanho do lote
            warmup_steps: Passos de warmup
        """
        from sentence_transformers import InputExample, losses
        from torch.utils.data import DataLoader
        
        # Prepara exemplos de treinamento
        train_examples = []
        for item in training_data:
            # Positive pair
            train_examples.append(
                InputExample(texts=[item["query"], item["positive"]], label=1.0)
            )
            
            # Negative pairs
            for neg in item["negatives"]:
                train_examples.append(
                    InputExample(texts=[item["query"], neg], label=0.0)
                )
        
        # Cria DataLoader
        train_dataloader = DataLoader(
            train_examples,
            shuffle=True,
            batch_size=batch_size
        )
        
        # Define loss function
        train_loss = losses.CosineSimilarityLoss(self.model)
        
        # Treina
        logger.info(f"Iniciando treinamento com {len(train_examples)} exemplos")
        self.model.fit(
            train_objectives=[(train_dataloader, train_loss)],
            epochs=epochs,
            warmup_steps=warmup_steps,
            output_path=output_path,
            show_progress_bar=True
        )
        
        logger.info(f"Modelo treinado salvo em: {output_path}")
    
    def evaluate(
        self,
        test_queries: List[str],
        test_docs: List[str],
        test_labels: List[int]
    ) -> dict:
        """
        Avalia o modelo em dados de teste.
        
        Args:
            test_queries: Queries de teste
            test_docs: Documentos de teste
            test_labels: Labels (1 para relevante, 0 para não relevante)
            
        Returns:
            Métricas de avaliação
        """
        from sklearn.metrics import accuracy_score, precision_recall_fscore_support
        
        # Gera embeddings
        query_embeddings = self.model.encode(test_queries)
        doc_embeddings = self.model.encode(test_docs)
        
        # Calcula similaridades
        similarities = []
        for q_emb, d_emb in zip(query_embeddings, doc_embeddings):
            sim = np.dot(q_emb, d_emb) / (np.linalg.norm(q_emb) * np.linalg.norm(d_emb))
            similarities.append(sim)
        
        # Threshold para classificação
        threshold = 0.5
        predictions = [1 if sim > threshold else 0 for sim in similarities]
        
        # Calcula métricas
        accuracy = accuracy_score(test_labels, predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            test_labels, predictions, average='binary'
        )
        
        metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
        
        logger.info(f"Métricas de avaliação: {metrics}")
        return metrics
