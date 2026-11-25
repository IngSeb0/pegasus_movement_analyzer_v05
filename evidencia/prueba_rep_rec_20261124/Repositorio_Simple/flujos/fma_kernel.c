/* Carga de cómputo: N operaciones FMA seguidas.   Uso: ./fma_kernel --flops N
 *
 * fma(x, a, b) calcula x*a + b en UNA sola instrucción de la CPU (multiplicar y sumar
 * fusionados). Cuenta como 2 operaciones de punto flotante (FLOP), así que para N FLOP
 * se repite N/2 veces. Se compila con -mfma para que sea esa instrucción de hardware.
 * Cada vuelta usa el resultado de la anterior, así la CPU no puede saltarse trabajo. */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "uso: %s --flops N\n", argv[0]);
        return 2;
    }
    long long vueltas = atoll(argv[2]) / 2;
    double x = 0.25;
    for (long long i = 0; i < vueltas; i++)
        x = fma(x, 0.999999999999, 0.125);
    printf("%.17g\n", x);          /* imprimirlo evita que el compilador borre el bucle */
    return 0;
}
