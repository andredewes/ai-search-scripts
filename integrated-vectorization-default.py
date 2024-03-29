import requests
import json

azureAccessToken = "eyJ0eXAiOiJKV1QiLCJhbG..."

# AI Search parameters
baseUrl = "https://andre.search.windows.net"
indexName = "test-python7"

# Data source parameters
storageAccountConnectionString = "DefaultEndpointsProtocol..."
blobContainerName = "container-name"

# OpenAI parameters
openAiUrl = "https://xyz.openai.azure.com"
embeddingDeploymentId = "andre-embedding"
openAiApiKey = "2e6e8..."

# AI Multi-service account -> check here if you don't know what is this: https://learn.microsoft.com/en-us/azure/ai-services/multi-service-resource
multiserviceAccountApiKey = "4784a8f18d2f42a2..."

headers = {"Content-Type": "application/json", "Authorization" : "Bearer " + azureAccessToken}

### Create the Data Source ###

datasourceRequest = {
    "container": {
        "name": blobContainerName
    },
    "credentials": {
        "connectionString": storageAccountConnectionString
    },
    "dataDeletionDetectionPolicy": {
        "@odata.type": "#Microsoft.Azure.Search.NativeBlobSoftDeleteDeletionDetectionPolicy"
    },
    "name":  f'{indexName}-datasource',
    "type": "azureblob"
}

response = requests.post(f'{baseUrl}/datasources?api-version=2023-10-01-Preview', headers=headers, data=json.dumps(datasourceRequest))

if response.status_code == 200 or response.status_code == 201:
    print("Data source created!")
else:
    print(response.text)
    raise Exception("Data source request failed")

### Create the Index ###

indexRequest = {
    "name": indexName,
    "defaultScoringProfile": None,
    "fields": [
        {
            "name": "chunk_id",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "retrievable": True,
            "sortable": True,
            "facetable": True,
            "key": True,
            "indexAnalyzer": None,
            "searchAnalyzer": None,
            "analyzer": "keyword",
            "normalizer": None,
            "dimensions": None,
            "vectorSearchProfile": None,
            "synonymMaps": []
        },
        {
            "name": "parent_id",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "retrievable": True,
            "sortable": True,
            "facetable": True,
            "key": False,
            "indexAnalyzer": None,
            "searchAnalyzer": None,
            "analyzer": None,
            "normalizer": None,
            "dimensions": None,
            "vectorSearchProfile": None,
            "synonymMaps": []
        },
        {
            "name": "chunk",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "retrievable": True,
            "sortable": False,
            "facetable": False,
            "key": False,
            "indexAnalyzer": None,
            "searchAnalyzer": None,
            "analyzer": None,
            "normalizer": None,
            "dimensions": None,
            "vectorSearchProfile": None,
            "synonymMaps": []
        },
        {
            "name": "title",
            "type": "Edm.String",
            "searchable": True,
            "filterable": True,
            "retrievable": True,
            "sortable": False,
            "facetable": False,
            "key": False,
            "indexAnalyzer": None,
            "searchAnalyzer": None,
            "analyzer": None,
            "normalizer": None,
            "dimensions": None,
            "vectorSearchProfile": None,
            "synonymMaps": []
        },
        {
            "name": "vector",
            "type": "Collection(Edm.Single)",
            "searchable": True,
            "filterable": False,
            "retrievable": True,
            "sortable": False,
            "facetable": False,
            "key": False,
            "indexAnalyzer": None,
            "searchAnalyzer": None,
            "analyzer": None,
            "normalizer": None,
            "dimensions": 1536,
            "vectorSearchProfile": f'{indexName}-profile',
            "synonymMaps": []
        }
    ],
    "scoringProfiles": [],
    "corsOptions": None,
    "suggesters": [],
    "analyzers": [],
    "normalizers": [],
    "tokenizers": [],
    "tokenFilters": [],
    "charFilters": [],
    "encryptionKey": None,
    "similarity": {
        "@odata.type": "#Microsoft.Azure.Search.BM25Similarity",
        "k1": None,
        "b": None
    },
    "semantic": {
        "defaultConfiguration": f'{indexName}-semantic-configuration',
        "configurations": [
            {
                "name": f'{indexName}-semantic-configuration',
                "prioritizedFields": {
                    "titleField": {
                        "fieldName": "title"
                    },
                    "prioritizedContentFields": [
                        {
                            "fieldName": "chunk"
                        }
                    ],
                    "prioritizedKeywordsFields": []
                }
            }
        ]
    },
    "vectorSearch": {
        "algorithms": [
            {
                "name": f'{indexName}-algorithm',
                "kind": "hnsw",
                "hnswParameters": {
                    "metric": "cosine",
                    "m": 4,
                    "efConstruction": 400,
                    "efSearch": 500
                },
                "exhaustiveKnnParameters": None
            }
        ],
        "profiles": [
            {
                "name": f'{indexName}-profile',
                "algorithm": f'{indexName}-algorithm',
                "vectorizer": f'{indexName}-vectorizer'
            }
        ],
        "vectorizers": [
            {
                "name": f'{indexName}-vectorizer',
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": openAiUrl,
                    "deploymentId": embeddingDeploymentId,
                    "apiKey": openAiApiKey,
                    "authIdentity": None
                },
                "customWebApiParameters": None
            }
        ]
    }
}

response = requests.post(f'{baseUrl}/indexes?api-version=2023-10-01-Preview', headers=headers, data=json.dumps(indexRequest))

