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
AzureWebJobsStorage looks like `DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName={storage account name};AccountKey={storage account key}`

Start debugging
```
func host start
```

Send request data:
```
curl --header "Content-Type: application/json" \
     --header "aeg-event-type: Notification" \
     http://localhost:7071/runtime/webhooks/EventGrid?functionName=AzureImageSizerSrcset \
     --trace test.txt \
     --data-binary @- << EOF
[{
    "topic": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/Storage/providers/Microsoft.Storage/storageAccounts/testStorageAccount",
    "subject": "/blobServices/default/containers/testcontainer/blobs/testfile.txt",
    "eventType": "Microsoft.Storage.BlobCreated",
    "eventTime": "2020-03-28T16:15:48.647861394Z",
    "id": "831e1650-001e-001b-66ab-eeb76e069631",
    "data": {
      "api": "PutBlockList",
      "clientRequestId": "6d79dbfb-0e37-4fc4-981f-442c9ca65760",
      "requestId": "831e1650-001e-001b-66ab-eeb76e000000",
      "eTag": "0x8D4BCC2E4835CD0",
      "contentType": "text/plain",
      "contentLength": 524288,
      "blobType": "BlockBlob",
      "url": "https://example.blob.core.windows.net/testcontainer/testfile.txt",
      "sequencer": "00000000000004420000000000028963",
      "storageDiagnostics": {
        "batchId": "b68529f3-68cd-4744-baa4-3c0498ec19f0"
      }
    },
    "dataVersion": "",
    "metadataVersion": "1"
}]
EOF
```

For more information about debugging, look [here].(https://docs.microsoft.com/en-us/azure/azure-functions/functions-debug-event-grid-trigger-local)

## Building and publishing
```
func pack --build-native-deps --python
func azure functionapp publish <function_name>
```