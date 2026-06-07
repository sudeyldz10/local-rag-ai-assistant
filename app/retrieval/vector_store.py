import math

def cosine_similarity(A, B):                                  #
        dot_product = sum(x * y for x, y in zip(A, B))
        norm_A = math.sqrt(sum(x * x for x in A))
        norm_B = math.sqrt(sum(x * x for x in B))
        
        if norm_A == 0 or norm_B == 0:
             return 0.0
        return dot_product / (norm_A * norm_B)