from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import os, boto3, json, time


app = FastAPI()

class Contratacao(BaseModel):
    nome: str
    cpfCnpj: str
    seguros: list
    cep: str

# Configurações
region_name = os.environ.get("AWS_DEFAULT_REGION", "sa-east-1")
sqs_endpoint = os.environ.get("AWS_SQS_ENDPOINT", "http://localhost:4566")
sns_endpoint = os.environ.get("AWS_SNS_ENDPOINT", "http://localhost:4566")
s3_endpoint = os.environ.get("AWS_S3_ENDPOINT", "http://localhost:4566")
queue_name = "minha-fila"
topic_name = "meu-topico"
bucket_name = "meu-bucket"

# Criação da fila SQS
sqs = boto3.client('sqs', region_name=region_name, endpoint_url=sqs_endpoint)
try:
    response = sqs.create_queue(QueueName=queue_name)
    queue_url = response['QueueUrl']
    print(f"Fila SQS criada com URL: {queue_url}")
except sqs.exceptions.QueueNameExists:
    # Se a fila já existir, obtemos a URL
    response = sqs.get_queue_url(QueueName=queue_name)
    queue_url = response['QueueUrl']
    print(f"Fila SQS já existe, usando URL existente: {queue_url}")

# Criação do tópico SNS
sns = boto3.client('sns', region_name=region_name, endpoint_url=sns_endpoint)
try:
    response = sns.create_topic(Name=topic_name)
    topic_arn = response['TopicArn']
    print(f"Tópico SNS criado com ARN: {topic_arn}")
except sns.exceptions.TopicNameInvalid:
    # Se o tópico já existir, obtemos o ARN
    response = sns.create_topic(TopicName=topic_name)
    topic_arn = response['TopicArn']
    print(f"Tópico SNS já existe, usando ARN existente: {topic_arn}")

# Criação do bucket S3
s3 = boto3.client('s3', region_name=region_name, endpoint_url=s3_endpoint)
try:
    print(f"Tentando criar o bucket S3: {bucket_name}")
    time.sleep(5)  # Adicione este atraso
    s3.create_bucket(Bucket=bucket_name)
    print(f"Bucket S3 criado: {bucket_name}")
except s3.exceptions.BucketAlreadyExists:
    print(f"Bucket S3 já existe: {bucket_name}")
except s3.exceptions.BucketAlreadyOwnedByYou:
    print(f"Bucket S3 já existe e pertence a você: {bucket_name}")
except Exception as e:
    print(f"Erro ao criar o bucket S3: {e}")
    # Adicione esta linha para imprimir a mensagem de erro real
    print(f"Erro real: {str(e)}")

@app.post("/contratacao")
async def contratacao(
    arquivo: UploadFile = File(None),
    nome: str = Form(...),
    cpfCnpj: str = Form(...),
    seguros: list = Form(...),
    cep: str = Form(...)
):
    # Converta os dados para um dicionário
    dados_contratacao_dict = {
        "nome": nome,
        "cpfCnpj": cpfCnpj,
        "seguros": seguros,
        "cep": cep
    }

    # Converta o dicionário para uma string JSON
    dados_contratacao_json = json.dumps(dados_contratacao_dict)

    # Envie para SQS
    sqs.send_message(QueueUrl=queue_url, MessageBody=dados_contratacao_json)

    # Publique em SNS
    sns.publish(TopicArn=topic_arn, Message=dados_contratacao_json)

    # Se um arquivo foi fornecido, leia o conteúdo e envie para S3
    if arquivo:
        arquivo_content = arquivo.file.read()
        s3.upload_fileobj(
            Fileobj=arquivo_content,
            Bucket=bucket_name,
            Key=arquivo.filename
        )

    # Salve a mensagem em um arquivo
    with open("mensagem_enviada.json", "w") as arquivo_saida:
        json.dump(dados_contratacao_dict, arquivo_saida, indent=2)

    return {"message": "Dados de contratação recebidos e enviados para SQS, SNS e arquivo enviado para S3 (se fornecido)."}
