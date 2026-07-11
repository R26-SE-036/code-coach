public class GenArrayIndexFix058 {
    static int largest1(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
            }
        }
        return best;
    }

    static int lastOf(int[] totals) {
        return totals[totals.length - 1];
    }

    static int largest2(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static boolean isEven3(int stock) {
        return stock % 2 == 0;
    }
}
