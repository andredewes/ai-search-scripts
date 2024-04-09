import os
import azure.functions as func
import logging
import json
from openai import AzureOpenAI
import tiktoken

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

openai_endpoint = os.getenv("OPENAI_ENDPOINT")
openai_key = os.getenv("OPENAI_KEY")
openai_deployment = os.getenv("OPENAI_DEPLOYMENT")

if (openai_endpoint is None or openai_key is None or openai_deployment is None):
    raise Exception("Please provide the OPENAI_ENDPOINT, OPENAI_KEY, and OPENAI_DEPLOYMENT environment variables.")

#The incoming request from AI Search WebApi will be in the following format: https://learn.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api#sample-input-json-structure
#The response from the function should be in the following format: https://learn.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api#sample-output-json-structure
@app.route(route="extractTokenAtPosition")
def extractTokenAtPosition(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP extractTokenAtPosition function processed a request.')
    try:
        logging.info(f"Received RAW Body: {req.get_body()}")
        body = json.dumps(req.get_json())

        if body:
            result = compose_response(body, "extractTokenAtPosition")

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
    
@app.route(route="summarize")
def summarize(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP extractTokenAtPosition function processed a request.')
    try:
        body = json.dumps(req.get_json())

        if body:
            result = compose_response(body, "summary")

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

def compose_response(json_data, function_name):
    values = json.loads(json_data)['values']

    # Prepare the Output before the loop
    results = {}
    results["values"] = []

    for value in values:
        if function_name == "extractTokenAtPosition":
            output_record = splitString(data=value['data'], recordId=value['recordId'])

        if function_name == "summary":
            output_record = makeSummary(data=value['data'], recordId=value['recordId'])
            
        results['values'].append(output_record)
        #if function_name == "trim":
        #    output_record = trim(data=value['data'], recordId=value['recordId'])

    logging.info(f"HTTP Return: {results}")
    return json.dumps(results, ensure_ascii=False)

def splitString(data, recordId):
    # Custom Web API skill JSON reference
    # https://learn.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api

    output_record = {
        "recordId": None,
        "data": {},
        "errors": None,
        "warnings": None
    }

    try:
        logging.info(f"Data in values array: {data}")
        text = data['text']
        delimiter = data['delimiter']
        position = data['position']

        textSplit = text.split(delimiter)[int(position)]

        output_record['recordId'] = recordId
        output_record['data']['text'] = textSplit

    except IndexError as error:
        logging.error(f"Invalid text, delimiter to split. Error: {error}")
        output_record['recordId'] = recordId
        output_record['errors'] = [{"message": "Invalid text, delimiter to split. Error: " + str(error)}]

    except Exception as error:
        logging.error(f"Error: {error}")
        output_record['recordId'] = recordId
        output_record['errors'] = [{"message": "Error: " + str(error)}]

    logging.info(f"output_record: {output_record}")
    return output_record

def makeSummary(data, recordId):
    output_record = {
        "recordId": None,
        "data": {},
        "errors": None,
        "warnings": None
    }

    try:
        client = AzureOpenAI(
            api_key=openai_key,  
            api_version="2024-02-01",
            azure_endpoint = openai_endpoint
            )
    
        prompt = f"""Resuma esse texto abaixo. Instruções:
- Mantenha no resumo informações como nomes, números de processos, protocolos, valores monetários, datas, resoluções, email, URLs e referências a leis do Brasil
- Mantenha todas informações que são relevantes a processos jurídicos
- Seja possível reconstruir todo esse texto original sem perder sentido
- Seja conciso
===
Texto:
{data['text']}
====
Resumo:
"""   
        response = client.chat.completions.create(
            model=openai_deployment,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.0,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stream=False
        )

        summary = response.choices[0].message.content;

        tokens_original_text = num_tokens_from_string(prompt)
        tokens_summary = num_tokens_from_string(summary)

        output_record['recordId'] = recordId
        output_record['data']['summary'] = summary 
        output_record['data']['tokens_text'] = tokens_original_text
        output_record['data']['tokens_summary'] = tokens_summary

    except Exception as error:
        logging.error(f"Error: {error}")
        output_record['recordId'] = recordId
        output_record['errors'] = [{"message": "Error: " + str(error)}]

    logging.info(f"output_record: {output_record}")
    return output_record

def num_tokens_from_string(string: str) -> int:
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    num_tokens = len(encoding.encode(string))
    return num_tokens