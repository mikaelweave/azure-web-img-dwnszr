#1/bin/bash

############################
# Example deployment script
############################

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

# Create Storage Account
storage=$(az storage account create -n $RESOURCE_NAME --sku Standard_RAGRS)

# Create Function
az functionapp create --consumption-plan-location $LOCATION \
    --runtime python --runtime-version 3.8 --functions-version 3 \
    --name $RESOURCE_NAME --storage-account $RESOURCE_NAME \
    --os-type linux

# Package local version of function
# TODO: Replace with pull of github release
mkdir -p .tmp/azure-web-img-dwnszr
cp -r host.json local.settings.json .tmp/
pip install  --target=".tmp/.python_packages/lib/site-packages"  -r requirements.txt
cp src/* .tmp/azure-web-img-dwnszr/
cd .tmp; zip -r ../azure-web-img-dwnszr.zip .*; cd ..
rm -rf .tmp

# Deploy function 
# Will currently throw error but deploy successfully - https://github.com/Azure/azure-cli/issues/12513
az functionapp deployment source config-zip --name $RESOURCE_NAME \
    --src azure-web-img-dwnszr.zip

# Setup settings for function
az functionapp config appsettings set --name $RESOURCE_NAME \
    --settings "ImageSizes=480,768,1200,1400,1700,2000,2436"

# Create blob trigger
# May require preview version of the exenthub extension
# See https://github.com/Azure/azure-cli/issues/12092#issuecomment-584883771
function_id=$(az functionapp show --name $RESOURCE_NAME --output tsv --query 'id')/functions/azure-web-img-dwnsizr
az eventgrid event-subscription create \
  --source-resource-id $(echo $storage | jq -r '.id') \
  --name $RESOURCE_NAME-azure-web-img-dwnszr-function \
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
    --scopes "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP_NAME}/providers/microsoft.insights/components/${RESOURCE_NAME}" \
    --condition "count requests/failed > 0" \
    --evaluation-frequency "15m" \
    --window-size "30m" \
    --action $action_group_id