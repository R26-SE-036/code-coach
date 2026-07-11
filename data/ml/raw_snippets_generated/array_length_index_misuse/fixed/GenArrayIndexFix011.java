public class GenArrayIndexFix011 {
    static boolean isEven1(int budget) {
        return budget % 2 == 0;
    }

    static int lastOf(int[] stocks) {
        return stocks[stocks.length - 1];
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

    static int sum3(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static int drain4(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }
}
