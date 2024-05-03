import json
import os
import azure.functions as func
from urllib.request import urlretrieve
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from urllib.request import urlopen

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

ai_multiservice_endpoint = os.getenv("AI_MULTI_SERVICE_ENDPOINT")
ai_multiservice_key = os.getenv("AI_MULTI_SERVICE_KEY")

if (ai_multiservice_endpoint is None or ai_multiservice_key is None):
    raise Exception("Please provide the AI_MULTI_SERVICE_ENDPOINT and AI_MULTI_SERVICE_KEY environment variables.")

credential = AzureKeyCredential(ai_multiservice_key)
document_intelligence_client = DocumentIntelligenceClient(ai_multiservice_endpoint, credential)

#The incoming request from AI Search WebApi will be in the following format: https://learn.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api#sample-input-json-structure
#The response from the function should be in the following format: https://learn.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api#sample-output-json-structure
@app.route(route="analyze_document")
def analyze_document(req: func.HttpRequest) -> func.HttpResponse:

    try:
        body = json.dumps(req.get_json())

        if body:
            result = compose_response(body)

            return func.HttpResponse(result, mimetype="application/json")
        else:
            return func.HttpResponse(
                "Invalid body",
                status_code=400
            )
    except ValueError:
        return func.HttpResponse(
            "Invalid body",
            status_code=400
        )

def compose_response(json_data):
    values = json.loads(json_data)['values']
    
    # Prepare the Output before the loop
    results = {}
    results["values"] = []
    
    for value in values:
        output_record = analyze(endpoint=ai_multiservice_endpoint, key=ai_multiservice_key, recordId=value["recordId"], data=value["data"])        
        results["values"].append(output_record)

    return json.dumps(results, ensure_ascii=False)

def analyze(endpoint, key, recordId, data):
    try:
        blobUrl = data["blobUrl"]
        
        blobUrl += data["blobSasToken"]
        model = data["model"]
        outputFormat = data["outputFormat"]

        document_analysis_client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))

        data = urlopen(blobUrl).read()
        poller = document_analysis_client.begin_analyze_document(model, analyze_request=data, output_content_format=outputFormat, content_type="application/octet-stream")
        result = poller.result()

        output_record = {
            "recordId": recordId,
            "data": {
                    "content": result.content
                }
        }

    except Exception as error:
        output_record = {
            "recordId": recordId,
            "errors": [ { "message": "Error: " + str(error) }   ] 
        }

    return output_record