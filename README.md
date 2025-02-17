# 🚀 FIAP - Cognitive Environment Project

Este projeto foi desenvolvido como parte do trabalho acadêmico na disciplina de **Cognitive Environments**, abordando **reconhecimento facial e extração de informações de documentos** usando **Computer Vision e AWS Rekognition**.

## 📌 Objetivo do Projeto
O objetivo do projeto é validar documentos de identificação, extraindo **nome, CPF e endereço**, além de comparar a **foto do documento** com uma **foto de validação** para garantir a autenticidade do usuário.

## 🏗️ Estrutura do Projeto

O projeto é dividido em três componentes:

1. **📓 Análise Exploratória (Jupyter Notebook)**
   - Testes usando **OpenCV (`cv2`), DLib e AWS Rekognition** para extração de face.
   - Extração de texto utilizando **AWS Textract**.
   - Comparação de Faces usando **AWS Rekognition**.

2. **🔙 Backend (AWS Lambda)**
   - Repositório: [`fiap-ds-cognitive-environment-backend`](https://github.com/mateuspada/fiap-ds-cognitive-environment-backend)
   - API Serverless em **AWS Lambda** usando **AWS Textract** e **AWS Rekognition**.
   - Inicialmente, a solução usava **DLib e OpenCV**. No entanto, essas bibliotecas exigem dependências do sistema operacional que não funcionam bem no AWS Lambda sem um container dedicado.
   - **Decisão:** Mudar para **AWS Rekognition**, que oferece reconhecimento facial e comparação de faces sem precisar de bibliotecas externas.

3. **🖥️ Frontend (Streamlit)**
   - Repositório: [`fiap-ds-cognitive-environment-frontend`](https://github.com/mateuspada/fiap-ds-cognitive-environment-frontend)
   - Interface web para o usuário fazer **upload das imagens** e visualizar os resultados.
   - Converte arquivos PDF em imagem automaticamente utilizando **PyMuPDF (fitz)**.

---

## 🔙 Backend: AWS Lambda + Rekognition

O backend processa os documentos e valida as informações enviadas pelo usuário.

### **🛠️ Tecnologias**
- **AWS Lambda** (Serverless)
- **AWS Rekognition** (Face Detection & Comparison)
- **AWS Textract** (OCR para extrair textos dos documentos)
- **Python 3.13**

### **📥 Entrada da API**
A API recebe um JSON com as imagens codificadas em **Base64**:

```json
{
    "document_image_base64": "<imagem do documento>",
    "validation_image_base64": "<imagem para validação>",
    "residence_document_base64": "<comprovante de residência>"
}
```

### **📤 Saída da API**
 
Caso a validação seja bem-sucedida:

```json
{
  "statusCode": 200,
  "body": {
    "name": "<nome>",
    "cpf": "<cpf>",
    "photo_validation": true,
    "photo_similarity": 98.75,
    "name_validation": true,
    "address": "<address>"
  }
}
```

Caso haja um erro na validação:

```json
{
  "statusCode": 400,
  "body": "Error in document photo: No face detected"
}
```