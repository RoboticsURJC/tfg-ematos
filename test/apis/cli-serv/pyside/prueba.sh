for i in {1..5}; do
    echo "Ejecucion $i ..."
    python3 latency_test.py
    sleep 10
done
