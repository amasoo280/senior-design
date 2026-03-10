# Inference Profile Migration Summary

## Changes Made

The backend has been updated to use AWS Bedrock **inference profiles** instead of direct model IDs.

### Key Changes

1. **API Method**: Changed from `invoke_model()` to `invoke_inference_profile()`
2. **Parameter**: Changed from `modelId` to `inferenceProfileIdentifier`
3. **Credentials**: All AWS credentials now come exclusively from `settings` (no `os.getenv()` fallback)
4. **Configuration**: Inference profile ID comes from `settings.bedrock_model_id` (no hardcoded defaults)

### Updated Files

#### `backend/app/bedrock/client.py`

- ✅ Replaced `invoke_model()` with `invoke_inference_profile()`
- ✅ Changed `modelId` parameter to `inferenceProfileIdentifier`
- ✅ Removed all `os.getenv()` calls for AWS credentials
- ✅ Removed hardcoded model ID defaults
- ✅ Updated all docstrings and comments to reference "inference profile" instead of "model"
- ✅ Changed `model_id` attribute to `inference_profile_id`
- ✅ Updated error messages and return values

#### `backend/app/config.py`

- ✅ Already configured to read `BEDROCK_MODEL_ID` from `.env`
- ✅ No hardcoded model IDs remain
- ✅ Settings properly handle inference profile ID

## Configuration

### Required `.env` Variables

```env
# AWS Credentials (REQUIRED)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Inference Profile ID (REQUIRED)
# This should be your inference profile identifier, not a model ID
BEDROCK_MODEL_ID=your-inference-profile-id
```

### Important Notes

1. **`BEDROCK_MODEL_ID` now contains the inference profile identifier**, not a model ID
2. **No fallback to environment variables** - all credentials must be in `.env` file
3. **No hardcoded defaults** - the system will fail with a clear error if inference profile ID is missing

## API Changes

### Before (Model ID)
```python
response = self.client.invoke_model(
    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
    body=json.dumps(body),
    ...
)
```

### After (Inference Profile)
```python
response = self.client.invoke_inference_profile(
    inferenceProfileIdentifier=self.inference_profile_id,
    body=json.dumps(body),
    ...
)
```

## Error Handling

The system now provides clear error messages if:
- Inference profile ID is missing
- AWS credentials are missing
- AWS region is missing

All errors will guide users to set the appropriate `.env` variables.

## Testing

To test the changes:

1. **Set your inference profile ID in `.env`:**
   ```env
   BEDROCK_MODEL_ID=your-inference-profile-id
   ```

2. **Verify credentials are set:**
   ```powershell
   cd backend
   python -c "from app.config import settings; print(f'Profile ID: {settings.bedrock_model_id}'); print(f'Region: {settings.aws_region}')"
   ```

3. **Test Bedrock client initialization:**
   ```powershell
   python -c "from app.bedrock.client import BedrockClient; client = BedrockClient(); print('✅ Client initialized')"
   ```

## Migration Checklist

- [x] Replace `invoke_model` with `invoke_inference_profile`
- [x] Replace `modelId` with `inferenceProfileIdentifier`
- [x] Remove `os.getenv()` for AWS credentials
- [x] Remove hardcoded model IDs
- [x] Update all docstrings and comments
- [x] Update error messages
- [x] Update return values (changed `model_id` to `inference_profile_id`)
- [x] Ensure full compatibility with `config.py`

## Backward Compatibility

⚠️ **Breaking Change**: This is a breaking change. Users must:
1. Update their `.env` file to use inference profile IDs instead of model IDs
2. Ensure all AWS credentials are in `.env` (no environment variable fallback)

## Next Steps

1. Update your `.env` file with the inference profile identifier
2. Test the `/ask` endpoint
3. Verify AWS Bedrock inference profile access is enabled

