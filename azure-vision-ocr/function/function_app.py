import base64
import json
import os
import azure.functions as func
import requests

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

ai_multiservice_endpoint = os.getenv("AI_MULTI_SERVICE_ENDPOINT")
ai_multiservice_key = os.getenv("AI_MULTI_SERVICE_KEY")

if (ai_multiservice_endpoint is None or ai_multiservice_key is None):
    raise Exception("Please provide the AI_MULTI_SERVICE_ENDPOINT and AI_MULTI_SERVICE_KEY environment variables.")

#The incoming request from AI Search WebApi will be in the following format: https://learn.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api#sample-input-json-structure
#The response from the function should be in the following format: https://learn.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api#sample-output-json-structure
@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:

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
        output_record = analyze_image(endpoint=ai_multiservice_endpoint, key=ai_multiservice_key, recordId=value["recordId"], data=value["data"])        
        results["values"].append(output_record)

    return json.dumps(results, ensure_ascii=False)

def analyze_image(endpoint, key, recordId, data):
    try:
        imageAsBase64 = data["imageData"]

        headers = {
            'Content-Type': 'application/octet-stream',
            'Ocp-Apim-Subscription-Key': key,
        }

        base64Bytes = imageAsBase64.encode('utf-8')
        inputBytes = base64.b64decode(base64Bytes)

        response = requests.post(f'{endpoint}/vision/v3.2/ocr', headers=headers, data=inputBytes)

        output_record = {}

        if response.status_code == 200 or response.status_code == 201:
            line_infos = [region["lines"] for region in response.json()["regions"]]
            words= []
            for line in line_infos:
                for word_metadata in line:
                    for word_info in word_metadata["words"]:
                        words.append(word_info)

            finalText = ' '.join([word["text"] for word in words])

            output_record = {
                "recordId": recordId,
                "data": {
                    "text": finalText
                },
                "errors": [],
                "warnings": []
            }

        else:
            raise Exception(response.text)
        
    except Exception as error:
        output_record = {
            "recordId": recordId,
            "errors": [ { "message": "Error: " + str(error) }   ] 
        }

    return output_record