import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.lang.reflect.Array;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Random;

/**
 * Differential test harness for the mutation corpus.
 *
 * Runs every static method of one class on the same seeded random inputs and
 * prints a transcript: the return value, the exception, what the method
 * printed, and the arguments afterwards (so an in-place change shows). Two
 * versions of a class - the correct original and a mutant - get identical
 * inputs because the seed comes from the method's name and the input number,
 * so comparing their transcripts says whether the mutation changed behaviour.
 *
 * A call that runs past the time limit ends the transcript with TIMEOUT and
 * halts the JVM: an infinite loop is a behaviour too, and it cannot be
 * stopped from inside.
 *
 * Usage: java -cp <harness>;<classes> Fuzz <ClassName> [inputsPerMethod]
 */
public final class Fuzz {
    private static final long CALL_TIMEOUT_MS = 400;
    private static final int OUTPUT_LIMIT = 400;
    private static final String[] WORDS = {
        "", "a", "ab", "abc", "Java", "hello", "level", "racecar", "Code", "coach",
        "x", "AAA", "banana", "apple", "zoo", "Mango", "test", "noon", "Hi there", "42",
    };

    private static final List<Integer> CONSTANTS = new ArrayList<>();

    private Fuzz() {}

    public static void main(String[] args) throws Exception {
        Class<?> target = Class.forName(args[0]);
        int perMethod = args.length > 1 ? Integer.parseInt(args[1]) : 40;
        // The program's own number literals ("50,75,90"): a threshold test
        // like `score >= 90` is only exercised by inputs near 90.
        if (args.length > 2 && !args[2].isBlank()) {
            for (String literal : args[2].split(",")) {
                try {
                    CONSTANTS.add(Integer.parseInt(literal.trim()));
                } catch (NumberFormatException ignored) {
                    // not an int literal - skip it
                }
            }
        }
        PrintStream real = System.out;

        Method[] methods = target.getDeclaredMethods();
        Arrays.sort(methods, Comparator.comparing(Fuzz::signature));
        for (Method method : methods) {
            if (!Modifier.isStatic(method.getModifiers()) || method.isSynthetic()) continue;
            if (method.getName().equals("main")) continue;
            method.setAccessible(true);
            if (!supported(method)) {
                real.println("SKIP " + signature(method));
                continue;
            }
            for (int k = 0; k < perMethod; k++) {
                Random random = new Random(seed(method.getName(), k));
                Object[] callArgs = new Object[method.getParameterCount()];
                Type[] generic = method.getGenericParameterTypes();
                Class<?>[] types = method.getParameterTypes();
                Pool pool = new Pool();
                // Collections first, then the scalars - so a target, a char
                // or an index can be taken from the data it will be used on.
                for (int pass = 0; pass < 2; pass++) {
                    for (int p = 0; p < callArgs.length; p++) {
                        boolean scalar = !(types[p].isArray() || types[p] == String.class || List.class.isAssignableFrom(types[p]));
                        if ((pass == 0) == scalar) continue;
                        callArgs[p] = value(types[p], generic[p], random, k, pool);
                        pool.absorb(callArgs[p]);
                    }
                }
                real.println(signature(method) + "#" + k + " in=" + render(callArgs));
                real.println("  " + call(method, callArgs, real));
            }
        }
        real.flush();
    }

    private static long seed(String name, int k) {
        return name.hashCode() * 1_000_003L + k;
    }

    private static String signature(Method method) {
        StringBuilder text = new StringBuilder(method.getName()).append('(');
        for (Class<?> type : method.getParameterTypes()) text.append(type.getSimpleName()).append(',');
        return text.append(')').toString();
    }

    private static String call(Method method, Object[] callArgs, PrintStream real) {
        ByteArrayOutputStream printed = new ByteArrayOutputStream();
        final Object[] outcome = new Object[2];
        Thread worker = new Thread(() -> {
            System.setOut(new PrintStream(printed, true));
            try {
                outcome[0] = method.invoke(null, callArgs);
            } catch (InvocationTargetException failure) {
                outcome[1] = failure.getCause() == null ? failure : failure.getCause();
            } catch (Throwable failure) {
                outcome[1] = failure;
            }
        });
        worker.setDaemon(true);
        worker.start();
        try {
            worker.join(CALL_TIMEOUT_MS);
        } catch (InterruptedException ignored) {
            Thread.currentThread().interrupt();
        }
        System.setOut(real);
        if (worker.isAlive()) {
            real.println("  TIMEOUT");
            real.flush();
            Runtime.getRuntime().halt(0);
        }
        String out = printed.toString().replace("\r\n", "\n");
        if (out.length() > OUTPUT_LIMIT) out = out.substring(0, OUTPUT_LIMIT) + "...";
        String result = outcome[1] != null
            ? "THROWS " + outcome[1].getClass().getSimpleName()
            : "RETURNS " + render(outcome[0]);
        return result + " | OUT " + out.replace("\n", "\\n") + " | ARGS " + render(callArgs);
    }

