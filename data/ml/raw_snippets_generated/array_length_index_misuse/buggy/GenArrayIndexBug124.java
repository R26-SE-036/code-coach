public class GenArrayIndexBug124 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static void stampLast(int[] stocks, int value) {
        stocks[stocks.length] = value;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printAll3(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }

    static boolean isEven4(int points) {
        return points % 2 == 0;
    }
}
