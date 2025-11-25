# Google AI Studio Setup Guide

This guide explains how to set up Google AI Studio (Gemini API) integration for automatic bank statement processing.

## Overview

The bank statement upload endpoint automatically processes PDF files using Google AI Studio's Gemini API to extract transaction data. When you upload a bank statement, the system:

1. Saves the PDF file
2. Sends it to Google AI Studio for processing
3. Extracts transaction data (dates, amounts, descriptions, categories)
4. Returns structured JSON with all extracted transactions

## Prerequisites

- A Google account
- Access to Google AI Studio (<https://aistudio.google.com/>)

## Step 1: Get Your API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click on "Get API Key" or navigate to the API keys section
4. Create a new API key or use an existing one
5. Copy the API key (it will look like: `AIzaSy...`)

**Important:** Keep your API key secure and never commit it to version control.

## Step 2: Set the Environment Variable

### Windows (PowerShell)

```powershell
$env:GOOGLE_AI_API_KEY="your-api-key-here"
```

### Windows (Command Prompt)

```cmd
set GOOGLE_AI_API_KEY=your-api-key-here
```

### Linux/macOS

```bash
export GOOGLE_AI_API_KEY="your-api-key-here"
```

### Permanent Setup (Windows)

1. Open System Properties → Environment Variables
2. Add a new User variable:
   - Variable name: `GOOGLE_AI_API_KEY`
   - Variable value: `your-api-key-here`
3. Click OK and restart your terminal/IDE

### Permanent Setup (Linux/macOS)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export GOOGLE_AI_API_KEY="your-api-key-here"
```

Then reload:

```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Docker Setup

If using Docker, add to your `docker-compose.yaml`:

```yaml
services:
  api:
    environment:
      - GOOGLE_AI_API_KEY=${GOOGLE_AI_API_KEY}
```

And create a `.env` file in your project root:

```
GOOGLE_AI_API_KEY=your-api-key-here
```

## Step 3: Install Dependencies

Make sure you have installed the required Python package:

```bash
pip install -r requirements.txt
```

This will install `google-generativeai` along with other dependencies.

## Step 4: Verify Setup

1. Start your Django server:

   ```bash
   python manage.py runserver
   ```

2. Upload a bank statement PDF through the API endpoint:

   ```bash
   curl -X POST http://localhost:8000/bank-statements/upload/ \
     -F "pdf_file=@path/to/statement.pdf" \
     -F "user_id=your_username"
   ```

3. Check the response - it should include an `extracted_data` field with transactions.

## API Response Format

When a bank statement is successfully processed, the response includes:

```json
{
  "message": "Bank statement uploaded successfully",
  "file_details": {
    "id": 1,
    "filename": "statement.pdf",
    "file_size": 123456,
    "file_size_display": "120.6 KB",
    "upload_date": "2024-01-15T10:30:00Z",
    "processing_status": "completed"
  },
  "status": "success",
  "extracted_data": {
    "transactions": [
      {
        "date": "2024-01-15",
        "title": "Grocery Store Purchase",
        "amount": 125.50,
        "transaction_type": "Expense",
        "category": "Food"
      },
      {
        "date": "2024-01-16",
        "title": "Salary Deposit",
        "amount": 3000.00,
        "transaction_type": "Income",
        "category": "Salary"
      }
    ],
    "account_name": "Checking Account",
    "statement_period": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    },
    "processing_error": null
  }
}
```

## Processing Status

The `processing_status` field can have the following values:

- `pending`: File uploaded but not yet processed
- `processing`: Currently being processed by AI
- `completed`: Successfully processed (transactions extracted)
- `failed`: Processing failed (check `error_message` field)

## Error Handling

If AI processing fails, the upload will still succeed, but:

- `processing_status` will be set to `failed`
- `error_message` will contain the error details
- `extracted_data.processing_error` will contain the error message
- `extracted_data.transactions` will be an empty array

Common errors:

- **API key not configured**: Set the `GOOGLE_AI_API_KEY` environment variable
- **Invalid API key**: Verify your API key is correct
- **PDF parsing error**: The PDF might be corrupted or in an unsupported format
- **Rate limiting**: You may have exceeded API rate limits (check Google AI Studio quotas)

## Transaction Data Structure

Each extracted transaction contains:

- `date`: Transaction date in YYYY-MM-DD format
- `title`: Transaction description/merchant name
- `amount`: Transaction amount as a positive number
- `transaction_type`: Either "Income", "Expense", or "Transfer"
- `category`: Categorized transaction type (e.g., "Food", "Transport", "Salary")

## Using the Extracted Data

After uploading and processing, you can:

1. Review the extracted transactions in the response
2. Use the transaction data to create transactions via the `/transactions/create/` endpoint
3. Match transactions to existing accounts
4. Import transactions in bulk

## Testing

To test the integration without a real bank statement:

1. Create a simple PDF with transaction data
2. Upload it via the API
3. Check the `extracted_data` field in the response
4. Verify that transactions are correctly extracted

## Troubleshooting

### API Key Not Working

- Verify the key is set: `echo $GOOGLE_AI_API_KEY` (Linux/macOS) or `echo %GOOGLE_AI_API_KEY%` (Windows)
- Restart your Django server after setting the environment variable
- Check that the key is valid in Google AI Studio

### No Transactions Extracted

- The PDF might not contain recognizable transaction data
- The statement format might not be supported
- Check the `processing_error` field for details
- Try with a different bank statement format

### Processing Takes Too Long

- Large PDFs may take longer to process
- Check your internet connection
- Verify API quotas in Google AI Studio

## Security Notes

- Never commit your API key to version control
- Use environment variables for API keys
- Rotate your API key periodically
- Monitor API usage in Google AI Studio dashboard
- Set up API key restrictions in Google Cloud Console if needed

## Cost Considerations

Google AI Studio offers free tier usage with rate limits. Check the current pricing and quotas at:
<https://ai.google.dev/pricing>

## Support

For issues with:

- **Google AI Studio API**: Check [Google AI Studio Documentation](https://ai.google.dev/docs)
- **Integration issues**: Check server logs for error messages
- **Transaction extraction accuracy**: The AI model may need prompt tuning for specific bank formats
