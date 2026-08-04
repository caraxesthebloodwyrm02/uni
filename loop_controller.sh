#!/usr/bin/env bash
# ==============================================================================
# Script Name: loop_controller.sh
# Description: Controller logic for validation loops including weighting and bias calculations
# Scope/Safety: Safe / Reads process lists and logs bias/weights to /tmp
# Dependencies: pgrep, kill, sleep, grep, awk, bc, ps, tee
# ==============================================================================

# Configuration
LOG_FILE="/tmp/mangrove_loop_control.log"
WEIGHT_FILE="/tmp/mangrove_loop_weights.json"
BIAS_LOG="/tmp/mangrove_bias_accumulation.log"

# Check dependencies
for cmd in pgrep kill sleep grep awk bc ps tee; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: Required dependency '$cmd' is not installed or not in PATH." >&2
        if [ "$0" != "$BASH_SOURCE" ]; then
            return 1
        else
            exit 1
        fi
    fi
done

# Initialize log files
touch "$LOG_FILE" "$WEIGHT_FILE" "$BIAS_LOG"

# Function to log messages with timestamp
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to top (stop) a running loop by name
top_loop() {
    local loop_name="$1"
    local pids=$(pgrep -f "$loop_name")

    if [ -z "$pids" ]; then
        log_message "No running processes found for '$loop_name'"
        return 1
    fi

    log_message "Stopping processes for '$loop_name': $pids"
    kill $pids 2>/dev/null

    # Wait a moment for graceful shutdown
    sleep 1

    # Force kill if still running
    local remaining=$(pgrep -f "$loop_name")
    if [ -n "$remaining" ]; then
        log_message "Force killing remaining processes: $remaining"
        kill -9 $remaining 2>/dev/null
    fi

    log_message "Loop '$loop_name' stopped"
    return 0
}

# Function to apply weight to steer the process
apply_weight() {
    local process_name="$1"
    local weight="$2"  # Weight value (typically 0.1 to 2.0)

    # Validate weight parameter
    if ! [[ "$weight" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        log_message "Error: Weight must be a number"
        return 1
    fi

    # Store weight in JSON format
    if [ ! -f "$WEIGHT_FILE" ] || [ ! -s "$WEIGHT_FILE" ]; then
        echo "{}" > "$WEIGHT_FILE"
    fi

    # Update weight for the process
    if command -v jq >/dev/null 2>&1; then
        jq --arg name "$process_name" --argjson weight "$weight" \
           '. + {($name): $weight}' "$WEIGHT_FILE" > "${WEIGHT_FILE}.tmp" && \
        mv "${WEIGHT_FILE}.tmp" "$WEIGHT_FILE"
    else
        # Fallback without jq
        echo "{\"$process_name\": $weight}" > "$WEIGHT_FILE"
    fi

    log_message "Applied weight $weight to process '$process_name'"
    return 0
}

# Function to cumulatively gather biases from process output
gather_bias() {
    local process_name="$1"
    local output_line="$2"

    # Simple bias detection - look for certain patterns
    # In a real implementation, this could be more sophisticated
    local bias_score=0

    # Check for error indicators
    if echo "$output_line" | grep -qi "error\|fail\|warn"; then
        bias_score=$((bias_score - 1))
    fi

    # Check for success indicators
    if echo "$output_line" | grep -qi "success\|pass\|ok"; then
        bias_score=$((bias_score + 1))
    fi

    # Log the bias observation
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $process_id: $bias_score - $output_line" >> "$BIAS_LOG"

    # Calculate cumulative bias for this process
    local total_bias=0
    count=0
    while IFS= read -r line; do
        if [[ "$line" == *"$process_name:"* ]]; then
            value=$(echo "$line" | awk -F': ' '{print $2}' | awk '{print $1}')
            total_bias=$((total_bias + value))
            count=$((count + 1))
        fi
    done < "$BIAS_LOG"

    if [ $count -gt 0 ]; then
        local avg_bias=$(echo "scale=2; $total_bias / $count" | bc)
        log_message "Cumulative bias for '$process_name': $avg_bias (based on $count observations)"
        echo "$avg_bias"
    else
        echo "0"
    fi
}

# Function to get current weight for a process
get_weight() {
    local process_name="$1"

    if [ ! -f "$WEIGHT_FILE" ] || [ ! -s "$WEIGHT_FILE" ]; then
        echo "1.0"  # Default weight
        return 0
    fi

    if command -v jq >/dev/null 2>&1; then
        jq -r ".$process_name // 1.0" "$WEIGHT_FILE"
    else
        # Simple fallback - just return default
        echo "1.0"
    fi
}

# Function to show current status
show_status() {
    echo "=== Loop Controller Status ==="
    echo "Log file: $LOG_FILE"
    echo "Weight file: $WEIGHT_FILE"
    echo "Bias log: $BIAS_LOG"
    echo ""

    if [ -f "$WEIGHT_FILE" ] && [ -s "$WEIGHT_FILE" ]; then
        echo "Current weights:"
        if command -v jq >/dev/null 2>&1; then
            jq 'to_entries|map("  \(.key): \(.value)")[]' "$WEIGHT_FILE"
        else
            cat "$WEIGHT_FILE"
        fi
    else
        echo "No weights configured"
    fi

    echo ""
    echo "Recent bias measurements (last 5):"
    tail -5 "$BIAS_LOG" 2>/dev/null || echo "No bias data yet"

    echo ""
    echo "Active processes matching our patterns:"
    ps aux | grep -E "(validate-workspace|warmup_apparat|loop_controller)" | grep -v grep || echo "None"
}

# Helper function to run a process with weighting
run_with_weight() {
    local process_name="$1"
    shift
    local command="$*"

    local weight=$(get_weight "$process_name")
    log_message "Running '$process_name' with weight $weight: $command"

    # In a real implementation, we might adjust nice/ionice based on weight
    # For now, we just log it and run the command
    eval "$command" 2>&1 | while read -r line; do
        echo "$line"
        gather_bias "$process_name" "$line"
    done
}

# If called directly, show help
if [ "$0" = "$BASH_SOURCE" ]; then
    echo "Usage: source $0  # To load functions into your shell"
    echo "Available functions:"
    echo "  top_loop <process_name>     - Stop a running loop"
    echo "  apply_weight <name> <weight> - Apply weight to steer a process"
    echo "  get_weight <name>           - Get current weight for a process"
    echo "  gather_bias <name> <line>   - Process a line for bias tracking"
    echo "  show_status                 - Show current status"
    echo "  run_with_weight <name> <cmd> - Run command with weighting"
fi