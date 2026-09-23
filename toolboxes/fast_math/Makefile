# Compilación del toolbox de cálculo rápido.
#
# Este Makefile genera una biblioteca compartida llamada fast_math.so a partir de
# fast_math.cpp. La librería puede ser cargada por Python o por otros módulos que
# necesiten funciones nativas con mejor rendimiento que el código Python puro.

all: fast_math.so

fast_math.so: fast_math.cpp
	g++ -shared -fPIC fast_math.cpp -o fast_math.so

clean:
	rm -f fast_math.so