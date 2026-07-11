public class GenArrayIndexBug070 {
    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static void showLast(int[] totals) {
        System.out.println(totals[totals.length]);
    }

    static int sum2(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int largest4(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }
}
