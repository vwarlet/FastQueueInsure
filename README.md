# Fast Queue Insure
Projetinho utilizando FastAPI, Localstack, SQL, SNS

## Execução

Iniciar o container
```
docker-compose up --build
```

Enviar a mensagem
```
curl -X POST -H "Content-Type: multipart/form-data" \
-F "nome=Diego" \
-F "cpfCnpj=123456789" \
-F "seguros=residencial,rural,itens-pessoais" \
-F "cep=49030170" \
http://localhost:8000/contratacao
```

Comando para visualizar a mensagem enviada
``` 
aws --endpoint-url=http://localhost:4566 sqs receive-message --queue-url <URL da Fila>
```
