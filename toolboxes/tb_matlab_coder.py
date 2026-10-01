import os
from core.toolbox_manager import MatpyLabToolbox


class MatlabCoderToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "MATLAB Coder"

    @property
    def description(self):
        return "Convierte algoritmos a lenguaje C/C++ generando automáticamente los archivos fuente y Makefiles para hardware."

    def export_functions(self):
        def matlab_codegen(func_name, args_list, expression):
            """
            Genera código C y un Makefile para una expresión o algoritmo.
            Uso: codegen('calc_pid', ['float err', 'float kp'], 'return err * kp;')
            """
            # Crear carpeta de salida en la raíz del proyecto
            out_dir = "codegen_out"
            os.makedirs(out_dir, exist_ok=True)

            c_file = os.path.join(out_dir, f"{func_name}.c")
            h_file = os.path.join(out_dir, f"{func_name}.h")
            make_file = os.path.join(out_dir, "Makefile")

            # Generar firma de la función
            args_str = ", ".join(args_list)
            firma = f"float {func_name}({args_str})"

            # 1. Generar archivo Header (.h)
            with open(h_file, 'w', encoding='utf-8') as f:
                f.write(f"#ifndef {func_name.upper()}_H\n")
                f.write(f"#define {func_name.upper()}_H\n\n")
                f.write(f"{firma};\n\n")
                f.write(f"#endif\n")

            # 2. Generar archivo Source (.c)
            with open(c_file, 'w', encoding='utf-8') as f:
                f.write(f'#include "{func_name}.h"\n\n')
                f.write(f"{firma} {{\n")
                f.write(f"    {expression}\n")
                f.write(f"}}\n")

            # 3. Generar Makefile dedicado para mingw32-make
            with open(make_file, 'w', encoding='utf-8') as f:
                f.write(f"CC = gcc\n")
                f.write(f"CFLAGS = -Wall -O2\n\n")
                f.write(f"all: {func_name}.o\n\n")
                f.write(f"{func_name}.o: {func_name}.c\n")
                f.write(f"\t$(CC) $(CFLAGS) -c {func_name}.c -o {func_name}.o\n\n")
                f.write(f"clean:\n")
                f.write(f"\tdel *.o\n")

            print(f"✅ Código C generado exitosamente en la carpeta '{out_dir}/'")
            print(f"   📄 {func_name}.c")
            print(f"   📄 {func_name}.h")
            print(f"   ⚙️  Makefile (listo para mingw32-make)")

            return True

        return {
            'codegen': matlab_codegen
        }
