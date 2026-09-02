#!/usr/bin/env python3

import argparse
import os
from pathlib import Path


def _fila_en_bytes(fila: int, cols: int) -> bytearray:
   
    bytes_por_fila = (cols + 7) // 8
    fila_bytes = bytearray(bytes_por_fila)
    full_bytes = cols // 8
    patron = b"\x55" if fila % 2 == 0 else b"\xAA"

    if full_bytes:
        fila_bytes[:full_bytes] = patron * full_bytes

    restante = cols % 8
    if restante:
        valor = 0
        for pos in range(restante):
            columna = full_bytes * 8 + pos
            if (fila + columna) % 2 == 1:
                valor |= 1 << (7 - pos)
        fila_bytes[full_bytes] = valor

    return fila_bytes


def generar_matriz_binaria(rows: int, cols: int, output: str) -> None:

    path = Path(output)
    bytes_por_fila = (cols + 7) // 8

    with path.open("wb") as archivo:
        archivo.write(rows.to_bytes(8, byteorder="little", signed=False))
        archivo.write(cols.to_bytes(8, byteorder="little", signed=False))

        for fila in range(rows):
            archivo.write(_fila_en_bytes(fila, cols))

    print(f"Archivo generado: {path}")
    print(f"Filas: {rows}")
    print(f"Columnas: {cols}")
    print(f"Tamanio estimado: {((rows * bytes_por_fila) + 16) / (1024 ** 2):.2f} MB")


def validar_matriz_binaria(path: str) -> None:

    file_size = os.path.getsize(path)
    with open(path, "rb") as archivo:
        filas = int.from_bytes(archivo.read(8), byteorder="little", signed=False)
        columnas = int.from_bytes(archivo.read(8), byteorder="little", signed=False)

    bytes_por_fila = (columnas + 7) // 8
    datos = file_size - 16
    if datos % bytes_por_fila != 0:
        raise ValueError("El archivo no tiene una estructura consistente.")

    filas_detectadas = datos // bytes_por_fila
    if filas_detectadas != filas:
        raise ValueError(f"Se esperaban {filas} filas pero se detectaron {filas_detectadas}.")

    print(f"Dimensiones verificadas: {filas} x {columnas}")
    print(f"Filas reales detectadas: {filas_detectadas}")
    print(f"Total de elementos: {filas * columnas}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera una matriz booleana compacta y valida sus dimensiones.")
    parser.add_argument("--rows", type=int, default=100000, help="Numero de filas")
    parser.add_argument("--cols", type=int, default=100000, help="Numero de columnas")
    parser.add_argument("--output", type=str, default="matriz_100000x100000.bin", help="Ruta del archivo binario")
    args = parser.parse_args()

    generar_matriz_binaria(args.rows, args.cols, args.output)
    validar_matriz_binaria(args.output)


if __name__ == "__main__":
    main()
