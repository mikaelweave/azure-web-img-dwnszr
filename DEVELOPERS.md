# Developers

## Debugging

**Prerequisites**
- Ensure you have `StorageAccountConnectionString` set in your `.env` file. This can be be found in the *Access Keys* blade of your test storage account.
- Azure Function Core Tools installed https://github.com/Azure/azure-functions-core-tools

**Start debugging**
The easiest way to begin debugging is to use the included *Debug Python Function* VSCode configuration. Once the function is running locally, you can send a sample request using the below `curl` command. In the command, the subject is `/blobServices/default/containers/testcontainer/blobs/testfile.jpg`. If you create a conatiner in your test storage account named `testcontainer` and upload an image named `testfile.jpg`, then your code will attemp to process this file while debugging locally.
```
curl --header "Content-Type: application/json" \
     --header "aeg-event-type: Notification" \
     http://localhost:7071/runtime/webhooks/EventGrid?functionName=src \
     --data-binary @- << EOF
[{
    "topic": "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/Storage/providers/Microsoft.Storage/storageAccounts/testStorageAccount",
    "subject": "/blobServices/default/containers/testcontainer/blobs/testfile.jpg",
    "eventType": "Microsoft.Storage.BlobCreated",
    "eventTime": "2020-03-28T16:15:48.647861394Z",
    "id": "00000000-0000-0000-0000-000000000000",
    "data": {
      "api": "PutBlockList",
      "clientRequestId": "00000000-0000-0000-0000-000000000000",
      "requestId": "00000000-0000-0000-0000-000000000000",
      "eTag": "0x8D4BCC2E4835CD0",
      "contentType": "text/plain",
      "contentLength": 524288,
      "blobType": "BlockBlob",
      "url": "https://example.blob.core.windows.net/testcontainer/testfile.jpg",
      "sequencer": "00000000000004420000000000028963",
      "storageDiagnostics": {
        "batchId": "00000000-0000-0000-0000-000000000000"
      }
    },
    "dataVersion": "",
    "metadataVersion": "1"
}]
EOF
```

For more information about debugging, look [here].(https://docs.microsoft.com/en-us/azure/azure-functions/functions-debug-event-grid-trigger-local)

## Tests

Testing is accomplished using *tox*. NOTE: End-to-end testing require the proper environment variables to be set. Please setup `.env` in the format of `.env.sample` first.

*Linting*: `tox -e lint`
*Unit Tests*: `tox "tests/unit"`
*End-to-end Tests*: `tox "tests/e2e"`