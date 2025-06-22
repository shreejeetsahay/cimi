# app/services/vectors.py
from pinecone import Pinecone, ServerlessSpec


class Vectors:
    def __init__(self, api_key):
        self.api_key = api_key
        self.pc = Pinecone(api_key=self.api_key)

    def create_index(
        self,
        index_name,
        dimension,
        metric="cosine",
        vector_type="dense",
        cloud={"name": "aws", "region": "us-east-1"},
        deletion_protection="disabled",
        tags={"environment": "development"},
    ):
        # Create a dense index with integrated embedding
        index_name = index_name
        if not self.pc.has_index(index_name):
            self.pc.create_index(
                name=index_name,
                vector_type=vector_type,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(cloud=cloud["name"], region=cloud["region"]),
                deletion_protection=deletion_protection,
                tags=tags,
            )

    def upsert_vectors(self, index_name, namespace, vectors):
        if self.pc.has_index(index_name):
            # Target the index
            dense_index = self.pc.Index(index_name)
            # Upsert the records into a namespace
            dense_index.upsert(namespace=namespace, vectors=vectors)
        else:
            print(f"Index {index_name} does not exist.")

    def similarity_search(
        self, index_name, namespace, query_vector, no_of_results, filter=None
    ):
        if self.pc.has_index(index_name):
            index = self.pc.Index(index_name)
            if filter:
                results = index.query(
                    vector=query_vector,
                    top_k=no_of_results,
                    namespace=namespace,
                    filter=filter,
                    include_metadata=True,
                    include_values=False,
                )
            else:
                results = index.query(
                    namespace=namespace,
                    vector=query_vector,
                    top_k=no_of_results,
                    include_metadata=True,
                    include_values=False,
                )
            for match in results["matches"]:
                print(f"{match['id']} (score: {match['score']:.4f})")
                print(" →", match.get("metadata"), "\n")
            return results
        else:
            print(f"Index {index_name} does not exist.")
            return -1 
        
    def get_vector_count(self, index_name, namespace):
        if self.pc.has_index(index_name):
            dense_index = self.pc.Index(index_name)
            stats = dense_index.describe_index_stats()
            namespace_data = stats['namespaces']
            if namespace in namespace_data.keys():
                return namespace_data[namespace]["vector_count"]
            else:
                print(f"Namespace {namespace} does not exist.")
                return -1 
        else:
            print(f"Index {index_name} does not exist.")
            return -1