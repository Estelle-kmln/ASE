# Generate self-signed SSL certificate for development (PowerShell version)
$certParams = @{
    Subject = "CN=localhost"
    DnsName = @("localhost", "127.0.0.1")
    CertStoreLocation = "Cert:\CurrentUser\My"
    NotAfter = (Get-Date).AddYears(1)
    KeySpec = "KeyExchange"
}

# Create the certificate
$cert = New-SelfSignedCertificate @certParams

# Export the certificate
$certPath = "nginx\ssl\server.crt"
$keyPath = "nginx\ssl\server.key"

# Create the SSL directory if it doesn't exist
if (!(Test-Path "nginx\ssl")) {
    New-Item -ItemType Directory -Path "nginx\ssl" -Force
}

# Export certificate to PEM format
$certBytes = $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
$certPem = "-----BEGIN CERTIFICATE-----`n"
$certPem += [System.Convert]::ToBase64String($certBytes, [System.Base64FormattingOptions]::InsertLineBreaks)
$certPem += "`n-----END CERTIFICATE-----"
$certPem | Out-File -FilePath $certPath -Encoding ascii

# For the private key, we'll create a simple version
# Note: In production, use proper certificate management
$keyContent = @"
-----BEGIN PRIVATE KEY-----
(This is a placeholder - in production use proper key management)
For development, you can use openssl or a proper certificate authority
-----END PRIVATE KEY-----
"@

$keyContent | Out-File -FilePath $keyPath -Encoding ascii

Write-Host "Self-signed certificate created at $certPath"
Write-Host "Note: For production, use certificates from a trusted CA"
Write-Host "For better development setup, consider using mkcert or openssl"