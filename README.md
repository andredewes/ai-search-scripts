# Useful HTTP scripts to manage Azure AI Search

This repository aims to provide some HTTP files (which you can use in Visual Studio Code) to quickly performs operations in Azure AI Search that are not exposed in the Azure Portal interface.

## Pre-requisites

- Visual Studio code with [REST Client](https://github.com/Huachao/vscode-restclient) extension installed 
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli)

## Usage

You can just open this repository in Visual Studio Code, find the script you want, and before running the requests make sure to replace all the variables in the beginning of the file (they start with ``@``) to fit your scenario.

Pay attention to the ``@azureAccessToken`` variable. To acquire an Azure access token to manage your AI Search instance, you need to run this AZ CLI command:

``az account get-access-token --scope https://search.azure.com/.default --subscription <<your-subscription-id>>``

Then copy the ``accessToken`` value from the output. It should begins with ``ey...``

## Available scripts

| Script                            | Description   |
| ---                               | ---           | 
| integrated-vectorization.http     |  This script replicates the same steps that happens when you run the [Integrated Vectorization](https://learn.microsoft.com/en-us/azure/search/search-get-started-portal-import-vectors) wizard. It is useful when you disable Public Access from the networking blade because the button from the portal is disabled in that scenario. It creates a Data Source, Index, Skillset and Indexer |
