from common import utils
from common import model
from common import _version

def lambda_handler(event, context):
    """
    GET request, list of transactions in event['body']

    Due to lambda proxy integration with REST API, must include specific response format
    """
    print("version:", _version.__version__)
    print("game type:", model.Game.type)
    