if response.status_code == 200 or response.status_code == 201:
    print("Index created!")
else:
    print(response.text)
    raise Exception("Index request failed")


### Create the Skillset ###

skillsetRequest = {
    "name": f'{indexName}-skillset',
    "description": "Skillset to chunk documents and generate embeddings",
    "skills": [
        {
            "@odata.type": "#Microsoft.Skills.Text.AzureOpenAIEmbeddingSkill",
            "name": None,
            "description": None,
            "context": "/document/pages/*",
            "resourceUri": openAiUrl,
            "apiKey": openAiApiKey,
            "deploymentId": embeddingDeploymentId,
            "inputs": [
                {
                    "name": "text",
                    "source": "/document/pages/*",
                    "sourceContext": None,
                    "inputs": []
                }
            ],
            "outputs": [
                {
                    "name": "embedding",
                    "targetName": "vector"
                }
            ],
            "authIdentity": None
        },
        {
            "@odata.type": "#Microsoft.Skills.Text.SplitSkill",
            "name": None,
            "description": "Split skill to chunk documents",
            "context": "/document",
            "defaultLanguageCode": None,
            "textSplitMode": "pages",
            "maximumPageLength": 2000,
            "pageOverlapLength": 500,
            "inputs": [
                {
                    "name": "text",
                    "source": "/document/mergedText",
                    "sourceContext": None,
                    "inputs": []
                }
            ],
            "outputs": [
                {
                    "name": "textItems",
                    "targetName": "pages"
                }
            ]
        },
        {
            "@odata.type": "#Microsoft.Skills.Text.MergeSkill",
            "name": None,
            "description": None,
            "context": "/document",
            "insertPreTag": None,
            "insertPostTag": None,
            "inputs": [
                {
                    "name": "text",
                    "source": "/document/content",
                    "sourceContext": None,
                    "inputs": []
                },
                {
                    "name": "itemsToInsert",
                    "source": "/document/normalized_images/*/text",
                    "sourceContext": None,
                    "inputs": []
                },
                {
                    "name": "offsets",
                    "source": "/document/normalized_images/*/contentOffset",
                    "sourceContext": None,
                    "inputs": []
                }
            ],
            "outputs": [
                {
                    "name": "mergedText",
                    "targetName": "mergedText"
                }
            ]
        },
        {
            "@odata.type": "#Microsoft.Skills.Vision.OcrSkill",
            "name": None,
            "description": None,
            "context": "/document/normalized_images/*",
            "textExtractionAlgorithm": None,
            "lineEnding": None,
            "defaultLanguageCode": None,
            "detectOrientation": True,
            "inputs": [
                {
                    "name": "image",
                    "source": "/document/normalized_images/*",
                    "sourceContext": None,
                    "inputs": []
                }
            ],
            "outputs": [
                {
                    "name": "text",
                    "targetName": "text"
                }
            ]
        }
    ],
    "cognitiveServices": {
        "@odata.type": "#Microsoft.Azure.Search.CognitiveServicesByKey",
        "description": None,
        "key": multiserviceAccountApiKey
    },
    "knowledgeStore": None,
    "indexProjections": {
        "selectors": [
            {
                "targetIndexName": "vector-debug-test",
                "parentKeyFieldName": "parent_id",
                "sourceContext": "/document/pages/*",
                "mappings": [
                    {
                        "name": "chunk",
                        "source": "/document/pages/*",
                        "sourceContext": None,
                        "inputs": []
                    },
                    {
                        "name": "vector",
                        "source": "/document/pages/*/vector",
                        "sourceContext": None,
                        "inputs": []
                    },
                    {
                        "name": "title",
                        "source": "/document/metadata_storage_name",
                        "sourceContext": None,
                        "inputs": []
                    }
                ]
            }
        ],
        "parameters": {
            "projectionMode": "skipIndexingParentDocuments"
        }
    },
    "encryptionKey": None
}

response = requests.post(f'{baseUrl}/skillsets?api-version=2023-10-01-Preview', headers=headers, data=json.dumps(skillsetRequest))

if response.status_code == 200 or response.status_code == 201:
    print("Skillset created!")
else:
    print(response.text)
    raise Exception("Skillset request failed")

### Create the Indexer ###

indexerRequest = {
    "name": f'{indexName}-indexer',
    "description": None,
    "dataSourceName": f'{indexName}-datasource',
    "skillsetName": f'{indexName}-skillset',
    "targetIndexName": indexName,
    "disabled": None,
    "schedule": None,
    "parameters": {
        "batchSize": None,
        "maxFailedItems": None,
        "maxFailedItemsPerBatch": None,
        "base64EncodeKeys": None,
        "configuration": {
            "dataToExtract": "contentAndMetadata",
            "parsingMode": "default",
            "imageAction": "generateNormalizedImages"
        }
    },
    "fieldMappings": [
        {
            "sourceFieldName": "metadata_storage_name",
            "targetFieldName": "title",
            "mappingFunction": None
        }
    ],
    "outputFieldMappings": [],
    "cache": None,
    "encryptionKey": None
}

response = requests.post(f'{baseUrl}/indexers?api-version=2023-10-01-Preview', headers=headers, data=json.dumps(indexerRequest))

if response.status_code == 200 or response.status_code == 201:
    print("Indexer created!")
else:
    print(response.text)
    raise Exception("Indexer request failed")