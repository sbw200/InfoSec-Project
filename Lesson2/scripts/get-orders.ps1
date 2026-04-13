param(
    [string]$ApiUrl = $env:API_URL,
    [Parameter(Mandatory = $true)]
    [string]$Token
)

if (-not $ApiUrl) {
    throw "API_URL is not set."
}

$response = Invoke-RestMethod -Uri $ApiUrl -Method Post -Headers @{
    "Content-Type"  = "application/json"
    "Authorization" = $Token
} -Body (@{ action = "orders" } | ConvertTo-Json -Compress)

$response | ConvertTo-Json -Depth 10
