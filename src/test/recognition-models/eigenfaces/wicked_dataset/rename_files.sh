#!/bin/bash

# Verificar que se proporcione un argumento
if [ -z "$1" ]; then
    echo "Uso: $0 <nombre_base>"
    exit 1
fi

# Nombre base pasado como argumento
base_name="$1"

# Inicializar contador
counter=1

# Renombrar archivos en el directorio actual
for file in *; do
    # Verificar que sea un archivo
    if [ -f "$file" ]; then
        mv "$file" "${base_name}_$(printf "%03d" $counter).jpg"
        counter=$((counter + 1))
    fi
done

echo "Renombrado completado con base: $base_name"

