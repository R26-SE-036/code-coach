import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;

/**
 * Compiles many small Java files in one JVM.
 *
 * Starting javac once per file costs most of a second each; the mutation
 * corpus has thousands of files. This reads "source<TAB>outputDir" lines from
 * stdin, compiles each file on its own (so one broken mutant cannot fail the
 * others) and prints "OK <source>" or "ERR <source> <first error line>".
 */
public final class BatchCompile {
    private BatchCompile() {}

    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        StandardJavaFileManager files = compiler.getStandardFileManager(null, null, StandardCharsets.UTF_8);
        BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
        String line;
        while ((line = input.readLine()) != null) {
            if (line.isBlank()) continue;
            String[] parts = line.split("\t");
            File source = new File(parts[0]);
            File out = new File(parts[1]);
            out.mkdirs();
            Iterable<? extends JavaFileObject> units = files.getJavaFileObjectsFromFiles(List.of(source));
            StringWriter errors = new StringWriter();
            List<String> options = Arrays.asList("-d", out.getPath(), "-nowarn", "-Xlint:none", "-proc:none");
            boolean ok = compiler.getTask(errors, files, null, options, null, units).call();
            if (ok) {
                System.out.println("OK\t" + parts[0]);
            } else {
                String first = errors.toString().split("\\R", 2)[0];
                System.out.println("ERR\t" + parts[0] + "\t" + first);
            }
            System.out.flush();
        }
    }
}
