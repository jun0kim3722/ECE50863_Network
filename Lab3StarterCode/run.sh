#!/bin/bash

# === CONFIGURATION ===
TEST_DIR="tests"
START_ID=1
END_ID=6

# === START ===
for STUDENT_ID in $(seq $START_ID $END_ID); do
    OUTPUT_FILE="results/student${STUDENT_ID}.log"
    echo "Running tests for student${STUDENT_ID}.py" > "$OUTPUT_FILE"
    echo "========================================================================================================================" >> "$OUTPUT_FILE"

    for test_file in ${TEST_DIR}/*.ini; do
        echo "Running test: $test_file" | tee -a "$OUTPUT_FILE"
        python3 simulator.py "$test_file" "$STUDENT_ID" -v | tail -n 6 >> "$OUTPUT_FILE"
    done
done

echo "Done."