    // ------------------------------------------------------------- inputs

    private static boolean supported(Method method) {
        for (Class<?> type : method.getParameterTypes()) {
            if (!supported(type)) return false;
        }
        return true;
    }

    private static boolean supported(Class<?> type) {
        if (type.isArray()) return supported(type.getComponentType());
        return type == int.class || type == long.class || type == double.class
            || type == boolean.class || type == char.class || type == String.class
            || type == Integer.class || type == Double.class || type == List.class
            || type == ArrayList.class;
    }

    /** Values already chosen for this call, for the scalars to borrow from. */
    private static final class Pool {
        final List<Integer> ints = new ArrayList<>();
        final List<Character> chars = new ArrayList<>();
        final List<String> strings = new ArrayList<>();
        int longest = 0;

        void absorb(Object value) {
            if (value == null) return;
            if (value instanceof Integer) {
                ints.add((Integer) value);
            } else if (value instanceof String) {
                String text = (String) value;
                strings.add(text);
                longest = Math.max(longest, text.length());
                for (char c : text.toCharArray()) chars.add(c);
            } else if (value instanceof List) {
                List<?> list = (List<?>) value;
                longest = Math.max(longest, list.size());
                for (Object item : list) absorb(item);
            } else if (value.getClass().isArray()) {
                int size = Array.getLength(value);
                longest = Math.max(longest, size);
                for (int i = 0; i < size; i++) {
                    Object item = Array.get(value, i);
                    if (item instanceof Double) ints.add((int) Math.round((Double) item));
                    else if (item instanceof Character) chars.add((Character) item);
                    else absorb(item);
                }
            }
        }
    }

