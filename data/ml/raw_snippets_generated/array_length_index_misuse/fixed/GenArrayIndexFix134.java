public class GenArrayIndexFix134 {
    static boolean isEven1(int total) {
        return total % 2 == 0;
    }

    static void printAll2(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void stampLast(int[] totals, int value) {
        totals[totals.length - 1] = value;
    }
}
