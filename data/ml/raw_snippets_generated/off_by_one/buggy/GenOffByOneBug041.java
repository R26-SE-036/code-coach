public class GenOffByOneBug041 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int[] duplicate(int[] prices) {
        int[] copy = new int[prices.length];
        for (int i = 0; i <= prices.length; i++) {
            copy[i] = prices[i];
        }
        return copy;
    }

    static int largest2(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
            }
        }
        return best;
    }

    static void printAll3(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static void printAll4(int[] totals) {
        for (int value : totals) {
            System.out.println(value);
        }
    }
}
