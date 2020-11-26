#!/bin/bash

############################
# Example deployment script
############################

# Will deploy the latest release from Github. If developing locally, please look at the comment on line 41

# Required dependencies:
# Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest

# First ensure you have a proper .env file (in the same format as .env.sample) with the deployment values filled out
# Load settings from .env file
export $(grep -v '^#' .env | xargs)

# Login
az login
az account set --subscription $SUBSCRIPTION_ID

# Create Resource Group
az group create -l $LOCATION -n $RESOURCE_GROUP_NAME
az configure --defaults group=$RESOURCE_GROUP_NAME location=$LOCATION

# Create Image Storage Account
storage=$(az storage account create -n $STORAGE_ACCOUNT_NAME --sku Standard_RAGRS)

# Create Function
az functionapp create --consumption-plan-location $LOCATION \
    --runtime python --runtime-version 3.8 --functions-version 3 \
    --name $FUNCTION_APP_NAME --storage-account $STORAGE_ACCOUNT_NAME \
    --os-type linux

# Get latest release
curl -s https://api.github.com/repos/mikaelweave/azure_web_img_dwnszr/releases/latest | jq '.assets[0].browser_download_url' | xargs wget -O azure_web_img_dwnszr.zip

# Deploy function 
# Will currently throw error but deploy successfully - https://github.com/Azure/azure-cli/issues/12513
az functionapp deployment source config-zip --name $RESOURCE_NAME \
    --src azure_web_img_dwnszr.zip

# If you are developing locally, run this instead if lines 33-39.
# func azure functionapp publish $FUNCTION_APP_NAME

# Setup settings for function
# Resources for srcset - https://medium.com/hceverything/applying-srcset-choosing-the-right-sizes-for-responsive-images-at-different-breakpoints-a0433450a4a3
# Iphone - https://www.paintcodeapp.com/news/ultimate-guide-to-iphone-resolutions
az functionapp config appsettings set --name $FUNCTION_APP_NAME \
    --settings "ImageSizes=320,480,640,768,828,1024,1242,1366,1440,1600,1920,2280,2560"
az functionapp config appsettings set --name $FUNCTION_APP_NAME \
    --settings "StorageAccountConnectionString=$(az storage account show-connection-string --name $STORAGE_ACCOUNT_NAME --output tsv)"

# Create blob trigger
# May require preview version of the exenthub extension
# See https://github.com/Azure/azure-cli/issues/12092#issuecomment-584883771
function_id=$(az functionapp show --name $FUNCTION_APP_NAME --output tsv --query 'id')/functions/azure-web-img-dwnsizr
az eventgrid event-subscription create \
  --source-resource-id $(echo $storage | jq -r '.id') \
  --name $FUNCTION_APP_NAME_azure_web_img_dwnszr_function \
  --endpoint-type azurefunction \
  --endpoint $function_id \
  --included-event-types 'Microsoft.Storage.BlobCreated' \
  --advanced-filter subject StringEndsWith '.jpg' '.jpeg' 'png' \
  --advanced-filter subject StringContains '$web'

# Create action group for alerts
action_group_id=$(az monitor action-group create --action email admin $EMAIL --name EmailErrorsAzureWebImgDwnszr --output tsv --query id)

# Create alert on function failures
az monitor metrics alert create --name "Azure Web Img Dwnsizr Error" \
    --description "Alert when our Azure Web Img Dwnsizr function has an error" \
    --scopes "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP_NAME}/providers/microsoft.insights/components/${FUNCTION_APP_NAME}" \
    --condition "count requests/failed > 0" \
    --evaluation-frequency "15m" \
    --window-size "30m" \
    --action $action_group_id