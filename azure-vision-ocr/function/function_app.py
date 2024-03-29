import azure.functions as func
import logging
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="get_folder")
def get_folder(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP get_folder function processed a request.')

    # Custom Web API skill JSON reference
    # https://learn.microsoft.com/en-us/azure/search/cognitive-search-custom-skill-web-api

    try:
        logging.debug(f"Received RAW Body: {req.get_body()}")
        rjson = json.loads(req.get_body())
        logging.debug(f"JSON body loaded")

        for key in rjson['values']:
            logging.debug(f"Key in values array: {key}")
            url = key['data']['url']
            logging.info(f"Received URL: {url} in recordId: {key['recordId']}")
            folder = url.split("/")[-2]
            del key['data']['url']
            logging.debug(f"URL removed from recordId: {key['recordId']}")
            key['data']['folder'] = folder
            logging.debug(f"Folder added to recordId: {key['recordId']}")
        response = json.dumps(rjson)
        logging.info(f"Response: {response}")
        return func.HttpResponse(
            f"{response}",
            mimetype="application/json"
        )

    except json.decoder.JSONDecodeError as errorMessage:
        responseJson={}
        responseJson['values']=[]
        responseJson['values'].append({
            "recordId": "0",
            "data": {},
            "errors": None,
            "warnings": None
        })
        responseJson['values'][0]['errors']=[]
        responseJson['values'][0]['errors'].append({"message": str("HTTP request does not contain valid JSON data. Exception: "+str(errorMessage))})
        response = json.dumps(responseJson)
        logging.error(f"Error: {str(response)}")
        return func.HttpResponse(
             f"{response}",
             status_code=200
        )

    except IndexError as errorMessage:
        rjson = json.loads(req.get_body())
        for key in rjson['values']:
            logging.info(f"Key: {key}")
            del key['data']['url']
            key['data']['errors'] = []
            key['data']['errors'].append({"message": str("One of the URLs doesn't have a valid URI format. Exception: "+str(errorMessage))})
        response = json.dumps(rjson)
        logging.error(f"Error: {str(response)}")

        return func.HttpResponse(
             f"{response}",
             status_code=200
        )