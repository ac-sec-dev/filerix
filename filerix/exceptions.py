class PathValidationError(Exception):
    """
    Exceção levantada quando um caminho fornecido falha em alguma verificação.
    
    Attributes:
        path (str): O caminho que causou a exceção.
        reason (str): Descrição do motivo da falha
    """
    
    def __init__(self, path: str, reason: str):
        self.path = path 
        self.reason = reason 
        
        super().__init__(f'[PathValidationError] Falha ao validar caminho ({path})\n[-] {reason}')
    