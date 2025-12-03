#!/bin/bash
# Setup script for SAC preset
# This preset creates configuration files and systemd service units

# Create apps directory
mkdir -p /apps

# Create configuration files and systemd units for services
create_service_config() {
    local service_name=$1
    local server_port=$2
    
    echo "Creating configuration for service: $service_name"
    
    # Create service directory
    mkdir -p /apps/$service_name
    
    # Create Development JSON configuration
    cat > /apps/$service_name/appsettings.Development.json <<EOF
{
  "ServiceName": "$service_name",
  "Environment": "Development",
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost;Database=${service_name}_dev;User Id=dev_user;Password=dev_password;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Debug",
      "System": "Information",
      "Microsoft": "Information"
    }
  },
  "AllowedHosts": "*",
  "ServerPort": $server_port,
  "MaxConnections": $(( RANDOM % 100 + 10 )),
  "Timeout": $(( RANDOM % 30 + 5 )),
  "CorsSettings": {
    "AllowedOrigins": [
      "http://localhost:2221",
      "http://localhost:2222",
      "http://localhost:2223"
    ],
    "AllowedMethods": ["GET", "POST", "PUT", "DELETE"],
    "AllowedHeaders": ["Content-Type", "Authorization"]
  },
  "CacheEnabled": $(( RANDOM % 2 )),
  "CacheTTL": $(( RANDOM % 3600 + 60 )),
  "DebugMode": true,
  "ApiVersion": "1.0.$(( RANDOM % 10 ))",
  "ApiKey": "$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)"
}
EOF

    # Create Production JSON configuration
    cat > /apps/$service_name/appsettings.Production.json <<EOF
{
  "ServiceName": "$service_name",
  "Environment": "Production",
  "ConnectionStrings": {
    "DefaultConnection": "Server=prod-db;Database=${service_name};User Id=prod_user;Password=prod_password;"
  },
  "Logging": {
    "LogLevel": {
      "Default": "Warning",
      "System": "Error",
      "Microsoft": "Error"
    }
  },
  "AllowedHosts": "*",
  "ServerPort": $server_port,
  "MaxConnections": $(( RANDOM % 500 + 100 )),
  "Timeout": $(( RANDOM % 15 + 15 )),
  "CorsSettings": {
    "AllowedOrigins": [
      "https://api.example.com",
      "https://admin.example.com",
      "https://app.example.com"
    ],
    "AllowedMethods": ["GET", "POST", "PUT", "DELETE"],
    "AllowedHeaders": ["Content-Type", "Authorization", "X-API-Key"]
  },
  "CacheEnabled": true,
  "CacheTTL": $(( RANDOM % 7200 + 3600 )),
  "DebugMode": false,
  "ApiVersion": "1.0.$(( RANDOM % 10 ))",
  "ApiKey": "$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)"
}
EOF

    # Create systemd service unit file
    cat > /etc/systemd/system/$service_name.service <<EOF
[Unit]
Description=$service_name Service
After=network.target

[Service]
Type=simple
User=nobody
WorkingDirectory=/apps/$service_name
ExecStart=/usr/bin/dotnet /apps/$service_name/$service_name.dll
Restart=always
RestartSec=10
Environment="ASPNETCORE_ENVIRONMENT=Production"
Environment="DOTNET_PRINT_TELEMETRY_MESSAGE=false"

[Install]
WantedBy=multi-user.target
EOF

    echo "Configuration for $service_name created successfully"
}

# Create services and configs
create_service_config "app_t1" 8001
create_service_config "app_t2" 8002
create_service_config "app_t3" 8003

# Create a script to list all services
cat > /apps/list_services.sh <<EOF
#!/bin/bash
# Script to list all service configurations

echo "Available services:"
for service in /apps/app_t*; do
    if [ -d "\$service" ]; then
        service_name=\$(basename \$service)
        echo "- \$service_name"
        echo "  Configuration files:"
        ls -la \$service/*.json
        echo "  Systemd unit:"
        ls -la /etc/systemd/system/\$service_name.service
        echo ""
    fi
done
EOF

chmod +x /apps/list_services.sh

echo "SAC preset has been installed successfully."
echo "Configuration files are in /apps directory."
echo "Systemd service units are in /etc/systemd/system/."
echo "To list all services and configs, run: /apps/list_services.sh" 