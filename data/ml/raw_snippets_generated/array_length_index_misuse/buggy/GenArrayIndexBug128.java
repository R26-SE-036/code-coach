public class GenArrayIndexBug128 {
    static int drain1(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static int largest2(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int largest4(int[] ratings) {
        int best = ratings[0];
        for (int i = 1; i < ratings.length; i++) {
            if (ratings[i] > best) {
                best = ratings[i];
            }
        }
        return best;
    }

    static void stampLast(int[] stocks, int value) {
        stocks[stocks.length] = value;
    }
}