    private static Object value(Class<?> type, Type generic, Random random, int k, Pool pool) {
        boolean reference = !type.isPrimitive();
        // Mostly real values, sometimes null: a guard like `s != null && ...`
        // only matters when null actually arrives.
        if (reference && k > 2 && random.nextInt(100) < 7) return null;
        if (type == int.class || type == Integer.class) return scalarInt(random, pool);
        if (type == long.class) return (long) scalarInt(random, pool);
        if (type == double.class || type == Double.class) {
            int whole = scalarInt(random, pool);
            return random.nextInt(4) == 0 ? whole + 0.5 : (double) whole;
        }
        if (type == boolean.class) return random.nextBoolean();
        if (type == char.class) {
            if (!pool.chars.isEmpty() && random.nextInt(2) == 0) return pool.chars.get(random.nextInt(pool.chars.size()));
            return "aeiouxyzAB019 ".charAt(random.nextInt(14));
        }
        if (type == String.class) {
            if (!pool.strings.isEmpty() && random.nextInt(5) < 2) return pool.strings.get(random.nextInt(pool.strings.size()));
            return text(random);
        }
        int shape = random.nextInt(7);
        if (type == List.class || type == ArrayList.class) {
            boolean strings = generic instanceof ParameterizedType
                && ((ParameterizedType) generic).getActualTypeArguments()[0] == String.class;
            int size = length(random, k);
            int[] numbers = sequence(size, shape, random);
            List<Object> list = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                // A null inside the collection, not only a null collection:
                // `word != null & word.length() > 0` over a list only fails there.
                if (strings && k > 2 && random.nextInt(100) < 10) list.add(null);
                else list.add(strings ? text(random) : (Object) numbers[i]);
            }
            return list;
        }
        if (type.isArray()) {
            Class<?> component = type.getComponentType();
            if (component.isArray()) {
                int rows = Math.min(length(random, k), 4);
                int columns = 1 + random.nextInt(4);
                Object grid = Array.newInstance(component, rows);
                for (int r = 0; r < rows; r++) {
                    int width = random.nextInt(5) == 0 ? 1 + random.nextInt(4) : columns;
                    Array.set(grid, r, fill(component.getComponentType(), sequence(width, shape, random), random));
                }
                return grid;
            }
            int size = length(random, k);
            if (component == String.class) {
                String[] words = new String[size];
                for (int i = 0; i < size; i++) words[i] = k > 2 && random.nextInt(100) < 10 ? null : text(random);
                return words;
            }
            if (component == char.class) {
                char[] letters = new char[size];
                for (int i = 0; i < size; i++) letters[i] = "aabbc A1".charAt(random.nextInt(8));
                return letters;
            }
            return fill(component, sequence(size, shape, random), random);
        }
        return null;
    }

    private static Object fill(Class<?> component, int[] numbers, Random random) {
        Object array = Array.newInstance(component, numbers.length);
        for (int i = 0; i < numbers.length; i++) {
            if (component == int.class || component == Integer.class) {
                Array.set(array, i, numbers[i]);
            } else if (component == long.class) {
                Array.set(array, i, (long) numbers[i]);
            } else if (component == double.class || component == Double.class) {
                Array.set(array, i, random.nextInt(4) == 0 ? numbers[i] + 0.5 : (double) numbers[i]);
            } else if (component == char.class) {
                Array.set(array, i, (char) ('a' + Math.floorMod(numbers[i], 5)));
            } else if (component == boolean.class) {
                Array.set(array, i, numbers[i] % 2 == 0);
            } else if (component == String.class) {
                Array.set(array, i, WORDS[Math.floorMod(numbers[i], WORDS.length)]);
            }
        }
        return array;
    }

    // Arrays come in the shapes bugs hide behind - duplicates, all equal,
    // already sorted either way, all negative - not only random spreads.
    private static int[] sequence(int size, int shape, Random random) {
        int[] values = new int[size];
        int same = random.nextInt(30) - 5;
        for (int i = 0; i < size; i++) {
            if (shape == 2) values[i] = random.nextInt(4);
            else if (shape == 3) values[i] = same;
            else if (shape == 6) values[i] = -1 - random.nextInt(20);
            else values[i] = random.nextInt(50) - 10;
        }
        if (shape == 4 || shape == 5) Arrays.sort(values);
        if (shape == 5) {
            for (int i = 0; i < size / 2; i++) {
                int swap = values[i];
                values[i] = values[size - 1 - i];
                values[size - 1 - i] = swap;
            }
        }
        return values;
    }

    // The first few inputs are the edge cases every off-by-one hides behind:
    // nothing, one element, two elements.
    private static int length(Random random, int k) {
        if (k == 0) return 0;
        if (k == 1) return 1;
        if (k == 2) return 2;
        return random.nextInt(8);
    }

    private static int scalarInt(Random random, Pool pool) {
        int roll = random.nextInt(20);
        // Either side of one of the program's own constants.
        if (!CONSTANTS.isEmpty() && random.nextInt(4) == 0) {
            return CONSTANTS.get(random.nextInt(CONSTANTS.size())) + random.nextInt(3) - 1;
        }
        // A value that is in the data, or a position in it.
        if (!pool.ints.isEmpty() && roll < 7) return pool.ints.get(random.nextInt(pool.ints.size()));
        if (pool.longest > 0 && roll < 10) return random.nextInt(pool.longest + 1);
        if (roll == 10) return 0;
        if (roll == 11) return -1 - random.nextInt(10);
        if (roll == 12) return 1;
        return random.nextInt(40) - 5;
    }

    private static String text(Random random) {
        int kind = random.nextInt(6);
        StringBuilder out = new StringBuilder();
        if (kind == 0) {
            char c = "abA ".charAt(random.nextInt(4));
            for (int i = random.nextInt(6); i > 0; i--) out.append(c);
            return out.toString();
        }
        if (kind == 1) {
            for (int i = random.nextInt(8); i > 0; i--) out.append("ab b".charAt(random.nextInt(4)));
            return out.toString();
        }
        if (kind == 2) {
            for (int i = random.nextInt(4); i > 0; i--) out.append("abc".charAt(random.nextInt(3)));
            String left = out.toString();
            return left + (random.nextBoolean() ? "x" : "") + new StringBuilder(left).reverse();
        }
        return WORDS[random.nextInt(WORDS.length)];
    }

    // ------------------------------------------------------------- output

    private static String render(Object value) {
        if (value == null) return "null";
        if (value instanceof Object[]) return Arrays.deepToString((Object[]) value);
        if (value.getClass().isArray()) {
            StringBuilder text = new StringBuilder("[");
            for (int i = 0; i < Array.getLength(value); i++) {
                if (i > 0) text.append(", ");
                text.append(render(Array.get(value, i)));
            }
            return text.append(']').toString();
        }
        if (value instanceof Double) {
            double number = (Double) value;
            if (Double.isNaN(number) || Double.isInfinite(number)) return String.valueOf(number);
            return String.format("%.6f", number);
        }
        return String.valueOf(value);
    }
}
