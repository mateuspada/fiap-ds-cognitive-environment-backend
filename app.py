import boto3
import base64
import json
import re

# AWS Clients
rekognition_client = boto3.client('rekognition')
textract_client = boto3.client('textract')

def extract_text_from_textract(image_bytes):
    """Extract text from image using AWS Textract."""
    response = textract_client.detect_document_text(Document={'Bytes': image_bytes})
    return [block['Text'] for block in response.get('Blocks', []) if block['BlockType'] == 'LINE']

def find_name_and_cpf(text_lines):
    """Procura padrões para encontrar nome e CPF""" 
    cpf_pattern = r"\d{3}\.\d{3}\.\d{3}-\d{2}" 
    cpf = None
    name = None

    for line in text_lines:
        if "NOME" in line.upper() or "NOME COMPLETO" in line.upper():
            idx = text_lines.index(line)
            if idx + 1 < len(text_lines):
                name = text_lines[idx + 2].strip().title() # No caso de CNH nova, o nome vem 2 linhas depois
        if re.search(cpf_pattern, line):
            cpf = re.search(cpf_pattern, line).group()

    return name, cpf

def extract_address(text_lines):
    """Extract address from residence proof."""
    address_parts = []
    capturing_address = False  # Flag para capturar endereço

    # Regex para identificar CEP 
    cep_pattern = r"\d{5}-\d{3}"

    # Identificar endereço baseado em padrões comuns
    for i, line in enumerate(text_lines):
        # Detecta o início do endereço (Rua, Avenida, etc.)
        if re.search(r"(RUA|AV|AVENIDA|TRAVESSA|ESTRADA|RODOVIA|ALAMEDA|PRAÇA)", line.upper()):
            capturing_address = True  # Começa a capturar endereço
            address_parts.append(line.strip())  # Adiciona a linha inicial

        # Continua capturando linhas do endereço até encontrar um CEP
        elif capturing_address:
            # Se encontrar um termo irrelevante antes do CEP, ignora
            if any(x in line.upper() for x in ["VALOR", "DATA", "PAGAR", "FATURA", "VIA"]):
                continue

            address_parts.append(line.strip())  # Adiciona a linha válida do endereço

            # Se encontrou um CEP, para a captura (pois é o fim do endereço)
            if re.search(cep_pattern, line):
                break

    address = " ".join(address_parts) if address_parts else None

    return address.title()

def detect_faces(image_bytes):
    """Detects exactly one face using AWS Rekognition. Returns error if none or multiple faces found."""
    response = rekognition_client.detect_faces(
        Image={'Bytes': image_bytes},
        Attributes=['DEFAULT']
    )
    
    face_count = len(response.get('FaceDetails', []))

    if face_count == 0:
        return False, "No face detected"
    elif face_count > 1:
        return False, f"Multiple faces detected ({face_count})"
    
    return True, None  # Exactly one face detected

def compare_faces(source_bytes, target_bytes, similarity_threshold=90):
    """Compare faces using AWS Rekognition"""
    response = rekognition_client.compare_faces(
        SourceImage={'Bytes': source_bytes},
        TargetImage={'Bytes': target_bytes},
        SimilarityThreshold=similarity_threshold
    )
    if response.get('FaceMatches'):
        return True, response['FaceMatches'][0]['Similarity']
    return False, 0.0

def lambda_handler(event, context):
    try:
        # Parse request
        payload = json.loads(event["body"]) if "body" in event else event

        # Extract base64 data
        doc_base64 = payload.get("document_image_base64")
        val_base64 = payload.get("validation_image_base64")
        res_base64 = payload.get("residence_document_base64")

        if not doc_base64 or not val_base64 or not res_base64:
            return {"statusCode": 400, "body": "Missing required fields"}

        # Convert Base64 to bytes
        doc_bytes = base64.b64decode(doc_base64)
        val_bytes = base64.b64decode(val_base64)
        res_bytes = base64.b64decode(res_base64)

        # Extract text from document with photo
        text_doc = extract_text_from_textract(doc_bytes)
        name, cpf = find_name_and_cpf(text_doc)

        if not name or not cpf:
            return {"statusCode": 400, "body": "Failed to extract name and CPF"}

        # Extract text from residence proof
        text_res = extract_text_from_textract(res_bytes)
        extracted_address = extract_address(text_res)
        name_match = name.lower() in " ".join(text_res).lower()

        # Detect faces in document and validation photo
        doc_face_detected, doc_error = detect_faces(doc_bytes)
        val_face_detected, val_error = detect_faces(val_bytes)

        if not doc_face_detected:
            return {"statusCode": 400, "body": f"Error in document photo: {doc_error}"}
        if not val_face_detected:
            return {"statusCode": 400, "body": f"Error in validation photo: {val_error}"}

        # Compare faces
        face_valid, similarity_score = compare_faces(doc_bytes, val_bytes)

        # Build response
        response_data = {
            "name": name,
            "cpf": cpf,
            "photo_validation": face_valid,
            "photo_similarity": round(similarity_score, 4),
            "name_validation": name_match,
            "address": extracted_address
        }

        return {"statusCode": 200, "body": json.dumps(response_data)}

    except Exception as e:
        return {"statusCode": 500, "body": f"Server error: {str(e)}"}