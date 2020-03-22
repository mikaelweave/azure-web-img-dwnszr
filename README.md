# Azure Image Resizer

## Overview
Why another Azure Function Image resizer? This one was written in Python so we can use the lovely Pillow library.

## Debugging
Add local config in local.setting.json
```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "{AzureWebJobsStorage}",
    "ImageSizes": "480,768,1200,1400,1700,2000,2436"
  }
}
```
AzureWebJobsStorage looks like "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName={storage account name};AccountKey={storage account key}"

Start debugging
```
func host start
```

Send request data:
```
event='[ {"id": "'"$RANDOM"'", "eventType": "recordInserted", "subject": "myapp/vehicles/motorcycles", "eventTime": "'`date +%Y-%m-%dT%H:%M:%S%z`'", "data":{ "make": "Ducati", "model": "Monster"},"dataVersion": "1.0"} ]'

curl --header "Content-Type: application/json" --request POST \
    --data $event http://localhost:7071/runtime/webhooks/EventGrid?functionName=AzureImageSizerSrcset
```

For more information about debugging, look [here].(https://docs.microsoft.com/en-us/azure/azure-functions/functions-debug-event-grid-trigger-local)

## Building and publishing
```
func pack --build-native-deps --python
func azure functionapp publish <function_name>
```