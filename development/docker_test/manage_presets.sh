#!/bin/bash
# Interactive script to manage test environment presets

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed. Please install jq first."
    exit 1
fi

CONFIG_FILE="presets.json"

# Function to display menu
show_menu() {
    clear
    echo "=== Mancer Test Environment Preset Manager ==="
    echo "1. List available presets"
    echo "2. Configure container presets"
    echo "3. Create new preset"
    echo "4. Remove preset"
    echo "5. Enable/Disable preset"
    echo "6. Save and exit"
    echo "7. Exit without saving"
    echo "==========================================="
    echo -n "Select an option: "
}

# Function to list presets
list_presets() {
    clear
    echo "Available Presets:"
    echo "-----------------"
    jq -r '.presets | to_entries[] | "\(.key): \(.value.description) (Enabled: \(.value.enabled))"' "$CONFIG_FILE"
    echo
    read -p "Press Enter to continue..."
}

# Function to configure container presets
configure_containers() {
    while true; do
        clear
        echo "Configure Container Presets"
        echo "-------------------------"
        jq -r '.containers | to_entries[] | "\(.key): \(.value.preset) (Enabled: \(.value.enabled))"' "$CONFIG_FILE"
        echo
        echo "1. Change container preset"
        echo "2. Enable/Disable container"
        echo "3. Back to main menu"
        echo -n "Select an option: "
        read option

        case $option in
            1)
                echo -n "Enter container name (e.g., mancer-test-1): "
                read container
                echo -n "Enter preset name: "
                read preset
                
                # Validate preset exists
                if ! jq -e ".presets.\"$preset\"" "$CONFIG_FILE" > /dev/null; then
                    echo "Error: Preset '$preset' does not exist"
                    read -p "Press Enter to continue..."
                    continue
                fi
                
                # Update config
                tmp_file=$(mktemp)
                jq --arg c "$container" --arg p "$preset" '.containers[$c].preset = $p' "$CONFIG_FILE" > "$tmp_file"
                mv "$tmp_file" "$CONFIG_FILE"
                ;;
            2)
                echo -n "Enter container name: "
                read container
                current_state=$(jq -r ".containers.\"$container\".enabled" "$CONFIG_FILE")
                new_state=$([ "$current_state" = "true" ] && echo "false" || echo "true")
                
                tmp_file=$(mktemp)
                jq --arg c "$container" --arg s "$new_state" '.containers[$c].enabled = ($s == "true")' "$CONFIG_FILE" > "$tmp_file"
                mv "$tmp_file" "$CONFIG_FILE"
                ;;
            3)
                break
                ;;
            *)
                echo "Invalid option"
                ;;
        esac
    done
}

# Function to create new preset
create_preset() {
    clear
    echo "Create New Preset"
    echo "----------------"
    echo -n "Enter preset name: "
    read preset_name
    
    if [ -z "$preset_name" ]; then
        echo "Error: Preset name cannot be empty"
        read -p "Press Enter to continue..."
        return
    fi
    
    if jq -e ".presets.\"$preset_name\"" "$CONFIG_FILE" > /dev/null; then
        echo "Error: Preset '$preset_name' already exists"
        read -p "Press Enter to continue..."
        return
    fi
    
    echo -n "Enter preset description: "
    read description
    
    # Create preset directory and files
    mkdir -p "presets/$preset_name"
    
    # Create setup script
    cat > "presets/$preset_name/setup-$preset_name.sh" << EOF
#!/bin/bash
# Setup script for preset: $preset_name

echo "Setting up preset: $preset_name"

# Add your setup commands here

echo "Preset setup completed!"
EOF
    
    # Create README
    cat > "presets/$preset_name/README.md" << EOF
# $preset_name Preset

$description

## Installed Components
- Add components here

## Usage
Add usage instructions here
EOF
    
    chmod +x "presets/$preset_name/setup-$preset_name.sh"
    
    # Update config
    tmp_file=$(mktemp)
    jq --arg n "$preset_name" --arg d "$description" '.presets[$n] = {"description": $d, "enabled": true}' "$CONFIG_FILE" > "$tmp_file"
    mv "$tmp_file" "$CONFIG_FILE"
    
    echo "Preset created successfully!"
    read -p "Press Enter to continue..."
}

# Function to remove preset
remove_preset() {
    clear
    echo "Remove Preset"
    echo "------------"
    echo -n "Enter preset name to remove: "
    read preset_name
    
    if [ "$preset_name" = "none" ]; then
        echo "Error: Cannot remove the 'none' preset"
        read -p "Press Enter to continue..."
        return
    fi
    
    if ! jq -e ".presets.\"$preset_name\"" "$CONFIG_FILE" > /dev/null; then
        echo "Error: Preset '$preset_name' does not exist"
        read -p "Press Enter to continue..."
        return
    fi
    
    # Check if preset is in use
    if jq -e ".containers[] | select(.preset == \"$preset_name\")" "$CONFIG_FILE" > /dev/null; then
        echo "Error: Preset is in use by one or more containers"
        read -p "Press Enter to continue..."
        return
    fi
    
    # Remove preset files
    rm -rf "presets/$preset_name"
    
    # Update config
    tmp_file=$(mktemp)
    jq --arg n "$preset_name" 'del(.presets[$n])' "$CONFIG_FILE" > "$tmp_file"
    mv "$tmp_file" "$CONFIG_FILE"
    
    echo "Preset removed successfully!"
    read -p "Press Enter to continue..."
}

# Function to enable/disable preset
toggle_preset() {
    clear
    echo "Enable/Disable Preset"
    echo "-------------------"
    echo -n "Enter preset name: "
    read preset_name
    
    if ! jq -e ".presets.\"$preset_name\"" "$CONFIG_FILE" > /dev/null; then
        echo "Error: Preset '$preset_name' does not exist"
        read -p "Press Enter to continue..."
        return
    fi
    
    current_state=$(jq -r ".presets.\"$preset_name\".enabled" "$CONFIG_FILE")
    new_state=$([ "$current_state" = "true" ] && echo "false" || echo "true")
    
    tmp_file=$(mktemp)
    jq --arg n "$preset_name" --arg s "$new_state" '.presets[$n].enabled = ($s == "true")' "$CONFIG_FILE" > "$tmp_file"
    mv "$tmp_file" "$CONFIG_FILE"
    
    echo "Preset $preset_name is now $(if [ "$new_state" = "true" ]; then echo "enabled"; else echo "disabled"; fi)"
    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    show_menu
    read option
    
    case $option in
        1) list_presets ;;
        2) configure_containers ;;
        3) create_preset ;;
        4) remove_preset ;;
        5) toggle_preset ;;
        6) 
            echo "Configuration saved"
            exit 0
            ;;
        7) 
            echo "Exiting without saving"
            exit 0
            ;;
        *)
            echo "Invalid option"
            read -p "Press Enter to continue..."
            ;;
    esac
done 